"""
Memory management module for Tourism Chatbot

This module provides conversation memory and state management:
- Thread-based conversation tracking
- User context management (visited locations, preferences)
- Memory utilities for agents
"""

from .agent_memory import create_agent_with_memory
from .context_manager import UserContextManager

__all__ = [
    'create_agent_with_memory',
    'UserContextManager',
]
