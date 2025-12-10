"""
Embedding API - Hugging Face Spaces Microservice

Vietnamese Tourism Embedding API
Provides semantic embeddings for tourism-related text and documents.
"""

from .app import create_app

__version__ = "1.0.0"

__all__ = ["create_app"]
