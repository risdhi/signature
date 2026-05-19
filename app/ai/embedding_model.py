# pyrefly: ignore [missing-import]
import numpy as np
import tensorflow as tf
# pyrefly: ignore [missing-import]
from tensorflow.keras.preprocessing import image
import logging
from app.ai.load_model import get_embedding_model

logger = logging.getLogger(__name__)


class EmbeddingExtractor:
    """Extract embeddings from signature images using pre-trained model"""
    
    def __init__(self):
        self.model = None
        self.input_shape = None
    
    def initialize(self, input_shape):
        """Initialize embedding extractor"""
        self.model = get_embedding_model()
        self.input_shape = input_shape
        logger.info(f"EmbeddingExtractor initialized with input shape: {input_shape}")
    
    def preprocess_image(self, image_path):
        """
        Preprocess image for model input (105x105 grayscale)
        Args:
            image_path: Path to image file
        Returns:
            Preprocessed image array
        """
        try:
            # Load image as grayscale and resize
            img = image.load_img(image_path, target_size=self.input_shape, color_mode='grayscale')
            img_array = image.img_to_array(img)
            # Ensure shape is (105, 105, 1)
            if img_array.shape[-1] != 1:
                img_array = np.expand_dims(img_array[..., 0], axis=-1)
            img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
            img_array = img_array / 255.0  # Normalize
            logger.debug(f"Image preprocessed: {img_array.shape}")
            return img_array
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            raise
    
    def extract_embedding(self, image_path):
        """
        Extract embedding from image
        
        Args:
            image_path: Path to preprocessed signature image
            
        Returns:
            Embedding vector (numpy array)
        """
        if self.model is None:
            raise RuntimeError("EmbeddingExtractor not initialized")
        
        try:
            # Preprocess image
            img_array = self.preprocess_image(image_path)
            
            # Extract embedding
            embedding = self.model.predict(img_array, verbose=0)
            embedding = embedding.squeeze()
            
            # Normalize embedding
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            
            logger.debug(f"Embedding extracted: shape {embedding.shape}, norm {np.linalg.norm(embedding):.4f}")
            return embedding
        except Exception as e:
            logger.error(f"Error extracting embedding: {str(e)}")
            raise
    
    def extract_batch_embeddings(self, image_paths):
        """
        Extract embeddings from multiple images
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Array of embeddings (N, embedding_dim)
        """
        embeddings = []
        for image_path in image_paths:
            embedding = self.extract_embedding(image_path)
            embeddings.append(embedding)
        
        return np.array(embeddings)


# Singleton instance
_embedding_extractor = None


def get_embedding_extractor(input_shape=None):
    """Get or create embedding extractor instance"""
    global _embedding_extractor
    
    if _embedding_extractor is None:
        _embedding_extractor = EmbeddingExtractor()
        if input_shape:
            _embedding_extractor.initialize(input_shape)
    
    return _embedding_extractor


def extract_embedding(image_path):
    """Extract embedding from image"""
    extractor = get_embedding_extractor()
    return extractor.extract_embedding(image_path)
