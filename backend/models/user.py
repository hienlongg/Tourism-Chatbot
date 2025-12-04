"""
User model for authentication.
Handles user data, password hashing, and verification.
"""

from mongoengine import Document, StringField, DateTimeField, ObjectIdField
from bson.objectid import ObjectId
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


class UserModel(Document):
    """User model for storing authentication data."""
    
    user_id = ObjectIdField(primary_key=True, default=ObjectId, db_field="UserID")
    email = StringField(required=True, unique=True, db_field="Email")
    hashed_password = StringField(required=True, db_field="HashedPassword")
    role = StringField(
        choices=["Student", "Counsellor", "AI"],
        default="Student",
        db_field="Role"
    )
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="CreatedAt")
    
    meta = {
        "db_alias": "AuthenticationDB",
        "collection": "Users"
    }
    
    @classmethod
    def create_user(cls, email: str, plain_password: str):
        """
        Create a new user with hashed password.
        
        Args:
            email: User's email address
            plain_password: Plain text password
            
        Returns:
            UserModel instance (not saved to database yet)
        """
        hashed = generate_password_hash(
            plain_password,
            method="pbkdf2:sha256",
            salt_length=16
        )
        return cls(email=email, hashed_password=hashed)
    
    def check_password(self, plain_password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.hashed_password, plain_password)
