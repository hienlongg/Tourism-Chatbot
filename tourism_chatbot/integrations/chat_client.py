"""
Chat API Client (Template)

Client for communicating with Chat API on Hugging Face Spaces.
Implement when Chat API is ready.
"""

import logging

logger = logging.getLogger(__name__)


class ChatClient:
    """Client for Chat API on Hugging Face Spaces (template)."""
    
    def __init__(self, api_url: str, timeout: int = 30):
        """
        Initialize chat client.
        
        Args:
            api_url: Hugging Face Space URL
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"🔗 ChatClient initialized (template)")
    
    def generate_response(self, query: str):
        """
        Generate chat response.
        
        Args:
            query: User query
            
        Returns:
            Chat response
        """
        raise NotImplementedError("Chat API not yet implemented")
