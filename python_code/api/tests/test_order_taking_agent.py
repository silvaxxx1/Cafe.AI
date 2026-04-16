"""
Tests for OrderTakingAgent.

postprocess() is now async (it awaits the recommendation agent).
get_response() is also async. All tests use AsyncMock for async dependencies.
"""
import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from agents.order_taking_agent import OrderTakingAgent
from agents.recommendation_agent import RecommendationAgent

APRIORI_PATH = "recommendation_objects/apriori_recommendations.json"
POPULAR_PATH = "recommendation_objects/popularity_recommendation.csv"


def make_recommendation_agent():
    with patch("agents.recommendation_agent.AsyncOpenAI"):
        return RecommendationAgent(APRIORI_PATH, POPULAR_PATH)


TEST_MENU_TEXT = "\n".join([
    "            Cappuccino - $4.50",
    "            Latte - $4.75",
    "            Croissant - $3.25",
])


def make_order_agent():
    with patch("agents.order_taking_agent.AsyncOpenAI"):
        rec_agent = make_recommendation_agent()
        return OrderTakingAgent(rec_agent, TEST_MENU_TEXT)


MESSAGES = [{"role": "user", "content": "I'd like a latte please"}]

VALID_ORDER_JSON = json.dumps({
    "chain of thought": "User wants a latte",
    "step number": "2",
    "order": [{"item": "Latte", "quanitity": 1, "price": 4.75}],
    "response": "Got it, one Latte at $4.75. Anything else?"
})


class TestPostprocess:
    async def test_valid_order_returns_correct_shape(self):
        agent = make_order_agent()
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock(
            return_value={"role": "assistant", "content": "You might also like..."}
        )
        result = await agent.postprocess(VALID_ORDER_JSON, MESSAGES, asked_recommendation_before=True)

        assert result["role"] == "assistant"
        assert result["memory"]["agent"] == "order_taking_agent"
        assert result["memory"]["step number"] == "2"
        assert isinstance(result["memory"]["order"], list)

    async def test_valid_order_sets_asked_recommendation_before(self):
        agent = make_order_agent()
        result = await agent.postprocess(VALID_ORDER_JSON, MESSAGES, asked_recommendation_before=True)
        assert result["memory"]["asked_recommendation_before"] is True

    async def test_recommendation_triggered_on_first_order(self):
        """When asked_recommendation_before=False and order has items, recommendation is fetched."""
        agent = make_order_agent()
        rec_content = "Try our Croissant!"
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock(
            return_value={"role": "assistant", "content": rec_content}
        )
        result = await agent.postprocess(VALID_ORDER_JSON, MESSAGES, asked_recommendation_before=False)

        agent.recommendation_agent.get_recommendations_from_order.assert_called_once()
        assert result["content"] == rec_content
        assert result["memory"]["asked_recommendation_before"] is True

    async def test_recommendation_not_triggered_when_already_asked(self):
        agent = make_order_agent()
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock()
        await agent.postprocess(VALID_ORDER_JSON, MESSAGES, asked_recommendation_before=True)
        agent.recommendation_agent.get_recommendations_from_order.assert_not_called()

    async def test_recommendation_not_triggered_on_empty_order(self):
        agent = make_order_agent()
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock()
        empty_order_json = json.dumps({
            "step number": "1",
            "order": [],
            "response": "What would you like to order?"
        })
        await agent.postprocess(empty_order_json, MESSAGES, asked_recommendation_before=False)
        agent.recommendation_agent.get_recommendations_from_order.assert_not_called()

    async def test_order_as_string_is_parsed(self):
        """The order field can arrive as a JSON string; postprocess must parse it."""
        agent = make_order_agent()
        order_items = [{"item": "Latte", "quanitity": 1, "price": 4.75}]
        output_with_string_order = json.dumps({
            "step number": "2",
            "order": json.dumps(order_items),
            "response": "One Latte coming up!"
        })
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock(
            return_value={"role": "assistant", "content": "Also try..."}
        )
        result = await agent.postprocess(output_with_string_order, MESSAGES, asked_recommendation_before=True)
        assert isinstance(result["memory"]["order"], list)
        assert result["memory"]["order"][0]["item"] == "Latte"

    async def test_malformed_json_returns_fallback(self):
        agent = make_order_agent()
        result = await agent.postprocess("this is not json", MESSAGES, asked_recommendation_before=False)

        assert result["role"] == "assistant"
        assert "trouble processing" in result["content"].lower() or "repeat" in result["content"].lower()
        assert result["memory"]["agent"] == "order_taking_agent"
        assert result["memory"]["order"] == []
        assert result["memory"]["step number"] == "1"


class TestGetResponse:
    async def test_get_response_returns_valid_shape(self):
        agent = make_order_agent()
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock(
            return_value={"role": "assistant", "content": "Try our Croissant!"}
        )
        with patch("agents.order_taking_agent.get_chatbot_response", AsyncMock(return_value=VALID_ORDER_JSON)):
            result = await agent.get_response(MESSAGES)

        assert result["role"] == "assistant"
        assert result["memory"]["agent"] == "order_taking_agent"

    async def test_get_response_recovers_last_order_from_history(self):
        """Agent should pick up prior order state from message history."""
        agent = make_order_agent()
        prior_order = [{"item": "Cappuccino", "quanitity": 1, "price": 4.50}]
        messages = [
            {
                "role": "assistant",
                "content": "One Cappuccino. Anything else?",
                "memory": {
                    "agent": "order_taking_agent",
                    "step number": "2",
                    "order": prior_order,
                    "asked_recommendation_before": True,
                }
            },
            {"role": "user", "content": "That's all thanks!"}
        ]
        llm_output = json.dumps({
            "step number": "6",
            "order": prior_order,
            "response": "Your total is $4.50. Thank you!"
        })
        agent.recommendation_agent.get_recommendations_from_order = AsyncMock(
            return_value={"role": "assistant", "content": ""}
        )
        with patch("agents.order_taking_agent.get_chatbot_response", AsyncMock(return_value=llm_output)):
            result = await agent.get_response(messages)

        assert result["memory"]["agent"] == "order_taking_agent"
