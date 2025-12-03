"""
Thread ID utilities for conversation management
"""

import uuid
from typing import Optional


def generate_thread_id(prefix: Optional[str] = None) -> str:
    """
    Generate a unique thread ID for a conversation.
    
    Args:
        prefix: Optional prefix for the thread ID (e.g., "user_", "session_")
    
    Returns:
        str: Unique thread identifier
    
    Example:
        >>> thread_id = generate_thread_id()
        >>> print(thread_id)
        'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        
        >>> thread_id = generate_thread_id(prefix="user_")
        >>> print(thread_id)
        'user_a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    """
    thread_id = str(uuid.uuid4())
    
    if prefix:
        thread_id = f"{prefix}{thread_id}"
    
    return thread_id


def format_thread_id(user_id: str, session_id: Optional[str] = None) -> str:
    """
    Format a thread ID from user ID and optional session ID.
    
    Args:
        user_id: User identifier
        session_id: Optional session identifier
    
    Returns:
        str: Formatted thread identifier
    
    Example:
        >>> thread_id = format_thread_id("user123")
        >>> print(thread_id)
        'user123'
        
        >>> thread_id = format_thread_id("user123", "session456")
        >>> print(thread_id)
        'user123_session456'
    """
    if session_id:
        return f"{user_id}_{session_id}"
    return user_id
