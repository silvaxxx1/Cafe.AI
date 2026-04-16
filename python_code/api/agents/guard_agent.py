from dotenv import load_dotenv
import os
import json
from copy import deepcopy
from .utils import get_chatbot_response
from openai import AsyncOpenAI
load_dotenv()

class GuardAgent():
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")

    async def get_response(self, messages):
        messages = deepcopy(messages)

        system_prompt = """
            You are a helpful AI assistant for a coffee shop application which serves drinks and pastries.
            Your task is to determine whether the user is asking something relevant to the coffee shop or not.
            When in doubt, allow the message. It is better to pass a borderline message than to wrongly block a customer.

            The user is allowed to:
            1. Ask questions about the coffee shop — its name, story, history, location, hours, atmosphere, or anything about the business.
            2. Ask questions about menu items — ingredients, details, allergens, descriptions, prices.
            3. Make an order or modify an existing order — including ordering items that may not be on the menu (the order agent will handle invalid items).
            4. Ask for recommendations on what to buy.
            5. Ask follow-up questions or say things like "no", "yes", "that's all", "confirm my order" during a conversation.

            The user is NOT allowed to:
            1. Ask about topics completely unrelated to the coffee shop (e.g. politics, coding, weather, sports, general trivia).
            2. Ask how to recreate or manufacture a menu item at home.

            IMPORTANT: If a user tries to order something (even if it sounds like non-coffee-shop food), treat it as an order attempt and allow it. The order agent will tell them if the item is unavailable.

            Your output should be in a structured json format like so. each key is a string and each value is a string. Make sure to follow the format exactly:
            {
            "chain of thought": go over each of the points above and make see if the message lies under this point or not. Then you write some your thoughts about what point is this input relevant to.
            "decision": "allowed" or "not allowed". Pick one of those. and only write the word.
            "message": leave the message empty if it's allowed, otherwise write "Sorry, I can't help with that. Can I help you with your order?"
            }
            """

        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output = await get_chatbot_response(self.client, self.model_name, input_messages, json_mode=True)
        output = self.postprocess(chatbot_output)

        return output

    def postprocess(self, output):
        try:
            output = json.loads(output)
            decision = output.get('decision', 'allowed')
            message  = output.get('message', '')
        except (json.JSONDecodeError, KeyError):
            decision = 'allowed'
            message  = ''

        return {
            "role": "assistant",
            "content": message,
            "memory": {"agent": "guard_agent", "guard_decision": decision}
        }
