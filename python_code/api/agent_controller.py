import json
import time
import structlog
from collections.abc import AsyncGenerator
from agents import (GuardAgent,
                    ClassificationAgent,
                    DetailsAgent,
                    OrderTakingAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )
from agents.utils import reset_token_counter, get_token_counts
from metrics import MetricsStore

log = structlog.get_logger()

class AgentController():
    def __init__(self, metrics: MetricsStore | None = None):
        self.metrics = metrics
        with open("menu.json") as f:
            self.menu = json.load(f)

        menu_text = "\n".join(
            f"            {item['name']} - ${item['price']:.2f}" for item in self.menu
        )

        self.guard_agent = GuardAgent()
        self.classification_agent = ClassificationAgent()
        self.recommendation_agent = RecommendationAgent(
            'recommendation_objects/apriori_recommendations.json',
            'recommendation_objects/popularity_recommendation.csv'
        )

        self.agent_dict: dict[str, AgentProtocol] = {
            "details_agent": DetailsAgent(),
            "order_taking_agent": OrderTakingAgent(self.recommendation_agent, menu_text),
            "recommendation_agent": self.recommendation_agent
        }

    async def get_response(self, input):
        start = time.perf_counter()
        reset_token_counter()

        job_input = input["input"]
        messages = job_input["messages"]

        guard_agent_response = await self.guard_agent.get_response(messages)
        guard_decision = guard_agent_response["memory"]["guard_decision"]
        log.info("guard_decision", decision=guard_decision)

        if guard_decision == "not allowed":
            self._record(start, guard_decision, chosen_agent=None)
            return guard_agent_response

        classification_agent_response = await self.classification_agent.get_response(messages)
        chosen_agent = classification_agent_response["memory"]["classification_decision"]
        log.info("agent_routed", agent=chosen_agent)

        agent = self.agent_dict.get(chosen_agent)
        if agent is None:
            log.warning("unknown_agent", agent=chosen_agent)
            self._record(start, guard_decision, chosen_agent=chosen_agent)
            return {
                "role": "assistant",
                "content": "I'm having trouble understanding your request. Could you rephrase that?",
                "memory": {"agent": "classification_agent", "error": f"unknown_agent:{chosen_agent}"}
            }

        response = await agent.get_response(messages)
        self._record(start, guard_decision, chosen_agent=chosen_agent)
        return response

    async def get_stream_response(self, input) -> AsyncGenerator[dict, None]:
        start = time.perf_counter()
        reset_token_counter()

        job_input = input["input"]
        messages = job_input["messages"]

        guard_agent_response = await self.guard_agent.get_response(messages)
        guard_decision = guard_agent_response["memory"]["guard_decision"]
        log.info("guard_decision", decision=guard_decision)

        if guard_decision == "not allowed":
            self._record(start, guard_decision, chosen_agent=None)
            async for event in self._fake_stream(guard_agent_response):
                yield event
            return

        classification_agent_response = await self.classification_agent.get_response(messages)
        chosen_agent = classification_agent_response["memory"]["classification_decision"]
        log.info("agent_routed", agent=chosen_agent)

        agent = self.agent_dict.get(chosen_agent)
        if agent is None:
            log.warning("unknown_agent", agent=chosen_agent)
            self._record(start, guard_decision, chosen_agent=chosen_agent)
            fallback = {
                "role": "assistant",
                "content": "I'm having trouble understanding your request. Could you rephrase that?",
                "memory": {"agent": "classification_agent", "error": f"unknown_agent:{chosen_agent}"}
            }
            async for event in self._fake_stream(fallback):
                yield event
            return

        self._record(start, guard_decision, chosen_agent=chosen_agent)

        if hasattr(agent, 'get_stream_response'):
            async for event in agent.get_stream_response(messages):
                yield event
        else:
            response = await agent.get_response(messages)
            async for event in self._fake_stream(response):
                yield event

    @staticmethod
    async def _fake_stream(response: dict) -> AsyncGenerator[dict, None]:
        content = response.get("content", "")
        words = content.split(" ")
        for i, word in enumerate(words):
            delta = word if i == len(words) - 1 else word + " "
            yield {"type": "token", "delta": delta}
        yield {"type": "done", "memory": response.get("memory", {})}

    def _record(self, start: float, guard_decision: str, chosen_agent: str | None) -> None:
        if self.metrics is None:
            return
        tokens = get_token_counts()
        self.metrics.record(
            total_ms=round((time.perf_counter() - start) * 1000),
            guard_decision=guard_decision,
            chosen_agent=chosen_agent,
            input_tokens=tokens["input"],
            output_tokens=tokens["output"],
        )
