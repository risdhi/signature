import os
import json
import time
# pyrefly: ignore [missing-import]
import numpy as np
from pathlib import Path
import logging
from datetime import datetime

from app.preprocessing.preprocess import preprocess_signature
from app.ai.embedding_model import get_embedding_extractor, extract_embedding
from app.ai.similarity import VerificationEngine
from app.ai.load_model import get_embedding_model

logger = logging.getLogger(__name__)


class SiasesePredictorWrapper:
    """
    Wrapper for complete Siamese Network verification pipeline
    """
    
    def __init__(self, config):
        """
        Initialize predictor
        
        Args:
            config: Flask config object
        """
        self.config = config
        self.embedding_extractor = None
        self.verification_engine = None
        self.is_initialized = False
    
    def initialize(self):
        """Initialize model and engines"""
        if self.is_initialized:
            logger.info("Predictor already initialized")
            return
        
        try:
            logger.info("Initializing SiamesePredictorWrapper...")
            
            # Load pretrained model FIRST
            from app.ai.load_model import load_pretrained_model
            model_path = self.config.get('MODEL_PATH', 'model/siamese_signature_model.h5')
            embedding_dim = self.config.get('EMBEDDING_DIM', 128)
            load_pretrained_model(model_path, embedding_dim)
            
            # Initialize embedding extractor
            self.embedding_extractor = get_embedding_extractor(self.config.get('IMG_SIZE', (299, 299)))
            
            # Initialize verification engine with thresholds from config
            self.verification_engine = VerificationEngine(
                cosine_threshold=self.config.get('SIMILARITY_THRESHOLD', 0.82),
                distance_threshold=self.config.get('DISTANCE_THRESHOLD', 0.25),
                voting_threshold=self.config.get('VOTING_THRESHOLD', 0.7)
            )
            
            self.is_initialized = True
            logger.info("SiamesePredictorWrapper initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing predictor: {str(e)}")
            raise
    
    def preprocess_and_extract_embedding(self, image_path, processed_output_path=None):
        """
        Preprocess image and extract embedding
        
        Args:
            image_path: Path to original image
            processed_output_path: Optional path to save processed image
            
        Returns:
            Tuple of (embedding, processed_image_path)
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Preprocess
            processed_image = preprocess_signature(image_path, processed_output_path)
            
            # Extract embedding
            embedding = self.embedding_extractor.extract_embedding(processed_output_path)
            
            return embedding, processed_output_path
            
        except Exception as e:
            logger.error(f"Error in preprocessing/embedding extraction: {str(e)}")
            raise
    
    def verify_signature(self, test_embedding, reference_embeddings):
        """
        Verify signature using Siamese network
        
        Args:
            test_embedding: Embedding of test signature
            reference_embeddings: List of reference embeddings
            
        Returns:
            Verification result dict
        """
        if not self.is_initialized:
            self.initialize()
        
        if len(reference_embeddings) == 0:
            raise ValueError("No reference embeddings provided")
        
        try:
            # Run verification
            result = self.verification_engine.verify_signature(test_embedding, reference_embeddings)
            return result
            
        except Exception as e:
            logger.error(f"Error in verification: {str(e)}")
            raise
    
    def register_signatures(self, user_id, image_paths, db_session, upload_folder):
        """
        Register reference signatures for a user
        
        Args:
            user_id: User ID
            image_paths: List of image file paths
            db_session: Database session
            upload_folder: Base upload folder
            
        Returns:
            List of created ReferenceSignature objects
        """
        if not self.is_initialized:
            self.initialize()
        
        from app.database.models import ReferenceSignature
        
        reference_signatures = []
        
        try:
            for idx, image_path in enumerate(image_paths):
                # Create output paths
                processed_path = os.path.join(upload_folder, 'processed', 
                                             f'user_{user_id}_ref_{idx}_processed.png')
                embedding_path = os.path.join(upload_folder, 'embeddings',
                                             f'user_{user_id}_ref_{idx}_embedding.npy')
                
                # Ensure directories exist
                Path(processed_path).parent.mkdir(parents=True, exist_ok=True)
                Path(embedding_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Preprocess and extract embedding
                embedding, _ = self.preprocess_and_extract_embedding(image_path, processed_path)
                
                # Save embedding
                np.save(embedding_path, embedding)
                
                # Create database record
                ref_sig = ReferenceSignature(
                    user_id=user_id,
                    image_path=str(image_path),
                    processed_image_path=processed_path,
                    embedding_path=embedding_path,
                    embedding=embedding.tolist(),
                    embedding_shape=str(embedding.shape),
                    file_size=os.path.getsize(image_path)
                )
                
                db_session.add(ref_sig)
                reference_signatures.append(ref_sig)
                
                logger.info(f"Registered reference signature {idx} for user {user_id}")
            
            db_session.commit()
            logger.info(f"Successfully registered {len(reference_signatures)} signatures for user {user_id}")
            
            return reference_signatures
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error registering signatures: {str(e)}")
            raise
    
    def verify_user_signature(self, user_id, test_image_path, db_session, config, timestamp=None, verified_by_user_id=None, description=None):
        """
        Complete verification pipeline for a user
        
        Args:
            user_id: User ID
            test_image_path: Path to test signature image
            db_session: Database session
            config: Flask config
            timestamp: Optional timestamp for results
            verified_by_user_id: Optional ID of the user performing the verification
            description: Optional description/context
            
        Returns:
            Verification result with all metrics
        """
        if not self.is_initialized:
            self.initialize()
        
        from app.database.models import VerificationHistory, User
        
        start_time = time.time()
        
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Get user and reference signatures
            user = db_session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            reference_sigs = user.reference_signatures.all()
            if len(reference_sigs) == 0:
                raise ValueError(f"No reference signatures found for user {user_id}")
            
            logger.info(f"Verifying signature for user {user_id} against {len(reference_sigs)} reference signatures")
            
            # Create output paths
            processed_path = os.path.join(config.get('PROCESSED_FOLDER', 'static/processed'),
                                         f'user_{user_id}_test_{timestamp.timestamp()}_processed.png')
            result_path = os.path.join(config.get('RESULTS_FOLDER', 'static/results'),
                                      f'user_{user_id}_result_{timestamp.timestamp()}.json')
            
            # Preprocess test image and extract embedding
            test_embedding, _ = self.preprocess_and_extract_embedding(test_image_path, processed_path)
            
            # Load reference embeddings
            reference_embeddings = [np.array(sig.embedding) for sig in reference_sigs]
            
            # Verify
            verification_result = self.verify_signature(test_embedding, reference_embeddings)
            
            # Add additional info
            verification_result.update({
                'user_id': user_id,
                'test_image_path': test_image_path,
                'processed_image_path': processed_path,
                'result_image_path': result_path,
                'verification_date': timestamp.isoformat(),
                'processing_time': time.time() - start_time
            })
            
            # Save result
            Path(result_path).parent.mkdir(parents=True, exist_ok=True)
            with open(result_path, 'w') as f:
                # Convert numpy arrays to lists for JSON serialization
                result_json = {k: v.tolist() if isinstance(v, np.ndarray) else v 
                              for k, v in verification_result.items()}
                json.dump(result_json, f, indent=2)
            
            # Create database record
            history = VerificationHistory(
                user_id=user_id,
                verified_by_user_id=verified_by_user_id,
                description=description,
                test_image_path=str(test_image_path),
                processed_image_path=processed_path,
                result_image_path=result_path,
                prediction=verification_result['prediction'],
                confidence=verification_result['confidence'],
                average_similarity=verification_result.get('average_similarity'),
                max_similarity=verification_result.get('max_similarity'),
                min_similarity=verification_result.get('min_similarity'),
                cosine_similarity=verification_result.get('average_similarity'),
                euclidean_distance=verification_result.get('average_distance'),
                matched_signatures=verification_result['matched_signatures'],
                total_signatures=verification_result['total_signatures'],
                voting_score=verification_result['voting_score'],
                similarity_scores=verification_result.get('cosine_similarities'),
                verification_date=timestamp,
                processing_time=verification_result['processing_time']
            )
            
            db_session.add(history)
            db_session.commit()
            
            logger.info(f"Verification complete: {verification_result['prediction']} "
                       f"(confidence: {verification_result['confidence']:.1f}%)")
            
            return verification_result
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error in verification pipeline: {str(e)}")
            raise


# Singleton instance
_predictor = None


def get_predictor(config):
    """Get or create predictor instance"""
    global _predictor
    
    if _predictor is None:
        _predictor = SiasesePredictorWrapper(config)
        _predictor.initialize()
    
    return _predictor
