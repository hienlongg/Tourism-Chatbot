"""
Image Search Engine for Tourism Location Identification

This module provides image-based search functionality to identify Vietnamese tourism
locations from uploaded photos using ResNet embeddings and FAISS similarity search.
"""

import os
import torch
import faiss
import numpy as np
import pickle
import logging
from typing import List, Dict, Optional, Tuple
from PIL import Image
import torchvision.models as models
from torchvision import transforms
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageSearchEngine:
    """
    Image search engine using ResNet embeddings and FAISS index.
    
    This class loads a pre-trained ResNet model and FAISS index at initialization
    and provides methods to search for similar images and retrieve location information.
    """
    
    _instance = None  # Singleton instance
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        index_path: str = "data/vector_db/faiss_tourism_images.index",
        metadata_path: str = "data/vector_db/faiss_tourism_images_metadata.pkl",
        device: Optional[str] = None
    ):
        """
        Initialize the image search engine.
        
        Args:
            index_path: Path to the FAISS index file
            metadata_path: Path to the metadata pickle file
            device: Device to run model on ('cuda', 'cpu', or None for auto-detect)
        """
        # Skip initialization if already initialized (singleton pattern)
        if self._initialized:
            return
            
        logger.info("🚀 Initializing ImageSearchEngine...")
        
        # Set device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        logger.info(f"📱 Using device: {self.device}")
        
        # Load ResNet model
        logger.info("🔧 Loading ResNet18 model...")
        weights = models.ResNet18_Weights.DEFAULT
        self.model = models.resnet18(weights=weights)
        
        # Remove the last layer (fc) to get embeddings (512 dimensions)
        self.model.fc = torch.nn.Identity()
        self.model = self.model.to(self.device)
        self.model.eval()
        logger.info("✅ ResNet18 model loaded successfully")
        
        # Define image transformation pipeline
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Load FAISS index
        logger.info(f"📂 Loading FAISS index from {index_path}...")
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        self.index = faiss.read_index(index_path)
        logger.info(f"✅ FAISS index loaded with {self.index.ntotal} vectors")
        
        # Load metadata
        logger.info(f"📂 Loading metadata from {metadata_path}...")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
        with open(metadata_path, 'rb') as f:
            self.metadata = pickle.load(f)
        logger.info(f"✅ Metadata loaded: {len(self.metadata['image_paths'])} images, {len(self.metadata['class_names'])} classes")
        
        self._initialized = True
        logger.info("🎉 ImageSearchEngine initialization complete!")
    
    def _preprocess_image(self, image_input) -> torch.Tensor:
        """
        Preprocess an image for model input.
        
        Args:
            image_input: Can be:
                - PIL Image object
                - Path to image file (str or Path)
                - numpy array
        
        Returns:
            Preprocessed image tensor
        """
        if isinstance(image_input, (str, Path)):
            image = Image.open(image_input).convert('RGB')
        elif isinstance(image_input, np.ndarray):
            image = Image.fromarray(image_input).convert('RGB')
        elif isinstance(image_input, Image.Image):
            image = image.convert('RGB')
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
        
        return self.transform(image)
    
    def _extract_embedding(self, image_tensor: torch.Tensor) -> np.ndarray:
        """
        Extract embedding from preprocessed image tensor.
        
        Args:
            image_tensor: Preprocessed image tensor
        
        Returns:
            Normalized embedding vector (512-dimensional)
        """
        # Add batch dimension if needed
        if image_tensor.dim() == 3:
            image_tensor = image_tensor.unsqueeze(0)
        
        image_tensor = image_tensor.to(self.device)
        
        with torch.no_grad():
            embedding = self.model(image_tensor).cpu().numpy()
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding)
        
        return embedding
    
    def search_similar_images(
        self,
        image_input,
        k: int = 5
    ) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Search for similar images in the index.
        
        Args:
            image_input: Input image (PIL Image, file path, or numpy array)
            k: Number of similar images to return
        
        Returns:
            Tuple of (distances, indices, results) where results is a list of dicts
            containing image_path, class_name, and distance for each match
        """
        # Preprocess and extract embedding
        image_tensor = self._preprocess_image(image_input)
        query_embedding = self._extract_embedding(image_tensor)
        
        # Search the index
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Build results with metadata
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            result = {
                'image_path': self.metadata['image_paths'][idx],
                'class_name': self.metadata['class_names'][self.metadata['labels'][idx]],
                'label_idx': self.metadata['labels'][idx],
                'distance': float(dist),
                'similarity_score': float(dist)  # Since we use IP on normalized vectors
            }
            results.append(result)
        
        return distances[0], indices[0], results
    
    def identify_location(
        self,
        image_input,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Identify the location from an image and return top matches.
        
        Args:
            image_input: Input image (PIL Image, file path, or numpy array)
            top_k: Number of top matches to return
        
        Returns:
            List of location matches with class names and confidence scores
        """
        logger.info(f"🔍 Identifying location from image (top_k={top_k})...")
        
        _, _, results = self.search_similar_images(image_input, k=top_k)
        
        # Group by location and aggregate scores
        location_scores = {}
        for result in results:
            location = result['class_name']
            score = result['similarity_score']
            
            if location not in location_scores:
                location_scores[location] = {
                    'location_name': location,
                    'total_score': 0,
                    'count': 0,
                    'max_score': 0,
                    'images': []
                }
            
            location_scores[location]['total_score'] += score
            location_scores[location]['count'] += 1
            location_scores[location]['max_score'] = max(location_scores[location]['max_score'], score)
            location_scores[location]['images'].append(result['image_path'])
        
        # Calculate average scores and sort
        aggregated_results = []
        for loc_data in location_scores.values():
            aggregated_results.append({
                'location_name': loc_data['location_name'],
                'confidence': loc_data['max_score'],  # Use max score as confidence
                'avg_similarity': loc_data['total_score'] / loc_data['count'],
                'match_count': loc_data['count'],
                'sample_images': loc_data['images'][:3]  # Keep top 3 sample images
            })
        
        # Sort by confidence (descending)
        aggregated_results.sort(key=lambda x: x['confidence'], reverse=True)
        
        logger.info(f"✅ Found {len(aggregated_results)} unique locations")
        if aggregated_results:
            logger.info(f"🎯 Top match: {aggregated_results[0]['location_name']} (confidence: {aggregated_results[0]['confidence']:.4f})")
        
        return aggregated_results


# Global instance (singleton)
_image_search_engine: Optional[ImageSearchEngine] = None


def get_image_search_engine() -> ImageSearchEngine:
    """
    Get the global ImageSearchEngine instance (singleton).
    
    Returns:
        ImageSearchEngine instance
    """
    global _image_search_engine
    
    if _image_search_engine is None:
        _image_search_engine = ImageSearchEngine()
    
    return _image_search_engine
