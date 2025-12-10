"""
Shared utilities for all Hugging Face Spaces APIs.

This module provides common functionality used across multiple microservices
deployed on Hugging Face Spaces (embedding, chat, images, etc).
"""

from .constants import *
from .base_api import BaseGradioAPI

__all__ = [
    'BaseGradioAPI',
    'API_TIMEOUT',
    'MAX_BATCH_SIZE',
    'DEFAULT_MODEL',
]
