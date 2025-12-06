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
    
    sender_id = StringField(required=True, db_field="SenderID")
    content = StringField(required=True, db_field="Content")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="CreatedAt")


class ConversationModel(Document):
    """Model for chat conversations between users."""
    
    conversation_id = ObjectIdField(primary_key=True, default=ObjectId, db_field="ConversationID")
    counsellor_id = StringField(required=True, db_field="CounsellorID")
    student_id = StringField(required=True, db_field="StudentID")
    last_message = EmbeddedDocumentField(LastMessageModel, db_field="LastMessage")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="CreatedAt")
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="UpdatedAt")
    
    meta = {
        "db_alias": "ChatDB",
        "collection": "Conversations",
        "indexes": [
            "counsellor_id",
            "student_id",
            "-updated_at"
        ]
    }


class MessageModel(Document):
    """Model for individual messages in conversations."""
    
    message_id = ObjectIdField(primary_key=True, default=ObjectId, db_field="MessageID")
    in_conversation_id = ReferenceField(
        "ConversationModel",
        required=True,
        reverse_delete_rule=CASCADE,
        db_field="InConversationID"
    )
    sender_id = StringField(required=True, db_field="SenderID")
    content = StringField(required=True, db_field="Content")
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="CreatedAt")
    
    meta = {
        "db_alias": "ChatDB",
        "collection": "Messages",
        "indexes": [
            "in_conversation_id",
            "-created_at"
        ]
    }
