import os
import json
# pyrefly: ignore [missing-import]
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Layer
try:
    # pyrefly: ignore [missing-import]
    from tensorflow.keras.preprocessing import image
except ImportError:
    # pyrefly: ignore [missing-import]
    from keras.preprocessing import image

import logging

logger = logging.getLogger(__name__)


class L1Distance(Layer):
    """
    Custom layer for computing L1 (Manhattan) distance between two input tensors
    """
    
    def __init__(self, **kwargs):
        super(L1Distance, self).__init__(**kwargs)
    
    def call(self, inputs, **kwargs):
        """
        Compute L1 distance between two input tensors
        """
        if isinstance(inputs, (list, tuple)) and len(inputs) == 2:
            x1, x2 = inputs[0], inputs[1]
        else:
            raise ValueError(f"Expected list/tuple of 2 tensors, got {inputs}")
        return tf.abs(x1 - x2)
    
    def compute_output_shape(self, input_shapes):
        return input_shapes[0]
    
    def get_config(self):
        return super().get_config()


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
        Load pre-trained Siamese model and extract single-input embedding sub-model.
        """
        if self._model is not None:
            logger.info("Model already loaded, using cached instance")
            return self._model
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        custom_objects = {'L1Distance': L1Distance}
        original_model = None
        
        # --- Attempt 1: Load .h5 with standard Keras ---
        logger.info(f"Loading model from {model_path}")
        try:
            from tensorflow.keras.models import load_model as tf_load_model
            original_model = tf_load_model(model_path, custom_objects=custom_objects)
            logger.info(f"Loaded with tf.keras. Input: {original_model.input_shape}, Output: {original_model.output_shape}")
        except Exception as e1:
            logger.warning(f"tf.keras load failed: {e1}")
        
        # --- Attempt 2: Try .keras file if .h5 failed ---
        if original_model is None:
            keras_path = model_path.replace('.h5', '.keras')
            if os.path.exists(keras_path):
                try:
                    import keras as standalone_keras
                    original_model = standalone_keras.models.load_model(
                        keras_path, custom_objects=custom_objects
                    )
                    logger.info(f"Loaded with standalone keras from .keras file")
                except Exception as e2:
                    logger.warning(f"Standalone keras load also failed: {e2}")
        
        # --- Attempt 3: Build architecture + load weights ---
        if original_model is None:
            logger.warning("All load attempts failed. Building architecture and loading weights...")
            original_model = self._build_siamese_model()
            for path in [model_path, model_path.replace('.h5', '.keras')]:
                if os.path.exists(path):
                    try:
                        original_model.load_weights(path, by_name=False, skip_mismatch=True)
                        logger.info(f"Weights loaded from {path}")
                        break
                    except Exception as ew:
                        logger.warning(f"Could not load weights from {path}: {ew}")
        
        # Extract single-input embedding sub-model
        embedding_model = self._extract_embedding_model(original_model, embedding_dim)
        
        self._model = embedding_model
        logger.info(f"Embedding model ready. Input: {embedding_model.input_shape}, Output: {embedding_model.output_shape}")
        return self._model
    
    def _extract_embedding_model(self, original_model, embedding_dim=128):
        """
        Extract embedding model from Siamese model.
        For Siamese (dual-input) models, extract the shared Sequential sub-model directly.

        Args:
            original_model: Original model (Siamese or embedding)
            embedding_dim: Expected embedding dimension

        Returns:
            Single-input embedding model
        """
        from tensorflow.keras.models import Model as KerasModel

        # Check if model is Siamese (2 inputs) or single-input embedding model
        if isinstance(original_model.input, list):
            logger.info("Detected Siamese model with 2 inputs, extracting shared feature extractor...")

            # Strategy 1: Find the Sequential sub-layer and use it directly as model
            for layer in original_model.layers:
                if hasattr(layer, 'layers') and ('sequential' in layer.name.lower() or 'feature' in layer.name.lower()):
                    logger.info(f"Using Sequential sub-model directly as embedding model: {layer.name}")
                    # The Sequential layer itself IS a model with single input
                    return layer

            # Strategy 2: Build new Model from first input to layer before L1Distance
            for i, layer in enumerate(original_model.layers):
                if 'l1_distance' in layer.name.lower() and i > 0:
                    prev_layer = original_model.layers[i - 1]
                    logger.info(f"Extracting from layer before L1Distance: {prev_layer.name}")
                    # Get output of prev_layer when fed first input
                    inp = original_model.input[0]
                    out = prev_layer.output[0] if isinstance(prev_layer.output, list) else prev_layer.output
                    embedding_model = KerasModel(inputs=inp, outputs=out, name='embedding_model')
                    return embedding_model

            # Fallback: rebuild a basic embedding model with same architecture
            logger.warning("Could not extract encoder; rebuilding default embedding model.")
            return self._build_siamese_model().layers[3]  # get the sequential sub-model

        else:
            # Already single-input model
            if len(original_model.output_shape) == 2 and original_model.output_shape[-1] <= embedding_dim:
                logger.info("Model is already a single-input embedding model")
                return original_model
            elif len(original_model.output_shape) == 2 and original_model.output_shape[-1] > embedding_dim:
                logger.info(f"Removing output layer (output: {original_model.output_shape[-1]})")
                embedding_model = KerasModel(
                    inputs=original_model.input,
                    outputs=original_model.layers[-2].output,
                    name='embedding_model'
                )
                return embedding_model
            else:
                return original_model
    
    def _build_siamese_model(self):
        """Build Siamese model from scratch"""
        logger.info("Building Siamese model from scratch...")
        
        from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense
        from tensorflow.keras.models import Model as KerasModel, Sequential
        
        # Input layers for both images
        img1 = Input((105, 105, 1), name='img1')
        img2 = Input((105, 105, 1), name='img2')
        
        # Shared feature extractor
        feature_extractor = Sequential([
            Conv2D(64, (3, 3), activation='relu', input_shape=(105, 105, 1)),
            MaxPooling2D((2, 2)),
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            Flatten(),
            Dense(128, activation='relu')
        ], name='feature_extractor')
        
        # Process both images through shared network
        feat1 = feature_extractor(img1)
        feat2 = feature_extractor(img2)
        
        # L1 distance layer
        distance = L1Distance(name='l1_distance')([feat1, feat2])
        
        # Output layer
        output = Dense(1, activation='sigmoid', name='output')(distance)
        
        # Create model
        model = KerasModel(inputs=[img1, img2], outputs=output, name='siamese_network')
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        
        logger.info("Siamese model built successfully")
        return model
    
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
