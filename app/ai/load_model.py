import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.preprocessing import image
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load and prepare pre-trained model for embedding extraction"""
    
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_model(self, model_path, embedding_dim=128):
        """
        Load pre-trained model and convert to embedding model
        
        Args:
            model_path: Path to .h5 or .keras model file
            embedding_dim: Expected embedding dimension
            
        Returns:
            Embedding model
        """
        if self._model is not None:
            logger.info("Model already loaded, using cached instance")
            return self._model
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            # Load original model
            logger.info(f"Loading model from {model_path}")
            original_model = load_model(model_path)
            logger.info(f"Model loaded successfully. Input shape: {original_model.input_shape}")
            logger.info(f"Model output shape: {original_model.output_shape}")
            
            # Check if we need to remove classification layer
            if len(original_model.output_shape) == 2 and original_model.output_shape[-1] > embedding_dim:
                # Remove last classification layer
                logger.info(f"Removing classification layer (output: {original_model.output_shape[-1]})")
                # Use the layer before last
                embedding_model = Model(
                    inputs=original_model.input,
                    outputs=original_model.layers[-2].output
                )
                logger.info(f"Embedding model created. Output shape: {embedding_model.output_shape}")
            else:
                # Use as-is if already appropriate dimension
                embedding_model = original_model
                logger.info("Using original model as embedding extractor")
            
            # Verify embedding dimension
            if embedding_model.output_shape[-1] < embedding_dim:
                logger.warning(f"Output dimension {embedding_model.output_shape[-1]} is less than expected {embedding_dim}")
            
            self._model = embedding_model
            logger.info(f"Model ready. Embedding dimension: {embedding_model.output_shape[-1]}")
            return self._model
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def get_model(self):
        """Get loaded model"""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first")
        return self._model
    
    def get_input_shape(self):
        """Get input shape of model"""
        if self._model is None:
            raise RuntimeError("Model not loaded")
        return self._model.input_shape[1:]  # Exclude batch dimension
    
    def get_output_shape(self):
        """Get embedding output shape"""
        if self._model is None:
            raise RuntimeError("Model not loaded")
        return self._model.output_shape[-1]
    
    def reset(self):
        """Reset singleton instance"""
        self._model = None


def load_pretrained_model(model_path, embedding_dim=128):
    """
    Load pretrained model for embedding extraction
    
    Args:
        model_path: Path to .h5 or .keras model
        embedding_dim: Expected embedding dimension
        
    Returns:
        Loaded embedding model
    """
    loader = ModelLoader.get_instance()
    return loader.load_model(model_path, embedding_dim)


def get_embedding_model():
    """Get the loaded embedding model"""
    loader = ModelLoader.get_instance()
    return loader.get_model()
