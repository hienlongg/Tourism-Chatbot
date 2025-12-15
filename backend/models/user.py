"""
User model for authentication.
Handles user data, password hashing, and verification.
"""

from mongoengine import Document, StringField, DateTimeField, ObjectIdField
from bson.objectid import ObjectId
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import logging  # Import logging để dùng trong create_user

class UserModel(Document):
    """User model for storing authentication data."""
    
    user_id = ObjectIdField(primary_key=True, default=ObjectId, db_field="UserID")
    email = StringField(required=True, unique=True, db_field="Email")
    
    # 👇 [QUAN TRỌNG] Đã có Avatar, nhưng THIẾU Name. Thêm dòng dưới:
    avatar = StringField(db_field="Avatar")
    name = StringField(db_field="Name") # <-- Cần thêm dòng này
    
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
    # 👇 [QUAN TRỌNG] Phải thêm tham số name=None vào hàm này
    def create_user(cls, email: str, plain_password: str, name: str = None):
        """
        Create a new user with hashed password.
        Args:
            email: User's email
            plain_password: Password
            name: User's full name (Optional)
        """
        logger = logging.getLogger(__name__)
        logger.info(f"create_user called with email={email}, name={name}")
        
        hashed = generate_password_hash(
            plain_password,
            method="pbkdf2:sha256",
            salt_length=16
        )
        
        # 👇 Truyền name vào constructor
        user = cls(email=email, hashed_password=hashed, name=name)
        
        logger.info(f"Created user object: {user.email}")
        return user
    
    def check_password(self, plain_password: str) -> bool:
        """
        Verify password against stored hash.
        """
        return check_password_hash(self.hashed_password, plain_password)