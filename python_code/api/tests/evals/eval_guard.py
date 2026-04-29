"""
Eval runner for GuardAgent.

Hits the real LLM — requires a valid .env in python_code/api/.
Run from the api/ directory:
    python -m tests.evals.eval_guard

Exit 0 if pass rate >= PASS_THRESHOLD, exit 1 otherwise.
"""
import json
import asyncio
import sys
from pathlib import Path

from agents.guard_agent import GuardAgent

EVAL_DATA = Path(__file__).parent.parent / "eval_data" / "guard_evals.json"
PASS_THRESHOLD = 0.80


async def run(cases: list[dict]) -> tuple[int, int]:
    agent = GuardAgent()
    passed = 0

    for case in cases:
        messages = [{"role": "user", "content": case["input"]}]
        result = await agent.get_response(messages)
        actual = result["memory"]["guard_decision"]
        ok = actual == case["expected"]
        passed += ok
        status = "PASS" if ok else "FAIL"
        print(f"  {status}  [{case['expected']:11}] '{case['input']}'  →  {actual}")
        await asyncio.sleep(0.5)

    return passed, len(cases)


def main():
    with open(EVAL_DATA) as f:
        cases = json.load(f)

    print(f"\nGuardAgent eval — {len(cases)} cases\n")
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
