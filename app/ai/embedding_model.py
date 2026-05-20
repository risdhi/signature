# pyrefly: ignore [missing-import]
import numpy as np
import tensorflow as tf
# pyrefly: ignore [missing-import]
from tensorflow.keras.preprocessing import image
import logging
from app.ai.load_model import get_embedding_model, ModelLoader

logger = logging.getLogger(__name__)


class EmbeddingExtractor:
    """Extract embeddings from signature images using pre-trained model"""
    
    def __init__(self):
        self.model = None
        self.input_shape = None    # (H, W) tuple
        self.n_channels = 1        # 1 = grayscale, 3 = RGB
    
    def initialize(self, input_shape):
        """
        Initialize embedding extractor.
        input_shape: (H, W) tuple — the spatial size expected by the model.
        The number of channels is inferred from the loaded model.
        """
        self.model = get_embedding_model()
        self.input_shape = input_shape

        # Detect model channel count from its input shape
        model_input = self.model.input_shape  # e.g. (None, 128, 128, 3) or (None, 105, 105, 1)
        if len(model_input) == 4:
            self.n_channels = model_input[-1]
        else:
            self.n_channels = 1

        # Override spatial size from the actual model input if different from config
        if len(model_input) == 4 and model_input[1] is not None:
            self.input_shape = (model_input[1], model_input[2])

        model_type = ModelLoader.get_model_type() or 'unknown'
        logger.info(
            f"EmbeddingExtractor initialized — model_type={model_type}, "
            f"input_shape={self.input_shape}, channels={self.n_channels}"
        )
    
    def preprocess_image(self, image_path):
        """
        Load and preprocess image for model input.
        - MobileNetV2 model: 128×128 RGB, raw pixel values [0,255]
          (preprocess_input is applied inside the model via Lambda layer)
        - Custom Siamese model: 105×105 grayscale, normalized to [0,1]
        """
        try:
            if self.n_channels == 3:
                # RGB — MobileNetV2 expects values in [0, 255]; Lambda inside model handles the rest
                color_mode = 'rgb'
                img = image.load_img(image_path, target_size=self.input_shape, color_mode=color_mode)
                img_array = image.img_to_array(img)          # shape (H, W, 3), dtype float32
                img_array = np.expand_dims(img_array, axis=0)  # (1, H, W, 3)
                # Do NOT normalize here — MobileNetV2's Lambda layer does it to [-1, 1]
            else:
                # Grayscale — original custom Siamese model
                color_mode = 'grayscale'
                img = image.load_img(image_path, target_size=self.input_shape, color_mode=color_mode)
                img_array = image.img_to_array(img)
                if img_array.shape[-1] != 1:
                    img_array = np.expand_dims(img_array[..., 0], axis=-1)
                img_array = np.expand_dims(img_array, axis=0)  # (1, H, W, 1)
                img_array = img_array / 255.0                  # normalize to [0, 1]

            logger.debug(
                f"Image preprocessed: path={image_path}, "
                f"shape={img_array.shape}, dtype={img_array.dtype}"
            )
            return img_array

        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            raise
    
    def extract_embedding(self, image_path):
        """
        Extract and return a normalized embedding vector for the given image.
        
        Args:
            image_path: Path to preprocessed signature image
            
        Returns:
            L2-normalized embedding vector (numpy array, shape [embedding_dim])
        """
        if self.model is None:
            raise RuntimeError("EmbeddingExtractor not initialized. Call initialize() first.")
        
        try:
            img_array = self.preprocess_image(image_path)
            embedding = self.model.predict(img_array, verbose=0)
            embedding = embedding.squeeze()

            # L2-normalize (MobileNetV2 model already applies l2_norm layer,
            # but we normalize here too for safety / custom model compatibility)
            norm = np.linalg.norm(embedding)
            if norm > 1e-8:
                embedding = embedding / norm

            logger.debug(
                f"Embedding extracted: shape={embedding.shape}, norm={np.linalg.norm(embedding):.4f}"
            )
            return embedding

        except Exception as e:
            logger.error(f"Error extracting embedding: {str(e)}")
            raise
    
    def extract_batch_embeddings(self, image_paths):
        """
        Extract embeddings from multiple images.
        
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
    """Get or create embedding extractor singleton."""
    global _embedding_extractor
    
    if _embedding_extractor is None:
        _embedding_extractor = EmbeddingExtractor()
        if input_shape:
            _embedding_extractor.initialize(input_shape)
    
    return _embedding_extractor


def extract_embedding(image_path):
    """Convenience function: extract embedding from image."""
    extractor = get_embedding_extractor()
    return extractor.extract_embedding(image_path)
