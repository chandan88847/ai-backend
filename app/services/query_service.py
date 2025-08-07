# app/services/query_service.py
from app.repositories.vector_store import ChromaVectorStore
from app.llm.embedder import get_embedding_vector
from app.llm.call_llm import call_llm
import logging

def answer_query(user_query: str, repo_url: str):
    """
    Orchestrates the RAG pipeline: embed query, search docs, and generate answer.
    """
    try:
        # Step 1: Get the embedder instance
        embedder_instance = get_embedding_vector() 

        # Step 2: Initialize the vector store, passing the embedder
        # This will now correctly connect to the 'code_and_docs_collection' by default
        store = ChromaVectorStore(repo_url=repo_url, embedder=embedder_instance)
        
        # Step 3: Search the vector store with the user's query
        docs = store.search(user_query)
        
        # Step 4: If no relevant documents are found, return a helpful message
        if not docs:
            logging.warning(f"No relevant documents found for query: '{user_query}' in repo: '{repo_url}'")
            return "I'm sorry, I couldn't find any relevant information in the available documents to answer your question."

        # Step 5: Build a context string from the retrieved documents
        context = "\n\n---\n\n".join(
            [
                f"Source: {doc['metadata'].get('source', 'Unknown')}\n\nContent:\n{doc.get('document', '')}"
                for doc in docs
            ]
        )

        # Step 6: Create a RAG-style prompt
        prompt = f"""
You are a helpful assistant that answers questions using only the provided context.

Instructions:
- Use only the factual information from the context below.
- If the context does not provide enough information, state that you cannot answer based on the provided documents.
- Do not make up or guess answers.

Context:
{context}

Question: {user_query}

Answer:
"""
        # Step 7: Call the LLM to generate an answer
        return call_llm(prompt)
        
    except FileNotFoundError as e:
        logging.error(f"FileNotFoundError in answer_query: {e}")
        return str(e)
    except Exception as e:
        logging.error(f"An unexpected error occurred in answer_query: {e}", exc_info=True)
        return f"An unexpected error occurred: {e}"