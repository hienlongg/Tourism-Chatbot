"""
RAG Tourism Recommendation Package

This package contains the core RAG functionality for Vietnamese tourism recommendations.
"""

from .rag_engine import (
    initialize_rag_system,
    generate_recommendation,
    generate_recommendation_stream,
    slugify,
    CSV_PATH,
    CHROMA_DB_PATH,
    EMBEDDING_MODEL,
    GEMINI_MODEL,
    TOP_K_RESULTS
)

__all__ = [
    'initialize_rag_system',
    'generate_recommendation',
    'generate_recommendation_stream',
    'slugify',
    'CSV_PATH',
    'CHROMA_DB_PATH',
    'EMBEDDING_MODEL',
    'GEMINI_MODEL',
    'TOP_K_RESULTS'
]

__version__ = '1.0.0'
