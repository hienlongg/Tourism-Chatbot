"""
LangChain Embedding Adapter

Makes remote embeddings compatible with LangChain's Embeddings interface.
Allows ChromaDB to use remote embeddings transparently.
"""

from langchain_core.embeddings import Embeddings
from typing import List
import logging

from .embedding_client import EmbeddingClient

logger = logging.getLogger(__name__)


class RemoteEmbeddingsAdapter(Embeddings):
    """
    LangChain-compatible wrapper for remote embedding API.
    
    This allows ChromaDB and other LangChain components to use
    remote embeddings from Hugging Face Spaces transparently.
    """
    
    def __init__(self, client: EmbeddingClient):
        """
        Initialize adapter with embedding client.
        
        Args:
            client: EmbeddingClient instance
        """
        self.client = client
        logger.info("🔗 RemoteEmbeddingsAdapter initialized")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embed multiple documents.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.client.embed_documents(texts)
            logger.info(f"✅ Embedded {len(texts)} documents via adapter")
            return embeddings
        except Exception as e:
            logger.error(f"❌ Error in embed_documents: {e}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """
        Embed a single query.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            embedding = self.client.embed_query(text)
            logger.info(f"✅ Embedded query via adapter")
            return embedding
        except Exception as e:
            logger.error(f"❌ Error in embed_query: {e}")
            raise
