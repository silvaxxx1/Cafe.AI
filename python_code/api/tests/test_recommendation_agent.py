"""
Tests for RecommendationAgent.

The core recommendation logic (get_apriori_recommendation,
get_popular_recommendation) has zero LLM dependency — tested purely (sync).

LLM-dependent paths (get_response, recommendation_classification) are
tested by mocking get_chatbot_response with AsyncMock.
"""
import json
import pytest
from unittest.mock import patch, AsyncMock

from agents.recommendation_agent import RecommendationAgent

APRIORI_PATH = "recommendation_objects/apriori_recommendations.json"
POPULAR_PATH = "recommendation_objects/popularity_recommendation.csv"


def make_agent():
    with patch("agents.recommendation_agent.AsyncOpenAI"):
        return RecommendationAgent(APRIORI_PATH, POPULAR_PATH)


# ---------------------------------------------------------------------------
# Pure logic — sync, no LLM
# ---------------------------------------------------------------------------

class TestGetAprioriRecommendation:
    def test_known_product_returns_recommendations(self):
        agent = make_agent()
        recs = agent.get_apriori_recommendation(["Cappuccino"])
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_unknown_product_returns_empty_list(self):
        agent = make_agent()
        recs = agent.get_apriori_recommendation(["NonExistentItem99"])
        assert recs == []

    def test_empty_input_returns_empty_list(self):
        agent = make_agent()
        recs = agent.get_apriori_recommendation([])
        assert recs == []

    def test_top_k_limits_results(self):
        agent = make_agent()
        recs = agent.get_apriori_recommendation(["Cappuccino"], top_k=2)
        assert len(recs) <= 2

    def test_default_top_k_returns_at_most_5(self):
        agent = make_agent()
        recs = agent.get_apriori_recommendation(["Cappuccino"])
        assert len(recs) <= 5

    def test_max_2_recs_per_category(self):
        agent = make_agent()
        products = list(agent.apriori_recommendations.keys())[:3]
        recs = agent.get_apriori_recommendation(products, top_k=20)

        product_to_category = dict(zip(agent.products, agent.product_categories))
        category_counts: dict = {}
        for rec in recs:
            cat = product_to_category.get(rec, "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        for cat, count in category_counts.items():
            assert count <= 2, f"Category '{cat}' appeared {count} times (max 2)"

    def test_no_duplicate_products_in_result(self):
        agent = make_agent()
        products = list(agent.apriori_recommendations.keys())[:3]
        recs = agent.get_apriori_recommendation(products)
        assert len(recs) == len(set(recs))


class TestGetPopularRecommendation:
    def test_no_filter_returns_top_products(self):
        agent = make_agent()
        recs = agent.get_popular_recommendation()
        assert isinstance(recs, list)
        assert len(recs) > 0

    def test_default_top_k_is_5(self):
        agent = make_agent()
        recs = agent.get_popular_recommendation()
        assert len(recs) <= 5

    def test_custom_top_k(self):
        agent = make_agent()
        recs = agent.get_popular_recommendation(top_k=3)
        assert len(recs) <= 3

    def test_category_filter_string(self):
        agent = make_agent()
        recs = agent.get_popular_recommendation(product_categories="Coffee")
        assert isinstance(recs, list)

    def test_category_filter_list(self):
        agent = make_agent()
        recs = agent.get_popular_recommendation(product_categories=["Coffee", "Bakery"])
        assert isinstance(recs, list)

    def test_unknown_category_returns_empty_list(self):
        agent = make_agent()
        recs = agent.get_popular_recommendation(product_categories="NonExistentCategory")
        assert recs == []


# ---------------------------------------------------------------------------
# LLM-dependent — async, mock get_chatbot_response
# ---------------------------------------------------------------------------

class TestRecommendationClassification:
    async def test_apriori_classification(self):
        agent = make_agent()
        llm_output = json.dumps({
            "chain of thought": "User ordered Cappuccino",
            "recommendation_type": "apriori",
            "parameters": ["Cappuccino"]
        })
        with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.recommendation_classification([{"role": "user", "content": "What goes well with my cappuccino?"}])

        assert result["recommendation_type"] == "apriori"
        assert "Cappuccino" in result["parameters"]

    async def test_popular_classification(self):
        agent = make_agent()
        llm_output = json.dumps({"recommendation_type": "popular", "parameters": []})
        with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.recommendation_classification([{"role": "user", "content": "What's popular?"}])

        assert result["recommendation_type"] == "popular"

    async def test_popular_by_category_classification(self):
        agent = make_agent()
        llm_output = json.dumps({"recommendation_type": "popular by category", "parameters": ["Coffee"]})
        with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.recommendation_classification([{"role": "user", "content": "What coffee do you recommend?"}])

        assert result["recommendation_type"] == "popular by category"

    async def test_malformed_json_falls_back_to_popular(self):
        agent = make_agent()
        with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(return_value="not json")):
            result = await agent.recommendation_classification([{"role": "user", "content": "Recommend something"}])

        assert result["recommendation_type"] == "popular"
        assert result["parameters"] == []


class TestGetResponse:
    async def test_empty_recommendations_returns_fallback_message(self):
        """When no recs are found the agent returns a safe fallback without crashing."""
        agent = make_agent()
        classification_output = json.dumps({
            "recommendation_type": "apriori",
            "parameters": ["NonExistentItem99"]
        })
        with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(return_value=classification_output)):
            result = await agent.get_response([{"role": "user", "content": "What pairs with NonExistentItem99?"}])

        assert "content" in result
        assert result["content"] != ""

    async def test_successful_response_shape(self):
        agent = make_agent()
        # First call → classification (popular), second call → final response text
        responses = iter([
            json.dumps({"recommendation_type": "popular", "parameters": []}),
            "I recommend the Cappuccino and Latte!"
        ])
        with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(side_effect=responses)):
            result = await agent.get_response([{"role": "user", "content": "What do you recommend?"}])

        assert result["role"] == "assistant"
        assert result["memory"]["agent"] == "recommendation_agent"
