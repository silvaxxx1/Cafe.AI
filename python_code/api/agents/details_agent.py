from dotenv import load_dotenv
import os
import asyncio
from .utils import get_chatbot_response
from openai import AsyncOpenAI
from copy import deepcopy
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
load_dotenv()


class DetailsAgent():
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")

        pinecone_key = os.getenv("PINECONE_API_KEY")
        self.rag_enabled = bool(pinecone_key)

        if self.rag_enabled:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.pc = Pinecone(api_key=pinecone_key)
            self.index_name = os.getenv("PINECONE_INDEX_NAME")
            print("[DetailsAgent] RAG enabled — local embeddings + Pinecone.")
        else:
            print("[DetailsAgent] RAG disabled — PINECONE_API_KEY not set.")

    def get_closest_results(self, index_name, embedding, top_k=2):
        index = self.pc.Index(index_name)
        return index.query(
            namespace="ns1",
            vector=embedding,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

    async def get_response(self, messages):
        messages = deepcopy(messages)

        if not self.rag_enabled:
            return {
                "role": "assistant",
                "content": "I don't have detailed product info available right now, but I'd be happy to help you place an order or give you a recommendation!",
                "memory": {"agent": "details_agent"}
            }

        user_message = messages[-1]['content']

        # Run the sync embedding model in a thread so we don't block the event loop
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.embedding_model.encode(user_message).tolist()
        )

        result = self.get_closest_results(self.index_name, embedding)
        source_knowledge = "\n".join(
            [x['metadata']['text'].strip() + '\n' for x in result['matches']]
        )

        prompt = f"""
        Using the contexts below, answer the query.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = "You are a customer support agent for a coffee shop called Fero Cafe. You should answer every question as if you are a waiter and provide the necessary information to the user regarding their orders."
        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output = await get_chatbot_response(self.client, self.model_name, input_messages)
        return self.postprocess(chatbot_output)

    def postprocess(self, output):
        return {
            "role": "assistant",
            "content": output,
            "memory": {"agent": "details_agent"}
        }
