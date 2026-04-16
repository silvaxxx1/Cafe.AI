"""
CLI chat client for quick local testing — no frontend needed.

Usage:
    cd coffee_shop_customer_service_chatbot/python_code/api
    python development_code.py
"""
import asyncio
import os
from agent_controller import AgentController


async def main():
    controller = AgentController()
    messages = []

    print("\nCafe.AI — CLI Chat (Ctrl+C to quit)\n")

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        print("\n── Conversation ──────────────────────────────────")
        for message in messages:
            print(f"{message['role'].capitalize()}: {message['content']}")
        print("──────────────────────────────────────────────────\n")

        prompt = input("You: ").strip()
        if not prompt:
            continue

        messages.append({"role": "user", "content": prompt})

        response = await controller.get_response({"input": {"messages": messages}})

        print(f"\n[agent: {response['memory'].get('agent', '?')}]")
        messages.append(response)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")
