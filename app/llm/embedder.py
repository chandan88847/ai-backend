# app/llm/embedder.py
from openai import OpenAI
import os
from langchain_openai import OpenAIEmbeddings


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str, model="text-embedding-3-small"):
    response = client.embeddings.create(
        input=[text],
        model=model
    )
    return response.data[0].embedding



def get_embedding_vector():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )


# # Local transformer model: all-MiniLM-L6-v2 (from HuggingFace/SBERT).
# from sentence_transformers import SentenceTransformer

# class Embedder:
#     def __init__(self, model_name="all-MiniLM-L6-v2"):
#         self.model = SentenceTransformer(model_name)

#     def embed(self, texts: list[str]) -> list[list[float]]:
#         return self.model.encode(texts, convert_to_tensor=False)

