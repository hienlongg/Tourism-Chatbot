"""
Filtered checkpointer wrapper that removes image URLs before saving to database.
Allows the agent to process images without persisting them.
"""

from typing import Any, Dict, Optional


class FilteredCheckpointer:
    """
    Wrapper around a checkpointer that filters out image URLs from messages
    before saving to the database.
    
    The agent still receives messages with images for processing,
    but only text content is persisted.
    """
    
    def __init__(self, base_checkpointer):
        """
        Initialize the filtered checkpointer.
        
        Args:
            base_checkpointer: The underlying checkpointer (PostgresSaver, etc.)
        """
        self.base_checkpointer = base_checkpointer
    
    def _filter_messages(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out image content from messages before saving.
        
        Args:
            values: The state values to be saved
            
        Returns:
            Filtered values with images removed from messages
        """
        if "messages" not in values:
            return values
        
        filtered_values = values.copy()
        messages = values.get("messages", [])
        
        filtered_messages = []
        for message in messages:
            # Create a copy of the message
            if hasattr(message, "content"):
                # For message objects with content attribute
                if isinstance(message.content, list):
                    # Filter to only keep text content
                    text_content = [
                        item for item in message.content
                        if isinstance(item, dict) and item.get("type") == "text"
                        or isinstance(item, str)
                    ]
                    
                    # Only keep message if it has text content
                    if text_content:
                        # Create a new message with filtered content
                        new_message = message.__class__(
                            content=text_content,
                            **{k: v for k, v in message.__dict__.items() 
                               if k != "content"}
                        )
                        filtered_messages.append(new_message)
                else:
                    # Text content - keep as is
                    filtered_messages.append(message)
            else:
                # Keep messages without content attribute
                filtered_messages.append(message)
        
        filtered_values["messages"] = filtered_messages
        return filtered_values
    
    def put(
        self,
        config: Dict[str, Any],
        values: Dict[str, Any],
        metadata: Dict[str, Any],
        *args,
        **kwargs
    ) -> None:
        """
        Save checkpoint with filtered messages.
        
        Args:
            config: The configuration for the checkpoint
            values: The values to save (will be filtered)
            metadata: Metadata about the checkpoint
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        # Filter the values before saving
        filtered_values = self._filter_messages(values)
        
        # Save using the base checkpointer with all provided arguments
        self.base_checkpointer.put(config, filtered_values, metadata, *args, **kwargs)
    
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a checkpoint from the database.
        
        Args:
            config: The configuration for the checkpoint
            
        Returns:
            The checkpoint data or None
        """
        return self.base_checkpointer.get(config)
    
    def get_tuple(self, config: Dict[str, Any]):
        """
        Retrieve a checkpoint tuple from the database.
        
        Args:
            config: The configuration for the checkpoint
            
        Returns:
            The checkpoint tuple or None
        """
        if hasattr(self.base_checkpointer, "get_tuple"):
            return self.base_checkpointer.get_tuple(config)
        return None
    
    def list(self, config: Dict[str, Any], **kwargs):
        """
        List checkpoints.
        
        Args:
            config: The configuration for listing checkpoints
            **kwargs: Additional arguments
            
        Yields:
            Checkpoint tuples
        """
        if hasattr(self.base_checkpointer, "list"):
            yield from self.base_checkpointer.list(config, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """
        Forward any unhandled attributes to the base checkpointer.
        """
        return getattr(self.base_checkpointer, name)
