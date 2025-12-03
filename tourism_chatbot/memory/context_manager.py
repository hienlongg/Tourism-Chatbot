"""
User context manager for tracking visited locations and preferences
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class UserContextManager:
    """
    Manages user-specific context for personalized recommendations.
    
    Tracks:
    - Visited locations
    - Revisit preferences
    - User preferences (future)
    
    Example:
        >>> context = UserContextManager(user_id="user123")
        >>> context.add_visited("bai_bien_my_khe")
        >>> context.add_visited("hoi_an_ancient_town")
        >>> context.get_visited()
        ['bai_bien_my_khe', 'hoi_an_ancient_town']
    """
    
    def __init__(self, user_id: str):
        """
        Initialize context manager for a user.
        
        Args:
            user_id: Unique user identifier
        """
        self.user_id = user_id
        self.visited_ids: List[str] = []
        self.allow_revisit: bool = False
        self.preferences: Dict = {}
        
        logger.debug(f"UserContextManager initialized for user: {user_id}")
    
    def add_visited(self, location_id: str) -> None:
        """
        Mark a location as visited.
        
        Args:
            location_id: Location identifier (loc_id)
        """
        if location_id not in self.visited_ids:
            self.visited_ids.append(location_id)
            logger.info(f"User {self.user_id} visited: {location_id}")
        else:
            logger.debug(f"Location {location_id} already in visited list")
    
    def add_visited_multiple(self, location_ids: List[str]) -> None:
        """
        Mark multiple locations as visited.
        
        Args:
            location_ids: List of location identifiers
        """
        for loc_id in location_ids:
            self.add_visited(loc_id)
    
    def remove_visited(self, location_id: str) -> bool:
        """
        Remove a location from visited list.
        
        Args:
            location_id: Location identifier to remove
        
        Returns:
            bool: True if removed, False if not found
        """
        if location_id in self.visited_ids:
            self.visited_ids.remove(location_id)
            logger.info(f"Removed {location_id} from visited list for user {self.user_id}")
            return True
        return False
    
    def get_visited(self) -> List[str]:
        """
        Get list of visited location IDs.
        
        Returns:
            List of visited location identifiers
        """
        return self.visited_ids.copy()
    
    def has_visited(self, location_id: str) -> bool:
        """
        Check if user has visited a location.
        
        Args:
            location_id: Location identifier to check
        
        Returns:
            bool: True if visited, False otherwise
        """
        return location_id in self.visited_ids
    
    def set_allow_revisit(self, allow: bool) -> None:
        """
        Set whether to allow recommending visited locations.
        
        Args:
            allow: True to allow revisits, False to exclude visited places
        """
        self.allow_revisit = allow
        logger.info(f"User {self.user_id} revisit preference: {allow}")
    
    def get_allow_revisit(self) -> bool:
        """
        Get revisit preference.
        
        Returns:
            bool: True if revisits allowed, False otherwise
        """
        return self.allow_revisit
    
    def set_preference(self, key: str, value: any) -> None:
        """
        Set a user preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        self.preferences[key] = value
        logger.debug(f"User {self.user_id} preference set: {key}={value}")
    
    def get_preference(self, key: str, default: any = None) -> any:
        """
        Get a user preference.
        
        Args:
            key: Preference key
            default: Default value if key not found
        
        Returns:
            Preference value or default
        """
        return self.preferences.get(key, default)
    
    def clear_visited(self) -> None:
        """Clear all visited locations."""
        count = len(self.visited_ids)
        self.visited_ids.clear()
        logger.info(f"Cleared {count} visited locations for user {self.user_id}")
    
    def get_stats(self) -> Dict:
        """
        Get user context statistics.
        
        Returns:
            dict: Statistics about user context
        """
        return {
            "user_id": self.user_id,
            "visited_count": len(self.visited_ids),
            "allow_revisit": self.allow_revisit,
            "preferences_count": len(self.preferences)
        }
    
    def to_dict(self) -> Dict:
        """
        Convert context to dictionary for serialization.
        
        Returns:
            dict: Serializable context data
        """
        return {
            "user_id": self.user_id,
            "visited_ids": self.visited_ids,
            "allow_revisit": self.allow_revisit,
            "preferences": self.preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserContextManager':
        """
        Create UserContextManager from dictionary.
        
        Args:
            data: Dictionary with context data
        
        Returns:
            UserContextManager instance
        """
        context = cls(user_id=data["user_id"])
        context.visited_ids = data.get("visited_ids", [])
        context.allow_revisit = data.get("allow_revisit", False)
        context.preferences = data.get("preferences", {})
        return context
