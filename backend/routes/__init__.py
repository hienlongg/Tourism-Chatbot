"""Routes package initialization.
Exports authentication, chat, and upload blueprints.
"""

from .authentication import auth_bp
from .chat import chat_bp, init_chatbot
from .upload import upload_bp

__all__ = ['auth_bp', 'chat_bp', 'init_chatbot', 'upload_bp']
