from dotenv import load_dotenv
import os
import asyncio
from .utils import get_chatbot_response, get_chatbot_response_stream, CONTEXT_WINDOW
from openai import AsyncOpenAI
from copy import deepcopy
from sentence_transformers import SentenceTransformer
load_dotenv()

# ChromaDB imported lazily to avoid startup errors when the index doesn't exist
try:
    import chromadb
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False

_DEFAULT_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")


class DetailsAgent():
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")
        self.rag_enabled = False

        if not _CHROMA_AVAILABLE:
            print("[DetailsAgent] RAG disabled — chromadb package not installed.")
            return

        chroma_path = os.getenv("CHROMA_DB_PATH", _DEFAULT_CHROMA_PATH)

        if not os.path.isdir(chroma_path):
            print("[DetailsAgent] RAG disabled — chroma_db not found. Run python_code/build_index.py first.")
            return

        try:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            chroma_client = chromadb.PersistentClient(path=chroma_path)
            self.collection = chroma_client.get_collection("coffeeshop")
            self.rag_enabled = True
            print("[DetailsAgent] RAG enabled — local embeddings + ChromaDB.")
        except Exception as e:
            print(f"[DetailsAgent] RAG disabled — could not load collection: {e}")
            print("               Run python_code/build_index.py to build the index.")

    def get_closest_results(self, embedding, top_k=2):
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )
        return results["documents"][0]  # list of matching text strings

    async def get_response(self, messages):
        messages = deepcopy(messages)

        if not self.rag_enabled:
            return {
                "role": "assistant",
                "content": "I don't have detailed product info available right now, but I'd be happy to help you place an order or give you a recommendation!",
                "memory": {"agent": "details_agent"}
            }

        user_message = messages[-1]['content']

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.embedding_model.encode(user_message).tolist()
        )

        chunks = self.get_closest_results(embedding)
        source_knowledge = "\n".join(chunk.strip() for chunk in chunks)

        prompt = f"""
        Using the contexts below, answer the query.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = "You are a customer support agent for a coffee shop called Fero Cafe. You should answer every question as if you are a waiter and provide the necessary information to the user regarding their orders."
        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-CONTEXT_WINDOW:]

        chatbot_output = await get_chatbot_response(self.client, self.model_name, input_messages)
        return self.postprocess(chatbot_output)

    def postprocess(self, output):
        return {
            "role": "assistant",
            "content": output,
            "memory": {"agent": "details_agent"}
        }

    async def get_stream_response(self, messages):
        messages = deepcopy(messages)

        if not self.rag_enabled:
            content = "I don't have detailed product info available right now, but I'd be happy to help you place an order or give you a recommendation!"
            yield {"type": "token", "delta": content}
            yield {"type": "done", "memory": {"agent": "details_agent"}}
            return

        user_message = messages[-1]['content']

        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self.embedding_model.encode(user_message).tolist()
        )

        chunks = self.get_closest_results(embedding)
        source_knowledge = "\n".join(chunk.strip() for chunk in chunks)

        prompt = f"""
        Using the contexts below, answer the query.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = "You are a customer support agent for a coffee shop called Fero Cafe. You should answer every question as if you are a waiter and provide the necessary information to the user regarding their orders."
        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-CONTEXT_WINDOW:]

        async for token in get_chatbot_response_stream(self.client, self.model_name, input_messages):
            yield {"type": "token", "delta": token}

        yield {"type": "done", "memory": {"agent": "details_agent"}}
