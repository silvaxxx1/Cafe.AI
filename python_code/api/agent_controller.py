import json
from agents import (GuardAgent,
                    ClassificationAgent,
                    DetailsAgent,
                    OrderTakingAgent,
                    RecommendationAgent,
                    AgentProtocol
                    )

class AgentController():
    def __init__(self):
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
        job_input = input["input"]
        messages = job_input["messages"]

        guard_agent_response = await self.guard_agent.get_response(messages)
        if guard_agent_response["memory"]["guard_decision"] == "not allowed":
            return guard_agent_response

        classification_agent_response = await self.classification_agent.get_response(messages)
        chosen_agent = classification_agent_response["memory"]["classification_decision"]

        agent = self.agent_dict[chosen_agent]
        response = await agent.get_response(messages)

        return response
