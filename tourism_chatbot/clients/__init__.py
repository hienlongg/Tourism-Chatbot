"""
Clients module - Integration with external services

This module provides clients for connecting to external AI services:
- RemoteEmbeddingClient: Calls HuggingFace Spaces embedding API
- LocalEmbeddingClient: Fallback to local embeddings
"""

from .embedding_client import (
    EmbeddingClient,
    RemoteEmbeddingClient,
    LocalEmbeddingClient,
    get_embedding_client,
)

__all__ = [
    'EmbeddingClient',
    'RemoteEmbeddingClient',
    'LocalEmbeddingClient',
    'get_embedding_client',
]
