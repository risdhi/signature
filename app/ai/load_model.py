import os
import json
import zipfile
import io
# pyrefly: ignore [missing-import]
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
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
    """Custom layer for computing L1 (Manhattan) distance between two input tensors"""
    
    def __init__(self, **kwargs):
        super(L1Distance, self).__init__(**kwargs)
    
    def call(self, inputs, **kwargs):
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
    _model_type = None  # 'custom' or 'mobilenet'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_model_type(cls):
        """Return the type of model currently loaded ('custom' or 'mobilenet')"""
        return cls._model_type
    
    def load_model(self, model_path, embedding_dim=128):
        """
        Load pre-trained Siamese model and extract single-input embedding sub-model.
        Falls back to MobileNetV2 if the custom model is degenerate.
        """
        if self._model is not None:
            logger.info(f"Model already loaded ({self.__class__._model_type}), using cached instance")
            return self._model
        
        if not os.path.exists(model_path):
            logger.warning(f"Model file not found: {model_path}. Will use MobileNetV2 fallback.")
        
        # Determine h5 and keras paths
        if model_path.endswith('.keras'):
            keras_path = model_path
            h5_path = model_path.replace('.keras', '.h5')
        else:
            h5_path = model_path
            keras_path = model_path.replace('.h5', '.keras')

        custom_objects = {'L1Distance': L1Distance}
        original_model = None
        
        # --- Attempt 1: Load full model with tf.keras from .h5 ---
        if os.path.exists(h5_path):
            try:
                from tensorflow.keras.models import load_model as tf_load_model
                original_model = tf_load_model(h5_path, custom_objects=custom_objects)
                logger.info(f"Loaded with tf.keras from .h5")
            except Exception as e1:
                logger.warning(f"tf.keras .h5 load failed: {e1}")

        # --- Attempt 2: Standalone Keras from .keras file ---
        if original_model is None and os.path.exists(keras_path):
            try:
                import keras as standalone_keras
                original_model = standalone_keras.models.load_model(
                    keras_path, custom_objects=custom_objects
                )
                logger.info("Loaded with standalone keras from .keras file")
            except Exception as e2:
                logger.warning(f"Standalone keras load failed: {e2}")

        # --- Attempt 3: Build architecture + inject trained weights ---
        embedding_model = None
        if original_model is None:
            logger.warning("Full model load failed. Building architecture and injecting trained weights...")
            original_model = self._build_siamese_model()
            loaded_weights = False

            # Strategy A: Load from inner model.weights.h5 inside .keras zip (Keras 3 format)
            if not loaded_weights and os.path.exists(keras_path):
                loaded_weights = self._load_weights_from_keras_zip(original_model, keras_path)

            # Strategy B: Load from outer .h5 file (TF2/Keras2 format)
            if not loaded_weights and os.path.exists(h5_path):
                loaded_weights = self._load_weights_from_h5(original_model, h5_path)

            if loaded_weights:
                logger.info("Trained weights injected into architecture.")
            else:
                logger.warning("Could not load trained weights.")

        # Extract single-input embedding sub-model from Siamese model
        if original_model is not None:
            embedding_model = self._extract_embedding_model(original_model, embedding_dim)

        # --- Degeneracy Check ---
        # If embeddings for two different random inputs are virtually identical,
        # the custom model is degenerate (collapsed embeddings). Fall back to MobileNetV2.
        if embedding_model is not None and self._is_degenerate(embedding_model):
            logger.warning(
                "Custom model produces degenerate (near-identical) embeddings for all inputs. "
                "Falling back to MobileNetV2 pretrained on ImageNet."
            )
            embedding_model = None

        # --- Fallback: MobileNetV2 ---
        if embedding_model is None:
            logger.info("Using MobileNetV2 as embedding backbone.")
            embedding_model = self._build_mobilenet_model(embedding_dim)
            self.__class__._model_type = 'mobilenet'
        else:
            self.__class__._model_type = 'custom'

        self._model = embedding_model
        logger.info(
            f"Embedding model ready [{self.__class__._model_type}]. "
            f"Input: {embedding_model.input_shape}, Output: {embedding_model.output_shape}"
        )
        return self._model

    # ------------------------------------------------------------------
    # Degeneracy Detection
    # ------------------------------------------------------------------

    def _is_degenerate(self, model, threshold=0.98, n_tests=5):
        """
        Test if the model produces near-identical embeddings for different random inputs.
        If cosine similarity > threshold for all pairs, the model is considered degenerate.
        """
        try:
            input_shape = model.input_shape[1:]  # e.g. (105, 105, 1)
            similarities = []
            for _ in range(n_tests):
                img_a = np.random.rand(1, *input_shape).astype(np.float32)
                img_b = np.random.rand(1, *input_shape).astype(np.float32)
                emb_a = model.predict(img_a, verbose=0).squeeze()
                emb_b = model.predict(img_b, verbose=0).squeeze()
                norm_a = np.linalg.norm(emb_a)
                norm_b = np.linalg.norm(emb_b)
                if norm_a < 1e-6 or norm_b < 1e-6:
                    return True  # Zero embeddings → degenerate
                emb_a = emb_a / norm_a
                emb_b = emb_b / norm_b
                cos_sim = float(np.dot(emb_a, emb_b))
                similarities.append(cos_sim)
            avg_sim = np.mean(similarities)
            logger.info(f"Degeneracy check: avg cosine similarity = {avg_sim:.6f} (threshold={threshold})")
            return avg_sim > threshold
        except Exception as e:
            logger.error(f"Degeneracy check failed: {e}")
            return False

    # ------------------------------------------------------------------
    # MobileNetV2 Fallback Backbone
    # ------------------------------------------------------------------

    def _build_mobilenet_model(self, embedding_dim=128):
        """
        Build an embedding model using MobileNetV2 pretrained on ImageNet.
        Input: (128, 128, 3) RGB images, values in [0, 255] — preprocessing done internally.
        Output: L2-normalized embedding of dimension `embedding_dim`.
        """
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        from tensorflow.keras.layers import (
            Dense, GlobalAveragePooling2D, Input, Lambda
        )
        from tensorflow.keras.models import Model as KerasModel

        logger.info("Building MobileNetV2 embedding model (128x128 RGB, ImageNet weights)...")

        inp = Input(shape=(128, 128, 3), name='signature_input')

        # MobileNetV2 preprocessing: scales pixel values from [0,255] to [-1,1]
        x = Lambda(preprocess_input, name='mobilenet_preprocess')(inp)

        base = MobileNetV2(
            input_shape=(128, 128, 3),
            include_top=False,
            weights='imagenet',
            alpha=1.0
        )
        base.trainable = False  # Use pretrained features as-is
        x = base(x, training=False)

        x = GlobalAveragePooling2D(name='gap')(x)
        
        if embedding_dim != 1280:
            dense_layer = Dense(embedding_dim, activation=None, use_bias=False, name='embedding_dense')
            x = dense_layer(x)
            
        # L2 normalize so cosine similarity = dot product
        x = Lambda(lambda v: tf.math.l2_normalize(v, axis=1), name='l2_norm')(x)

        model = KerasModel(inputs=inp, outputs=x, name='mobilenet_embedding')
        
        if embedding_dim != 1280:
            # Set weights deterministically using a fixed random seed
            np.random.seed(42)
            projection_matrix = np.random.normal(size=(1280, embedding_dim)).astype(np.float32)
            q, _ = np.linalg.qr(projection_matrix)
            dense_layer.set_weights([q])
            
        logger.info(f"MobileNetV2 model built. Input: {model.input_shape}, Output: {model.output_shape}")
        return model

    # ------------------------------------------------------------------
    # Weight loading helpers for the custom Siamese model
    # ------------------------------------------------------------------

    def _load_weights_from_keras_zip(self, model, keras_path):
        """Load weights positionally from inner model.weights.h5 inside .keras zip (Keras 3 format)."""
        logger.info(f"Loading weights from Keras 3 zip: {keras_path}")
        try:
            import h5py
            with zipfile.ZipFile(keras_path, 'r') as z:
                if 'model.weights.h5' not in z.namelist():
                    logger.warning("model.weights.h5 not found inside .keras zip")
                    return False
                
                weights_bytes = z.read('model.weights.h5')
                with h5py.File(io.BytesIO(weights_bytes), 'r') as f:
                    seq_path = 'layers/sequential/layers'
                    if seq_path not in f:
                        logger.warning(f"Path '{seq_path}' not found in weights file")
                        return False
                    
                    seq_group = f[seq_path]
                    # Only layers with actual weights (vars > 0)
                    weight_layer_names = sorted(
                        [k for k in seq_group.keys()
                         if 'vars' in seq_group[k] and len(seq_group[k]['vars']) > 0],
                        key=lambda x: x.replace('conv2d', 'a_conv2d')
                    )

                    seq_layer = model.get_layer('sequential_1')
                    trainable_layers = [l for l in seq_layer.layers if len(l.get_weights()) > 0]

                    loaded_count = 0
                    for wl_name, layer in zip(weight_layer_names, trainable_layers):
                        try:
                            vars_group = seq_group[wl_name]['vars']
                            kernel = np.array(vars_group['0'])
                            bias = np.array(vars_group['1'])
                            layer.set_weights([kernel, bias])
                            logger.info(f"Loaded: zip[{wl_name}] → model[{layer.name}] kernel={kernel.shape}")
                            loaded_count += 1
                        except Exception as e:
                            logger.error(f"Failed {wl_name} → {layer.name}: {e}")

                    # Also load the output dense layer
                    try:
                        dense_vars = f['layers/dense/vars']
                        dense_layer = model.get_layer('dense_3')
                        dense_layer.set_weights([np.array(dense_vars['0']), np.array(dense_vars['1'])])
                        loaded_count += 1
                    except Exception as e:
                        logger.warning(f"Could not load dense_3: {e}")

                    logger.info(f"Keras zip: loaded {loaded_count}/{len(trainable_layers)+1} layer weight sets")
                    return loaded_count >= len(trainable_layers)

        except Exception as e:
            logger.error(f"_load_weights_from_keras_zip failed: {e}")
            return False

    def _load_weights_from_h5(self, model, h5_path):
        """Load weights by name from TF2/Keras2-format .h5 file."""
        logger.info(f"Loading weights from legacy .h5: {h5_path}")
        try:
            import h5py
            with h5py.File(h5_path, 'r') as f:
                seq_layer = model.get_layer('sequential_1')
                trainable_layers = [l for l in seq_layer.layers if len(l.get_weights()) > 0]

                loaded_count = 0
                for layer in trainable_layers:
                    path = f'model_weights/sequential_1/sequential_1/{layer.name}'
                    try:
                        kernel = np.array(f[f'{path}/kernel'])
                        bias = np.array(f[f'{path}/bias'])
                        layer.set_weights([kernel, bias])
                        logger.info(f"Loaded h5 weights for {layer.name}: kernel={kernel.shape}")
                        loaded_count += 1
                    except KeyError:
                        logger.warning(f"Path not found in h5: {path}")
                    except Exception as e:
                        logger.error(f"Error loading {layer.name}: {e}")

                try:
                    dense_layer = model.get_layer('dense_3')
                    kernel = np.array(f['model_weights/dense_3/dense_3/kernel'])
                    bias = np.array(f['model_weights/dense_3/dense_3/bias'])
                    dense_layer.set_weights([kernel, bias])
                    loaded_count += 1
                except Exception as e:
                    logger.warning(f"Could not load dense_3 from h5: {e}")

                return loaded_count >= len(trainable_layers)
        except Exception as e:
            logger.error(f"_load_weights_from_h5 failed: {e}")
            return False

    def _extract_embedding_model(self, original_model, embedding_dim=128):
        """Extract single-input embedding sub-model from Siamese dual-input model."""
        from tensorflow.keras.models import Model as KerasModel

        if isinstance(original_model.input, list):
            # Strategy 1: Return the shared Sequential sub-layer directly
            for layer in original_model.layers:
                if hasattr(layer, 'layers') and (
                    'sequential' in layer.name.lower() or 'feature' in layer.name.lower()
                ):
                    logger.info(f"Using Sequential sub-model as embedding model: {layer.name}")
                    return layer

            # Strategy 2: Build Model from first input to layer before L1Distance
            for i, layer in enumerate(original_model.layers):
                if 'l1_distance' in layer.name.lower() and i > 0:
                    prev_layer = original_model.layers[i - 1]
                    inp = original_model.input[0]
                    out = (prev_layer.output[0]
                           if isinstance(prev_layer.output, list)
                           else prev_layer.output)
                    return KerasModel(inputs=inp, outputs=out, name='embedding_model')

            logger.warning("Could not extract encoder from Siamese model.")
            return None
        else:
            return original_model

    def _build_siamese_model(self):
        """Build Siamese model from scratch matching layer names in the .h5 weight file."""
        from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense
        from tensorflow.keras.models import Model as KerasModel, Sequential

        img1 = Input((105, 105, 1), name='img1')
        img2 = Input((105, 105, 1), name='img2')

        feature_extractor = Sequential([
            Conv2D(64, (3, 3), activation='relu', input_shape=(105, 105, 1), name='conv2d_2'),
            MaxPooling2D((2, 2)),
            Conv2D(128, (3, 3), activation='relu', name='conv2d_3'),
            MaxPooling2D((2, 2)),
            Conv2D(128, (3, 3), activation='relu', name='conv2d_4'),
            MaxPooling2D((2, 2)),
            Flatten(),
            Dense(128, activation='relu', name='dense_2')
        ], name='sequential_1')

        feat1 = feature_extractor(img1)
        feat2 = feature_extractor(img2)
        distance = L1Distance(name='l1_distance')([feat1, feat2])
        output = Dense(1, activation='sigmoid', name='dense_3')(distance)

        model = KerasModel(inputs=[img1, img2], outputs=output, name='siamese_network')
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def get_model(self):
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first")
        return self._model

    def get_input_shape(self):
        if self._model is None:
            raise RuntimeError("Model not loaded")
        return self._model.input_shape[1:]

    def get_output_shape(self):
        if self._model is None:
            raise RuntimeError("Model not loaded")
        return self._model.output_shape[-1]

    def reset(self):
        self._model = None
        self.__class__._model_type = None


def load_pretrained_model(model_path, embedding_dim=128):
    """Load pretrained model for embedding extraction."""
    loader = ModelLoader.get_instance()
    return loader.load_model(model_path, embedding_dim)


def get_embedding_model():
    """Get the loaded embedding model."""
    loader = ModelLoader.get_instance()
    return loader.get_model()
