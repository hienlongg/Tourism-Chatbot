"""
Image API Client (Template)

Client for communicating with Image API on Hugging Face Spaces.
Implement when Image API is ready.
"""

import logging

logger = logging.getLogger(__name__)


class ImageClient:
    """Client for Image API on Hugging Face Spaces (template)."""
    
    def __init__(self, api_url: str, timeout: int = 30):
        """
        Initialize image client.
        
        Args:
            api_url: Hugging Face Space URL
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        logger.info(f"🔗 ImageClient initialized (template)")
    
    def process_image(self, image_path: str):
        """
        Process image.
        
        Args:
            image_path: Path to image
            
        Returns:
            Processed image
        """
        raise NotImplementedError("Image API not yet implemented")
