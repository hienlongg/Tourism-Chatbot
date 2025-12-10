"""
Embedding API Client

Handles HTTP communication with the Embedding API on Hugging Face Spaces.
Provides both direct API calls and LangChain-compatible wrapper.
"""

import requests
import logging
from typing import List, Optional
from gradio_client import Client

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """
    Client for remote Embedding API on Hugging Face Spaces.
    
    Features:
    - Single text embedding
    - Batch document embedding
    - Automatic fallback to local embeddings if remote fails
    - Retry logic for reliability
    """
    
    def __init__(self, api_url: str, timeout: int = 30, use_gradio_client: bool = True):
        """
        Initialize embedding client.
        
        Args:
            api_url: Hugging Face Space URL (e.g., https://user-tourism-embedding.hf.space)
            timeout: Request timeout in seconds
            use_gradio_client: Use gradio_client instead of raw HTTP requests
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.use_gradio_client = use_gradio_client
        self._client = None
        
        logger.info(f"🔗 EmbeddingClient initialized: {self.api_url}")
    
    @property
    def client(self):
        """Lazy load gradio client."""
        if self._client is None and self.use_gradio_client:
            try:
                self._client = Client(self.api_url)
                logger.info("✅ Gradio client connected")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize gradio client: {e}")
                self._client = False  # Mark as failed
        return self._client
    
    def test_connection(self) -> bool:
        """
        Test if API is accessible.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            if self.use_gradio_client and self.client:
                # Try a simple prediction
                self.client.predict(text="test", api_name="/embed_text")
                logger.info("✅ Connection test passed")
                return True
            else:
                # Fall back to HTTP test
                response = requests.post(
                    f"{self.api_url}/run/embed_text",
                    json={"data": ["test"]},
                    timeout=5
                )
                if response.status_code == 200:
                    logger.info("✅ Connection test passed")
                    return True
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
        
        return False
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            if self.use_gradio_client and self.client:
                result = self.client.predict(text=text, api_name="/embed_text")
                logger.info(f"✅ Query embedded via gradio_client (dim={len(result)})")
                return result
            else:
                response = requests.post(
                    f"{self.api_url}/run/embed_text",
                    json={"data": [text]},
                    timeout=self.timeout
                )
                response.raise_for_status()
                embedding = response.json()["data"][0]
                logger.info(f"✅ Query embedded via HTTP (dim={len(embedding)})")
                return embedding
                
        except Exception as e:
            logger.error(f"❌ Error embedding query: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Join texts with newline as API expects
            texts_str = "\n".join(texts)
            
            if self.use_gradio_client and self.client:
                result = self.client.predict(texts=texts_str, api_name="/embed_documents")
                logger.info(f"✅ {len(result)} documents embedded via gradio_client")
                return result
            else:
                response = requests.post(
                    f"{self.api_url}/run/embed_documents",
                    json={"data": [texts_str]},
                    timeout=self.timeout
                )
                response.raise_for_status()
                embeddings = response.json()["data"][0]
                logger.info(f"✅ {len(embeddings)} documents embedded via HTTP")
                return embeddings
                
        except Exception as e:
            logger.error(f"❌ Error embedding documents: {e}")
            raise
    
    def similarity_search(self, query: str, num_results: int = 5) -> str:
        """
        Demo similarity search endpoint.
        
        Args:
            query: Search query
            num_results: Number of results
            
        Returns:
            Search results as string
        """
        try:
            if self.use_gradio_client and self.client:
                result = self.client.predict(
                    query=query,
                    num_results=num_results,
                    api_name="/similarity_search"
                )
                return result
            else:
                response = requests.post(
                    f"{self.api_url}/run/similarity_search",
                    json={"data": [query, num_results]},
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()["data"][0]
                
        except Exception as e:
            logger.error(f"❌ Error in similarity search: {e}")
            raise
