import chromadb
import re
import os
from typing import List, Dict, Any

def sanitize_filename(url: str) -> str:
    """
    Sanitizes a URL to create a valid, consistent, and clean filesystem path component.
    This logic MUST be used in both the embedding and query stages.
    """
    sanitized = re.sub(r'https?://', '', url)
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', sanitized)
    sanitized = re.sub(r'__+', '_', sanitized)
    sanitized = sanitized.strip('_')
    if sanitized.endswith('.git'):
        sanitized = sanitized[:-4]
    return sanitized

class ChromaVectorStore:
    def __init__(self, repo_url: str, embedder: Any, collection_name="code_and_docs_collection"):
        """
        Initializes the vector store for a specific repository,
        and accepts an embedder object to handle query embeddings.
        """
        if not repo_url:
            raise ValueError("A repo_url is required to initialize the ChromaVectorStore.")
        
        self.embedder = embedder
        sanitized_repo_name = sanitize_filename(repo_url)
        
        # Using an absolute path is more reliable
        # This assumes your script runs in a way that this relative path works.
        # Adjust if your project structure is different.
        persist_directory = os.path.abspath(os.path.join("./vector_stores", sanitized_repo_name))

        if not os.path.exists(persist_directory):
            raise FileNotFoundError(f"Vector store for repo '{repo_url}' not found at '{persist_directory}'. Please ensure the embeddings have been generated first.")

        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Now, this will get the collection created by the embedding script
        self.collection = self.client.get_collection(name=collection_name)

    def search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Embeds the query text and searches the collection, returning the document content.
        """
        if not self.embedder:
            raise RuntimeError("Embedder not initialized in ChromaVectorStore.")
            
        # Embed the query text using the LangChain embedder
        query_embedding = self.embedder.embed_query(query_text)

        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas", "distances", "documents"] # Ensure documents are included
        )
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return []

        # Combine results into a clean list of dictionaries
        combined_results = []
        for i in range(len(results['ids'][0])):
            combined_results.append({
                "id": results['ids'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i],
                "document": results['documents'][0][i]
            })
        
        return combined_results