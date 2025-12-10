"""
Validation utilities for post data.
"""

import re
from typing import Tuple
import bleach


def validate_title(title: str) -> Tuple[bool, str]:
    """
    Validate post title.
    
    Args:
        title: Post title to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Title is required"
    
    title = title.strip()
    
    if len(title) < 5:
        return False, "Title must be at least 5 characters long"
    
    if len(title) > 200:
        return False, "Title must not exceed 200 characters"
    
    return True, ""


def validate_content(content: str, post_type: str = "guide") -> Tuple[bool, str]:
    """
    Validate post content.
    
    Args:
        content: Post content to validate
        post_type: Type of post (guide or itinerary)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Content is required"
    
    content = content.strip()
    
    # Guides should have substantial content
    if post_type == "guide" and len(content) < 50:
        return False, "Guide content must be at least 50 characters long"
    
    if len(content) > 50000:
        return False, "Content must not exceed 50,000 characters"
    
    return True, ""


def validate_tags(tags: list) -> Tuple[bool, str]:
    """
    Validate post tags.
    
    Args:
        tags: List of tags to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not tags:
        return True, ""  # Tags are optional
    
    if not isinstance(tags, list):
        return False, "Tags must be a list"
    
    if len(tags) > 10:
        return False, "Maximum 10 tags allowed"
    
    # Validate each tag
    tag_pattern = re.compile(r'^[a-zA-Z0-9\s\-_]+$')
    for tag in tags:
        if not isinstance(tag, str):
            return False, "All tags must be strings"
        
        tag = tag.strip()
        if len(tag) < 2:
            return False, "Each tag must be at least 2 characters long"
        
        if len(tag) > 30:
            return False, "Each tag must not exceed 30 characters"
        
        if not tag_pattern.match(tag):
            return False, f"Tag '{tag}' contains invalid characters. Use only letters, numbers, spaces, hyphens, and underscores"
    
    return True, ""


def validate_location(location: dict) -> Tuple[bool, str]:
    """
    Validate location data.
    
    Args:
        location: Location dictionary with name, lat, lng
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not location:
        return False, "Location is required"
    
    if not isinstance(location, dict):
        return False, "Location must be an object"
    
    # Name is required
    if "name" not in location or not location["name"]:
        return False, "Location name is required"
    
    name = location["name"].strip()
    if len(name) < 2:
        return False, "Location name must be at least 2 characters long"
    
    # Coordinates are optional but must be valid if provided
    if "lat" in location or "lng" in location:
        try:
            lat = float(location.get("lat", 0))
            lng = float(location.get("lng", 0))
            
            if lat < -90 or lat > 90:
                return False, "Latitude must be between -90 and 90"
            
            if lng < -180 or lng > 180:
                return False, "Longitude must be between -180 and 180"
        except (ValueError, TypeError):
            return False, "Invalid coordinates format"
    
    return True, ""


def validate_images(images: list) -> Tuple[bool, str]:
    """
    Validate image URLs.
    
    Args:
        images: List of image URLs
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not images:
        return True, ""  # Images are optional
    
    if not isinstance(images, list):
        return False, "Images must be a list"
    
    if len(images) > 10:
        return False, "Maximum 10 images allowed"
    
    # Validate each URL
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    for img_url in images:
        if not isinstance(img_url, str):
            return False, "All image URLs must be strings"
        
        if not url_pattern.match(img_url):
            return False, f"Invalid image URL: {img_url}"
    
    return True, ""


def sanitize_html(content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    Allows only safe HTML tags.
    
    Args:
        content: HTML content to sanitize
        
    Returns:
        Sanitized HTML content
    """
    # Allow only safe tags
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'a', 'blockquote', 'code', 'pre'
    ]
    
    allowed_attributes = {
        'a': ['href', 'title'],
    }
    
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )


def validate_post_data(data: dict, post_type: str = "guide") -> Tuple[bool, str]:
    """
    Validate complete post data.
    
    Args:
        data: Post data dictionary
        post_type: Type of post (guide or itinerary)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate title
    is_valid, error = validate_title(data.get("title", ""))
    if not is_valid:
        return False, error
    
    # Validate content
    is_valid, error = validate_content(data.get("content", ""), post_type)
    if not is_valid:
        return False, error
    
    # Validate location
    is_valid, error = validate_location(data.get("location"))
    if not is_valid:
        return False, error
    
    # Validate tags (optional)
    if "tags" in data:
        is_valid, error = validate_tags(data.get("tags"))
        if not is_valid:
            return False, error
    
    # Validate images (optional)
    if "images" in data:
        is_valid, error = validate_images(data.get("images"))
        if not is_valid:
            return False, error
    
    return True, ""
