"""
Vision module for image-based location search.

This module provides image search functionality using ResNet embeddings
and FAISS similarity search to identify Vietnamese tourism locations from photos.
"""

from .image_search import ImageSearchEngine, get_image_search_engine

__all__ = ['ImageSearchEngine', 'get_image_search_engine']
