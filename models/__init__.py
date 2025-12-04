"""
Models package initialization.
Exports all database models and initializes MongoDB connections.
"""

from mongoengine import connect
from .user import UserModel
from .chat import ConversationModel, MessageModel, LastMessageModel
from config import Config

# Initialize MongoDB connections
connect(
    db="Authentication",
    alias="AuthenticationDB",
    host=Config.MONGODB_URI
)

connect(
    db="Chat",
    alias="ChatDB",
    host=Config.MONGODB_URI
)

__all__ = [
    'UserModel',
    'ConversationModel',
    'MessageModel',
    'LastMessageModel'
]
