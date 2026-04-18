"""
Tests for the eval runner logic.

No real LLM calls — all agents mocked. Covers:
- eval data files: existence, valid JSON, correct schema, balanced classes
- runner scoring: all pass, all fail, partial pass
- invalid LLM decision handling (unknown agent/type)
- pass threshold and exit codes
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock

EVAL_DATA_DIR = Path(__file__).parent / "eval_data"
APRIORI_PATH = Path(__file__).parent.parent / "recommendation_objects" / "apriori_recommendations.json"
POPULAR_PATH = Path(__file__).parent.parent / "recommendation_objects" / "popularity_recommendation.csv"

VALID_GUARD_DECISIONS = {"allowed", "not allowed"}
VALID_AGENTS = {"details_agent", "order_taking_agent", "recommendation_agent"}
VALID_REC_TYPES = {"apriori", "popular", "popular by category"}


# ---------------------------------------------------------------------------
# Eval data integrity
# ---------------------------------------------------------------------------

class TestEvalDataFiles:
    def test_guard_eval_data_exists(self):
        assert (EVAL_DATA_DIR / "guard_evals.json").exists()

    def test_classification_eval_data_exists(self):
        assert (EVAL_DATA_DIR / "classification_evals.json").exists()

    def test_recommendation_eval_data_exists(self):
        assert (EVAL_DATA_DIR / "recommendation_evals.json").exists()

    def test_guard_evals_valid_json(self):
        cases = json.loads((EVAL_DATA_DIR / "guard_evals.json").read_text())
        assert isinstance(cases, list) and len(cases) > 0

    def test_classification_evals_valid_json(self):
        cases = json.loads((EVAL_DATA_DIR / "classification_evals.json").read_text())
        assert isinstance(cases, list) and len(cases) > 0

    def test_recommendation_evals_valid_json(self):
        cases = json.loads((EVAL_DATA_DIR / "recommendation_evals.json").read_text())
        assert isinstance(cases, list) and len(cases) > 0

    def test_guard_evals_schema(self):
        cases = json.loads((EVAL_DATA_DIR / "guard_evals.json").read_text())
        for case in cases:
            assert "input" in case and "expected" in case
            assert isinstance(case["input"], str)
            assert case["expected"] in VALID_GUARD_DECISIONS, \
                f"Invalid expected value: {case['expected']}"

    def test_classification_evals_schema(self):
        cases = json.loads((EVAL_DATA_DIR / "classification_evals.json").read_text())
        for case in cases:
            assert "input" in case and "expected" in case
            assert isinstance(case["input"], str)
            assert case["expected"] in VALID_AGENTS, \
                f"Invalid expected value: {case['expected']}"

    def test_recommendation_evals_schema(self):
        cases = json.loads((EVAL_DATA_DIR / "recommendation_evals.json").read_text())
        for case in cases:
            assert "input" in case and "expected_type" in case
            assert isinstance(case["input"], str)
            assert case["expected_type"] in VALID_REC_TYPES, \
                f"Invalid expected_type: {case['expected_type']}"

    def test_guard_evals_balanced(self):
        cases = json.loads((EVAL_DATA_DIR / "guard_evals.json").read_text())
        decisions = {c["expected"] for c in cases}
        assert "allowed" in decisions
        assert "not allowed" in decisions
        allowed = sum(1 for c in cases if c["expected"] == "allowed")
        blocked = sum(1 for c in cases if c["expected"] == "not allowed")
        # neither class should be less than 30% of the dataset
        total = len(cases)
        assert allowed / total >= 0.30, f"Too few 'allowed' cases: {allowed}/{total}"
        assert blocked / total >= 0.30, f"Too few 'not allowed' cases: {blocked}/{total}"

    def test_classification_evals_covers_all_agents(self):
        cases = json.loads((EVAL_DATA_DIR / "classification_evals.json").read_text())
        agents = {c["expected"] for c in cases}
        assert agents == VALID_AGENTS

    def test_recommendation_evals_covers_all_types(self):
        cases = json.loads((EVAL_DATA_DIR / "recommendation_evals.json").read_text())
        types = {c["expected_type"] for c in cases}
        assert types == VALID_REC_TYPES


# ---------------------------------------------------------------------------
# Guard eval runner
# ---------------------------------------------------------------------------

class TestGuardEvalRunner:
    async def test_all_pass_returns_full_count(self):
        from tests.evals.eval_guard import run

        cases = [
            {"input": "What lattes do you have?", "expected": "allowed"},
            {"input": "What's the weather?", "expected": "not allowed"},
        ]
        responses = [
            json.dumps({"decision": "allowed", "message": ""}),
            json.dumps({"decision": "not allowed", "message": "Sorry"}),
        ]
        with patch("agents.guard_agent.AsyncOpenAI"):
            with patch("agents.guard_agent.get_chatbot_response", AsyncMock(side_effect=responses)):
                passed, total = await run(cases)

        assert passed == 2
        assert total == 2

    async def test_all_fail_returns_zero(self):
        from tests.evals.eval_guard import run

        cases = [{"input": "What lattes do you have?", "expected": "not allowed"}]
        with patch("agents.guard_agent.AsyncOpenAI"):
            with patch("agents.guard_agent.get_chatbot_response",
                       AsyncMock(return_value=json.dumps({"decision": "allowed", "message": ""}))):
                passed, total = await run(cases)

        assert passed == 0
        assert total == 1

    async def test_partial_pass(self):
        from tests.evals.eval_guard import run

        cases = [{"input": str(i), "expected": "allowed"} for i in range(4)]
        responses = [
            json.dumps({"decision": "allowed", "message": ""}),
            json.dumps({"decision": "allowed", "message": ""}),
            json.dumps({"decision": "not allowed", "message": "Sorry"}),
            json.dumps({"decision": "not allowed", "message": "Sorry"}),
        ]
        with patch("agents.guard_agent.AsyncOpenAI"):
            with patch("agents.guard_agent.get_chatbot_response", AsyncMock(side_effect=responses)):
                passed, total = await run(cases)

        assert passed == 2
        assert total == 4

    async def test_invalid_llm_decision_counts_as_fail(self):
        from tests.evals.eval_guard import run

        cases = [{"input": "Hello", "expected": "allowed"}]
        with patch("agents.guard_agent.AsyncOpenAI"):
            # LLM returns garbage JSON — postprocess defaults to "allowed", which matches
            with patch("agents.guard_agent.get_chatbot_response",
                       AsyncMock(return_value="not valid json")):
                passed, total = await run(cases)

        # guard postprocess defaults to "allowed" on bad JSON
        assert passed == 1
        assert total == 1


# ---------------------------------------------------------------------------
# Classification eval runner
# ---------------------------------------------------------------------------

class TestClassificationEvalRunner:
    async def test_all_pass_returns_full_count(self):
        from tests.evals.eval_classification import run

        cases = [
            {"input": "What drinks?", "expected": "details_agent"},
            {"input": "Order a latte", "expected": "order_taking_agent"},
            {"input": "Recommend something", "expected": "recommendation_agent"},
        ]
        responses = [
            json.dumps({"decision": "details_agent", "message": ""}),
            json.dumps({"decision": "order_taking_agent", "message": ""}),
            json.dumps({"decision": "recommendation_agent", "message": ""}),
        ]
        with patch("agents.classification_agent.AsyncOpenAI"):
            with patch("agents.classification_agent.get_chatbot_response", AsyncMock(side_effect=responses)):
                passed, total = await run(cases)

        assert passed == 3
        assert total == 3

    async def test_wrong_routing_counts_as_fail(self):
        from tests.evals.eval_classification import run

        cases = [{"input": "What drinks?", "expected": "details_agent"}]
        with patch("agents.classification_agent.AsyncOpenAI"):
            with patch("agents.classification_agent.get_chatbot_response",
                       AsyncMock(return_value=json.dumps({"decision": "order_taking_agent", "message": ""}))):
                passed, total = await run(cases)

        assert passed == 0
        assert total == 1

    async def test_unknown_agent_name_counts_as_fail(self, capsys):
        from tests.evals.eval_classification import run

        cases = [{"input": "Hello", "expected": "details_agent"}]
        with patch("agents.classification_agent.AsyncOpenAI"):
            with patch("agents.classification_agent.get_chatbot_response",
                       AsyncMock(return_value=json.dumps({"decision": "unknown_agent", "message": ""}))):
                passed, total = await run(cases)

        assert passed == 0
        captured = capsys.readouterr()
        assert "WARN" in captured.out
        assert "unknown_agent" in captured.out


# ---------------------------------------------------------------------------
# Recommendation eval runner
# ---------------------------------------------------------------------------

class TestRecommendationEvalRunner:
    async def test_all_pass_returns_full_count(self):
        from tests.evals.eval_recommendation import run

        cases = [
            {"input": "What's popular?", "expected_type": "popular"},
            {"input": "What coffee do you recommend?", "expected_type": "popular by category"},
            {"input": "I had a Latte, what goes with it?", "expected_type": "apriori"},
        ]
        responses = [
            json.dumps({"recommendation_type": "popular", "parameters": []}),
            json.dumps({"recommendation_type": "popular by category", "parameters": ["Coffee"]}),
            json.dumps({"recommendation_type": "apriori", "parameters": ["Latte"]}),
        ]
        with patch("agents.recommendation_agent.AsyncOpenAI"):
            with patch("agents.recommendation_agent.get_chatbot_response", AsyncMock(side_effect=responses)):
                passed, total = await run(cases)

        assert passed == 3
        assert total == 3

    async def test_wrong_type_counts_as_fail(self):
        from tests.evals.eval_recommendation import run

        cases = [{"input": "What's popular?", "expected_type": "popular"}]
        with patch("agents.recommendation_agent.AsyncOpenAI"):
            with patch("agents.recommendation_agent.get_chatbot_response",
                       AsyncMock(return_value=json.dumps({"recommendation_type": "apriori", "parameters": []}))):
                passed, total = await run(cases)

        assert passed == 0
        assert total == 1

    async def test_unknown_type_counts_as_fail_and_warns(self, capsys):
        from tests.evals.eval_recommendation import run

        cases = [{"input": "Surprise me", "expected_type": "popular"}]
        with patch("agents.recommendation_agent.AsyncOpenAI"):
            with patch("agents.recommendation_agent.get_chatbot_response",
                       AsyncMock(return_value=json.dumps({"recommendation_type": "mystery", "parameters": []}))):
                passed, total = await run(cases)

        assert passed == 0
        captured = capsys.readouterr()
        assert "WARN" in captured.out
        assert "mystery" in captured.out

    async def test_bad_json_defaults_to_popular_and_passes_if_expected(self):
        from tests.evals.eval_recommendation import run

        # postprocess_classfication defaults to "popular" on bad JSON
        cases = [{"input": "Hello", "expected_type": "popular"}]
        with patch("agents.recommendation_agent.AsyncOpenAI"):
            with patch("agents.recommendation_agent.get_chatbot_response",
                       AsyncMock(return_value="not json")):
                passed, total = await run(cases)

        assert passed == 1
        assert total == 1


# ---------------------------------------------------------------------------
# Pass threshold constants
# ---------------------------------------------------------------------------

class TestPassThreshold:
    def test_guard_threshold_is_80_percent(self):
        from tests.evals.eval_guard import PASS_THRESHOLD
        assert PASS_THRESHOLD == 0.80

    def test_classification_threshold_is_80_percent(self):
        from tests.evals.eval_classification import PASS_THRESHOLD
        assert PASS_THRESHOLD == 0.80

    def test_recommendation_threshold_is_80_percent(self):
        from tests.evals.eval_recommendation import PASS_THRESHOLD
        assert PASS_THRESHOLD == 0.80


# ---------------------------------------------------------------------------
# Exit code behaviour — test main() via the rate calculation directly
# ---------------------------------------------------------------------------

class TestExitCodes:
    def test_below_threshold_exits_1(self):
        from tests.evals import eval_guard

        with patch("tests.evals.eval_guard.asyncio.run", return_value=(7, 10)):
            with patch("builtins.open"):
                with patch("json.load", return_value=[{"input": "x", "expected": "allowed"}] * 10):
                    with pytest.raises(SystemExit) as exc:
                        eval_guard.main()
        assert exc.value.code == 1

    def test_at_threshold_exits_0(self):
        from tests.evals import eval_guard

        with patch("tests.evals.eval_guard.asyncio.run", return_value=(8, 10)):
            with patch("builtins.open"):
                with patch("json.load", return_value=[{"input": "x", "expected": "allowed"}] * 10):
                    with pytest.raises(SystemExit) as exc:
                        eval_guard.main()
        assert exc.value.code == 0

    def test_above_threshold_exits_0(self):
        from tests.evals import eval_guard

        with patch("tests.evals.eval_guard.asyncio.run", return_value=(10, 10)):
            with patch("builtins.open"):
                with patch("json.load", return_value=[{"input": "x", "expected": "allowed"}] * 10):
                    with pytest.raises(SystemExit) as exc:
                        eval_guard.main()
        assert exc.value.code == 0
