import os
import json
from .utils import get_chatbot_response
from openai import AsyncOpenAI
from copy import deepcopy
from dotenv import load_dotenv
load_dotenv()


class OrderTakingAgent():
    def __init__(self, recommendation_agent, menu_text: str):
        self.client = AsyncOpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")
        self.recommendation_agent = recommendation_agent
        self.menu_text = menu_text

    async def get_response(self, messages):
        messages = deepcopy(messages)
        system_prompt = f"""
            You are a customer support Bot for a coffee shop called "Fero Cafe"

            here is the menu for this coffee shop.

{self.menu_text}

            Things to NOT DO:
            * DON't ask how to pay by cash or Card.
            * Don't tell the user to go to the counter
            * Don't tell the user to go to place to get the order


            Your task is as follows:
            1. Take the User's Order. When the user mentions multiple items in one message, add ALL of them to the order list at once — never process items one at a time.
            2. Validate that all items are in the menu.
            3. If an item is not in the menu, tell the user and repeat back the remaining valid items.
            4. Ask if they need anything else.
            5. If they do, repeat from step 2.
            6. If they don't want anything else, finalize the order:
                1. List ALL items and their individual prices.
                2. Calculate the correct total.
                3. Thank the user and close the conversation.

            IMPORTANT — Order state rules:
            - The user message starts with "CURRENT ORDER STATE". This is the ground truth.
            - You MUST carry forward every item in that order list. Never drop an item that is already in the order.
            - Only add new items or remove items the user explicitly cancels.
            - If the order state is empty, start fresh from what the user just said.

            CRITICAL RULE — building the order list:
            - First, count every distinct item the user has mentioned across the entire conversation.
            - The "order" array MUST have one entry per item. Two items = two entries. Three items = three entries.
            - NEVER merge two items into one entry. NEVER omit an item.

            produce the following output without any additions, not a single letter outside of the structure bellow.
            Your output should be in a structured json format like so. each key is a string and each value is a string. Make sure to follow the format exactly:
            {{
            "chain of thought": First, LIST every item name the user has mentioned (e.g. "User mentioned: Latte, Croissant"). Then count them. Then write your thinking about the task step and what NOT to do.
            "item_count": The exact integer count of distinct items in the order.
            "step number": Determine which task you are on based on the conversation.
            "order": A JSON array with exactly item_count entries. Each entry: {{"item": "<name>", "quantity": 1, "price": <price>}}. Example with TWO items: [{{"item": "Latte", "quantity": 1, "price": 4.75}}, {{"item": "Croissant", "quantity": 1, "price": 3.25}}]. If the user mentioned 2 items this array MUST have 2 objects.
            "response": write the a response to the user
            }}
        """

        last_order_taking_status = ""
        asked_recommendation_before = False
        for message_index in range(len(messages) - 1, 0, -1):
            message = messages[message_index]
            agent_name = message.get("memory", {}).get("agent", "")
            if message["role"] == "assistant" and agent_name == "order_taking_agent":
                step_number = message["memory"]["step number"]
                order = message["memory"]["order"]
                asked_recommendation_before = message["memory"]["asked_recommendation_before"]
                last_order_taking_status = f"""
                CURRENT ORDER STATE (you MUST include ALL of these items in your output order — do not drop any):
                step number: {step_number}
                order: {order}
                """
                break

        messages[-1]['content'] = last_order_taking_status + " \n " + messages[-1]['content']

        input_messages = [{"role": "system", "content": system_prompt}] + messages

        chatbot_output = await get_chatbot_response(self.client, self.model_name, input_messages, json_mode=True)

        output = await self.postprocess(chatbot_output, messages, asked_recommendation_before)
        return output

    async def postprocess(self, output, messages, asked_recommendation_before):
        try:
            output = json.loads(output)
        except json.JSONDecodeError:
            return {
                "role": "assistant",
                "content": "Sorry, I had trouble processing that. Could you repeat your order?",
                "memory": {
                    "agent": "order_taking_agent",
                    "step number": "1",
                    "order": [],
                    "asked_recommendation_before": asked_recommendation_before
                }
            }

        if type(output["order"]) == str:
            output["order"] = json.loads(output["order"])

        response = output['response']
        if not asked_recommendation_before and len(output["order"]) > 0:
            recommendation_output = await self.recommendation_agent.get_recommendations_from_order(messages, output['order'])
            response = recommendation_output['content']
            asked_recommendation_before = True

        return {
            "role": "assistant",
            "content": response,
            "memory": {
                "agent": "order_taking_agent",
                "step number": output["step number"],
                "order": output["order"],
                "asked_recommendation_before": asked_recommendation_before
            }
        }
