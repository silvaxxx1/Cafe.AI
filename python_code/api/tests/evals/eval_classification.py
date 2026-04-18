"""
Eval runner for ClassificationAgent.

Hits the real LLM — requires a valid .env in python_code/api/.
Run from the api/ directory:
    python -m tests.evals.eval_classification

Exit 0 if pass rate >= PASS_THRESHOLD, exit 1 otherwise.
"""
import json
import asyncio
import sys
from pathlib import Path

from agents.classification_agent import ClassificationAgent

EVAL_DATA = Path(__file__).parent.parent / "eval_data" / "classification_evals.json"
PASS_THRESHOLD = 0.80

VALID_AGENTS = {"details_agent", "order_taking_agent", "recommendation_agent"}


async def run(cases: list[dict]) -> tuple[int, int]:
    agent = ClassificationAgent()
    passed = 0

    for case in cases:
        messages = [{"role": "user", "content": case["input"]}]
        result = await agent.get_response(messages)
        actual = result["memory"]["classification_decision"]

        if actual not in VALID_AGENTS:
            print(f"  WARN  LLM returned unknown agent '{actual}' for: '{case['input']}'")

        ok = actual == case["expected"]
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  [{case['expected']:22}] '{case['input']}'  →  {actual}")

    return passed, len(cases)


def main():
    with open(EVAL_DATA) as f:
        cases = json.load(f)

    print(f"\nClassificationAgent eval — {len(cases)} cases\n")
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
