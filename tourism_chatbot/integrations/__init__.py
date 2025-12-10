"""
Integration clients for remote APIs on Hugging Face Spaces.

This module provides clients for communicating with various microservices:
- Embedding API
- Chat API (future)
- Image API (future)
"""

from .embedding_client import EmbeddingClient

__all__ = ["EmbeddingClient"]
