"""
Eval runner for RecommendationAgent — specifically the recommendation_classification step.

Tests that the agent picks the right recommendation strategy (apriori / popular /
popular by category) given a user message. Does not test the final LLM-written
prose — only the routing decision, which is what can silently regress.

Hits the real LLM — requires a valid .env in python_code/api/.
Run from the api/ directory:
    python -m tests.evals.eval_recommendation

Exit 0 if pass rate >= PASS_THRESHOLD, exit 1 otherwise.
"""
import json
import asyncio
import sys
from pathlib import Path

from agents.recommendation_agent import RecommendationAgent

EVAL_DATA = Path(__file__).parent.parent / "eval_data" / "recommendation_evals.json"
APRIORI_PATH = Path(__file__).parent.parent.parent / "recommendation_objects" / "apriori_recommendations.json"
POPULAR_PATH = Path(__file__).parent.parent.parent / "recommendation_objects" / "popularity_recommendation.csv"
PASS_THRESHOLD = 0.80

VALID_TYPES = {"apriori", "popular", "popular by category"}


async def run(cases: list[dict]) -> tuple[int, int]:
    agent = RecommendationAgent(
        apriori_recommendation_path=str(APRIORI_PATH),
        popular_recommendation_path=str(POPULAR_PATH),
    )
    passed = 0

    for case in cases:
        messages = [{"role": "user", "content": case["input"]}]
        result = await agent.recommendation_classification(messages)
        actual = result["recommendation_type"]

        if actual not in VALID_TYPES:
            print(f"  WARN  LLM returned unknown type '{actual}' for: '{case['input']}'")

        ok = actual == case["expected_type"]
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  [{case['expected_type']:20}] '{case['input']}'  →  {actual}")

    return passed, len(cases)


def main():
    with open(EVAL_DATA) as f:
        cases = json.load(f)

    print(f"\nRecommendationAgent eval — {len(cases)} cases\n")
    passed, total = asyncio.run(run(cases))
    rate = passed / total
    print(f"\n{'='*50}")
    print(f"Result: {passed}/{total}  ({rate:.0%})")

    if rate < PASS_THRESHOLD:
        print(f"FAIL — below {PASS_THRESHOLD:.0%} threshold")
        sys.exit(1)

    print(f"PASS — at or above {PASS_THRESHOLD:.0%} threshold")
    sys.exit(0)


if __name__ == "__main__":
    main()
