"""
Embedding API Client for HuggingFace Spaces

This module provides a client to interact with the remote embedding model
hosted on Hugging Face Spaces. It wraps the HTTP API calls to make them
compatible with the existing LangChain interface.

Usage:
    from tourism_chatbot.clients.embedding_client import RemoteEmbeddingClient
    
    client = RemoteEmbeddingClient(space_url="https://yourusername-tourism-embedding.hf.space")
    embedding = client.embed_query("beautiful waterfalls")
"""

import requests
import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmbeddingClient(ABC):
    """Abstract base class for embedding clients."""
    
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        pass
    
    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        pass


class RemoteEmbeddingClient(EmbeddingClient):
    """
    Client for remote embedding API (Hugging Face Spaces).
    
    Communicates with the Gradio app via HTTP REST API.
    This allows the main backend to stay lightweight while offloading
    embedding computation to HF Spaces.
    """
    
    def __init__(
        self,
        space_url: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        verbose: bool = False
    ):
        """
        Initialize remote embedding client.
        
        Args:
            space_url: Full URL of the HF Space (e.g., https://yourusername-tourism-embedding.hf.space)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            verbose: If True, log API calls
        """
        self.space_url = space_url.rstrip('/')  # Remove trailing slash
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.verbose = verbose
        
        logger.info(f"🔗 Initialized RemoteEmbeddingClient: {self.space_url}")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to remote embedding API."""
        try:
            response = requests.get(self.space_url, timeout=5, verify=self.verify_ssl)
            if response.status_code == 200:
                logger.info("✅ Successfully connected to embedding API")
            else:
                logger.warning(f"⚠️  API returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to embedding API: {e}")
            raise ConnectionError(f"Cannot reach embedding API at {self.space_url}") from e
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector as list of floats
        
        Raises:
            requests.RequestException: If API call fails
        """
        if self.verbose:
            logger.info(f"📤 Embedding query: {text[:100]}...")
        
        try:
            response = requests.post(
                f"{self.space_url}/run/embed_text",
                json={"data": [text]},
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            result = response.json()
            embedding = result["data"][0]
            
            if self.verbose:
                logger.info(f"📥 Received embedding (dim={len(embedding)})")
            
            return embedding
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Embedding API error: {e}")
            raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        
        Raises:
            requests.RequestException: If API call fails
        """
        if not texts:
            return []
        
        if self.verbose:
            logger.info(f"📤 Embedding {len(texts)} documents...")
        
        try:
            # Convert list to multi-line string (one doc per line)
            docs_str = '\n'.join(texts)
            
            response = requests.post(
                f"{self.space_url}/run/embed_documents",
                json={"data": [docs_str]},
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            response.raise_for_status()
            
            result = response.json()
            embeddings = result["data"][0]  # Returns list of embeddings
            
            if self.verbose:
                logger.info(f"📥 Received {len(embeddings)} embeddings")
            
            return embeddings
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Embedding API error: {e}")
            raise


class LocalEmbeddingClient(EmbeddingClient):
    """
    Fallback client for local embeddings.
    
    Use this when HF Space is unavailable for development/testing.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize local embedding client.
        
        Args:
            model_name: HuggingFace model name
        """
        logger.info(f"🤖 Loading local embedding model: {model_name}")
        
        from langchain_huggingface import HuggingFaceEmbeddings
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info("✅ Local embedding model loaded")
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query using local model."""
        return self.embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents using local model."""
        return self.embeddings.embed_documents(texts)


def get_embedding_client(
    use_remote: bool = True,
    space_url: str = None,
    fallback_to_local: bool = True,
    verbose: bool = False
) -> EmbeddingClient:
    """
    Factory function to get appropriate embedding client.
    
    Strategy:
    1. If use_remote=True and space_url provided, try RemoteEmbeddingClient
    2. If remote fails and fallback_to_local=True, use LocalEmbeddingClient
    3. Otherwise, raise error
    
    Args:
        use_remote: Whether to attempt remote embedding API
        space_url: HF Space URL (required if use_remote=True)
        fallback_to_local: If True, use local embeddings on remote failure
        verbose: If True, log detailed information
    
    Returns:
        EmbeddingClient instance
    
    Raises:
        ValueError: If configuration is invalid
    """
    if use_remote:
        if not space_url:
            raise ValueError("space_url required when use_remote=True")
        
        try:
            return RemoteEmbeddingClient(space_url, verbose=verbose)
        except Exception as e:
            logger.warning(f"⚠️  Remote embedding failed: {e}")
            
            if fallback_to_local:
                logger.info("Falling back to local embeddings...")
                return LocalEmbeddingClient()
            else:
                raise
    else:
        return LocalEmbeddingClient()
