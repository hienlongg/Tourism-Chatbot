"""
Base class for Gradio-based APIs deployed on Hugging Face Spaces.

Provides common functionality and patterns for all microservices.
"""

import gradio as gr
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class BaseGradioAPI:
    """
    Base class for Gradio APIs on Hugging Face Spaces.
    
    Provides:
    - Common initialization patterns
    - Error handling
    - Health check endpoint
    - Logging setup
    """
    
    def __init__(self, title: str, description: str):
        """
        Initialize the API.
        
        Args:
            title: API title for web UI
            description: API description
        """
        self.title = title
        self.description = description
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging with consistent format."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check endpoint.
        
        Returns:
            Dict with status information
        """
        return {
            "status": "healthy",
            "service": self.title,
            "version": "1.0"
        }
    
    def handle_error(self, error: Exception) -> str:
        """
        Common error handling.
        
        Args:
            error: Exception to handle
            
        Returns:
            User-friendly error message
        """
        self.logger.error(f"Error: {str(error)}", exc_info=True)
        return f"Error: {str(error)}"
    
    def create_demo(self) -> gr.Blocks:
        """
        Create Gradio demo. Should be overridden in subclasses.
        
        Returns:
            gr.Blocks instance
        """
        raise NotImplementedError("Subclasses must implement create_demo()")
