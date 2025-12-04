"""Routes package initialization.
Exports authentication and chat blueprints.
"""

from .auth import auth_bp
from .chat import chat_bp, init_chatbot

__all__ = ['auth_bp', 'chat_bp', 'init_chatbot']
