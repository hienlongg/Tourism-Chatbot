"""
LangChain Embedding Adapter for Remote Embeddings

This module provides a LangChain-compatible wrapper around RemoteEmbeddingClient
so it can be used seamlessly with ChromaDB and other LangChain components.

Usage:
    from tourism_chatbot.clients.langchain_embedding_adapter import RemoteEmbeddingsAdapter
    from langchain_chroma import Chroma
    
    embeddings = RemoteEmbeddingsAdapter(space_url="https://your-space.hf.space")
    vector_store = Chroma(..., embedding_function=embeddings)
"""

import logging
from typing import List
from langchain_core.embeddings import Embeddings
from tourism_chatbot.clients.embedding_client import RemoteEmbeddingClient, LocalEmbeddingClient

logger = logging.getLogger(__name__)


class RemoteEmbeddingsAdapter(Embeddings):
    """
    LangChain-compatible wrapper for RemoteEmbeddingClient.
    
    Adapts the RemoteEmbeddingClient to work with LangChain's Embeddings interface,
    allowing it to be used with ChromaDB and other LangChain components.
    """
    
    def __init__(
        self,
        space_url: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        fallback_to_local: bool = True,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        verbose: bool = False
    ):
        """
        Initialize LangChain embedding adapter.
        
        Args:
            space_url: Full URL of the HF Space
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            fallback_to_local: If True, use local embeddings if remote fails
            model_name: Model name for fallback local embeddings
            verbose: If True, log detailed information
        """
        self.space_url = space_url
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.fallback_to_local = fallback_to_local
        self.model_name = model_name
        self.verbose = verbose
        self.client = None
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize embedding client (remote or fallback to local)."""
        try:
            self.client = RemoteEmbeddingClient(
                space_url=self.space_url,
                timeout=self.timeout,
                verify_ssl=self.verify_ssl,
                verbose=self.verbose
            )
            logger.info("✅ Using remote embeddings from HF Spaces")
        except Exception as e:
            logger.warning(f"⚠️  Remote embeddings unavailable: {e}")
            
            if self.fallback_to_local:
                logger.info("Falling back to local embeddings...")
                self.client = LocalEmbeddingClient(model_name=self.model_name)
            else:
                raise
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed search docs (required by LangChain interface).
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        return self.client.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed query text (required by LangChain interface).
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        return self.client.embed_query(text)
