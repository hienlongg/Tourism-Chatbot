"""
Chat models for conversations and messages.
"""

from mongoengine import (
    Document, EmbeddedDocument, StringField, DateTimeField,
    ObjectIdField, ReferenceField, EmbeddedDocumentField, CASCADE
)
from bson.objectid import ObjectId
from datetime import datetime, timezone


class LastMessageModel(EmbeddedDocument):
    """Embedded document for storing last message info in conversations."""
    
    SenderID = StringField(required=True)
    Content = StringField(required=True)
    CreatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))


class ConversationModel(Document):
    """Model for chat conversations between users."""
    
    ConversationID = ObjectIdField(primary_key=True, default=ObjectId)
    CounsellorID = StringField(required=True)
    StudentID = StringField(required=True)
    LastMessage = EmbeddedDocumentField(LastMessageModel)
    CreatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    UpdatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    meta = {
        "db_alias": "ChatDB",
        "collection": "Conversations",
        "indexes": [
            "CounsellorID",
            "StudentID",
            "-UpdatedAt"
        ]
    }


class MessageModel(Document):
    """Model for individual messages in conversations."""
    
    MessageID = ObjectIdField(primary_key=True, default=ObjectId)
    InConversationID = ReferenceField(
        "ConversationModel",
        required=True,
        reverse_delete_rule=CASCADE
    )
    SenderID = StringField(required=True)
    Content = StringField(required=True)
    CreatedAt = DateTimeField(default=lambda: datetime.now(timezone.utc))
    
    meta = {
        "db_alias": "ChatDB",
        "collection": "Messages",
        "indexes": [
            "InConversationID",
            "-CreatedAt"
        ]
    }
