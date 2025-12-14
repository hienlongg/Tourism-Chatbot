"""Routes package initialization.
Exports authentication, chat, upload, travel log, and posts blueprints.
"""

from .authentication import auth_bp
from .chat import chat_bp, init_chatbot
from .upload import upload_bp
from .travel_log import travel_log_bp
from .posts import posts_bp

__all__ = ['auth_bp', 'chat_bp', 'init_chatbot', 'upload_bp', 'travel_log_bp', 'posts_bp']
