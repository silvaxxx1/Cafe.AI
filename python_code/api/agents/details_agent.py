from dotenv import load_dotenv
import os
from .utils import get_chatbot_response,get_embedding
from openai import OpenAI
from copy import deepcopy
from pinecone import Pinecone
load_dotenv()

class DetailsAgent():
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("RUNPOD_TOKEN"),
            base_url=os.getenv("RUNPOD_CHATBOT_URL"),
        )
        self.model_name = os.getenv("MODEL_NAME")

        embedding_url = os.getenv("RUNPOD_EMBEDDING_URL")
        pinecone_key  = os.getenv("PINECONE_API_KEY")
        self.rag_enabled = bool(embedding_url and pinecone_key)

        if self.rag_enabled:
            self.embedding_client = OpenAI(
                api_key=os.getenv("RUNPOD_TOKEN"),
                base_url=embedding_url,
            )
            self.pc = Pinecone(api_key=pinecone_key)
            self.index_name = os.getenv("PINECONE_INDEX_NAME")
        else:
            print("[DetailsAgent] RAG disabled — RUNPOD_EMBEDDING_URL or PINECONE_API_KEY not set.")
    
    def get_closest_results(self,index_name,input_embeddings,top_k=2):
        index = self.pc.Index(index_name)
        
        results = index.query(
            namespace="ns1",
            vector=input_embeddings,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )

        return results

    def get_response(self,messages):
        messages = deepcopy(messages)

        if not self.rag_enabled:
            return {
                "role": "assistant",
                "content": "I don't have detailed product info available right now, but I'd be happy to help you place an order or give you a recommendation!",
                "memory": {"agent": "details_agent"}
            }

        user_message = messages[-1]['content']
        embedding = get_embedding(self.embedding_client,self.model_name,user_message)[0]
        result = self.get_closest_results(self.index_name,embedding)
        source_knowledge = "\n".join([x['metadata']['text'].strip()+'\n' for x in result['matches'] ])

        prompt = f"""
        Using the contexts below, answer the query.

        Contexts:
        {source_knowledge}

        Query: {user_message}
        """

        system_prompt = """ You are a customer support agent for a coffee shop called Merry's way. You should answer every question as if you are waiter and provide the neccessary information to the user regarding their orders """
        messages[-1]['content'] = prompt
        input_messages = [{"role": "system", "content": system_prompt}] + messages[-3:]

        chatbot_output =get_chatbot_response(self.client,self.model_name,input_messages)
        output = self.postprocess(chatbot_output)
        return output

    def postprocess(self,output):
        output = {
            "role": "assistant",
            "content": output,
            "memory": {"agent":"details_agent"
                      }
        }
        return output

    
