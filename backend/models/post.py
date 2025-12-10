"""
Post model for travel guides and tips.
Handles guide/tips data storage with support for future itinerary type.
"""

from mongoengine import (
    Document, StringField, DateTimeField, ObjectIdField,
    ListField, DictField, IntField, BooleanField, EmbeddedDocument,
    EmbeddedDocumentField, FloatField
)
from bson.objectid import ObjectId
from datetime import datetime, timezone


class LocationField(EmbeddedDocument):
    """Embedded document for location data."""
    name = StringField(required=True)
    lat = FloatField()
    lng = FloatField()


class AuthorField(EmbeddedDocument):
    """Embedded document for author data."""
    user_id = ObjectIdField(required=True)
    email = StringField(required=True)


class PostModel(Document):
    """Post model for storing travel guides and tips."""
    
    post_id = ObjectIdField(primary_key=True, default=ObjectId, db_field="_id")
    type = StringField(
        choices=["guide", "itinerary"],
        default="guide",
        required=True,
        db_field="type"
    )
    title = StringField(required=True, min_length=5, max_length=200, db_field="title")
    description = StringField(max_length=501, db_field="description")
    content = StringField(required=True, db_field="content")
    
    # Location information
    location = EmbeddedDocumentField(LocationField, db_field="location")
    
    # Media
    images = ListField(StringField(), default=list, db_field="images")
    
    # Categorization
    tags = ListField(StringField(), default=list, db_field="tags")
    
    # Author information
    author = EmbeddedDocumentField(AuthorField, required=True, db_field="author")
    
    # Engagement metrics
    likes = ListField(StringField(), default=list, db_field="likes")  # Array of user IDs
    views = IntField(default=0, db_field="views")
    
    # Publishing status
    is_published = BooleanField(default=True, db_field="isPublished")
    is_deleted = BooleanField(default=False, db_field="isDeleted")
    
    # Timestamps
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="createdAt")
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc), db_field="updatedAt")
    
    # Future fields for itineraries (Phase 2)
    number_of_days = IntField(db_field="numberOfDays")
    daily_plans = ListField(DictField(), default=list, db_field="dailyPlans")
    
    meta = {
        "db_alias": "PostsDB",
        "collection": "posts",
        "indexes": [
            "type",
            "author.user_id",
            "tags",
            "location.name",
            "-created_at",  # Descending index for newest first
            "-views",  # Descending index for most viewed
        ]
    }
    
    def toggle_like(self, user_id: str) -> int:
        """
        Toggle like for a user. Returns the new like count.
        
        Args:
            user_id: User ID to toggle like for
            
        Returns:
            New like count
        """
        if user_id in self.likes:
            self.likes.remove(user_id)
        else:
            self.likes.append(user_id)
        
        self.updated_at = datetime.now(timezone.utc)
        self.save()
        return len(self.likes)
    
    def increment_views(self) -> int:
        """
        Increment view count. Returns the new view count.
        
        Returns:
            New view count
        """
        self.views += 1
        self.save()
        return self.views
    
    def to_dict(self, include_author_email: bool = False) -> dict:
        """
        Convert post to dictionary for API responses.
        
        Args:
            include_author_email: Whether to include author email
            
        Returns:
            Dictionary representation of post
        """
        data = {
            "id": str(self.post_id),
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "location": {
                "name": self.location.name if self.location else None,
                "lat": self.location.lat if self.location else None,
                "lng": self.location.lng if self.location else None,
            } if self.location else None,
            "images": self.images,
            "tags": self.tags,
            "author": {
                "userId": str(self.author.user_id),
                "email": self.author.email if include_author_email else None
            },
            "likeCount": len(self.likes),
            "views": self.views,
            "isPublished": self.is_published,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # Add itinerary-specific fields if applicable
        if self.type == "itinerary":
            data["numberOfDays"] = self.number_of_days
            data["dailyPlans"] = self.daily_plans
        
        return data
