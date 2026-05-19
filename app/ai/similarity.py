# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
from scipy.spatial.distance import cosine, euclidean
import logging

logger = logging.getLogger(__name__)


class SimilarityMetrics:
    """Compute similarity metrics between embeddings"""
    
    @staticmethod
    def cosine_similarity(embedding1, embedding2):
        """
        Compute cosine similarity between two embeddings
        Range: [0, 1] where 1 is identical
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        embedding1 = np.array(embedding1).flatten()
        embedding2 = np.array(embedding2).flatten()
        
        similarity = 1 - cosine(embedding1, embedding2)
        return float(np.clip(similarity, 0, 1))
    
    @staticmethod
    def euclidean_distance(embedding1, embedding2):
        """
        Compute euclidean distance between two embeddings
        Range: [0, inf] where 0 is identical
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Euclidean distance
        """
        embedding1 = np.array(embedding1).flatten()
        embedding2 = np.array(embedding2).flatten()
        
        distance = euclidean(embedding1, embedding2)
        return float(distance)
    
    @staticmethod
    def l2_distance(embedding1, embedding2):
        """L2 norm distance"""
        return np.linalg.norm(np.array(embedding1) - np.array(embedding2))
    
    @staticmethod
    def compute_all_similarities(test_embedding, reference_embeddings):
        """
        Compute similarity between test and all reference embeddings
        
        Args:
            test_embedding: Test signature embedding
            reference_embeddings: List or array of reference embeddings
            
        Returns:
            Dict with similarity metrics
        """
        reference_embeddings = np.array(reference_embeddings)
        
        cosine_sims = []
        euclidean_dists = []
        
        for ref_emb in reference_embeddings:
            cos_sim = SimilarityMetrics.cosine_similarity(test_embedding, ref_emb)
            euc_dist = SimilarityMetrics.euclidean_distance(test_embedding, ref_emb)
            
            cosine_sims.append(cos_sim)
            euclidean_dists.append(euc_dist)
        
        cosine_sims = np.array(cosine_sims)
        euclidean_dists = np.array(euclidean_dists)
        
        return {
            'cosine_similarities': cosine_sims.tolist(),
            'euclidean_distances': euclidean_dists.tolist(),
            'average_similarity': float(np.mean(cosine_sims)),
            'max_similarity': float(np.max(cosine_sims)),
            'min_similarity': float(np.min(cosine_sims)),
            'std_similarity': float(np.std(cosine_sims)),
            'average_distance': float(np.mean(euclidean_dists)),
            'max_distance': float(np.max(euclidean_dists)),
            'min_distance': float(np.min(euclidean_dists)),
            'std_distance': float(np.std(euclidean_dists))
        }


class VerificationThreshold:
    """Manage verification thresholds"""
    
    # Adaptive thresholds
    COSINE_THRESHOLD = 0.82  # Must be >= this value
    DISTANCE_THRESHOLD = 0.25  # Must be <= this value (L2)
    VOTING_THRESHOLD = 0.7  # 70% must vote genuine
    
    @staticmethod
    def is_similar_cosine(similarity, threshold=None):
        """Check if similarity meets threshold (cosine)"""
        if threshold is None:
            threshold = VerificationThreshold.COSINE_THRESHOLD
        return similarity >= threshold
    
    @staticmethod
    def is_similar_distance(distance, threshold=None):
        """Check if distance meets threshold (euclidean)"""
        if threshold is None:
            threshold = VerificationThreshold.DISTANCE_THRESHOLD
        return distance <= threshold


class VerificationEngine:
    """Main verification engine using Siamese network approach"""
    
    def __init__(self, cosine_threshold=0.82, distance_threshold=0.25, voting_threshold=0.7):
        """
        Initialize verification engine
        
        Args:
            cosine_threshold: Threshold for cosine similarity
            distance_threshold: Threshold for euclidean distance
            voting_threshold: Percentage of signatures that must match
        """
        self.cosine_threshold = cosine_threshold
        self.distance_threshold = distance_threshold
        self.voting_threshold = voting_threshold
        logger.info(f"VerificationEngine initialized with thresholds: "
                   f"cosine={cosine_threshold}, distance={distance_threshold}, voting={voting_threshold}")
    
    def verify_signature(self, test_embedding, reference_embeddings, return_details=True):
        """
        Verify if test signature matches reference signatures
        
        Args:
            test_embedding: Embedding of test signature
            reference_embeddings: List of reference signature embeddings
            return_details: Whether to return detailed metrics
            
        Returns:
            Dict with prediction and confidence scores
        """
        if len(reference_embeddings) == 0:
            raise ValueError("No reference embeddings provided")
        
        # Compute all similarities
        metrics = SimilarityMetrics.compute_all_similarities(test_embedding, reference_embeddings)
        
        # Count votes based on cosine similarity
        cosine_votes = [s >= self.cosine_threshold for s in metrics['cosine_similarities']]
        distance_votes = [d <= self.distance_threshold for d in metrics['euclidean_distances']]
        
        # Combined voting (both metrics must agree)
        combined_votes = [c and d for c, d in zip(cosine_votes, distance_votes)]
        
        matched_count = sum(combined_votes)
        total_count = len(combined_votes)
        voting_score = matched_count / total_count if total_count > 0 else 0
        
        # Final prediction
        is_genuine = voting_score >= self.voting_threshold
        prediction = "GENUINE" if is_genuine else "FORGED"
        
        # Confidence calculation
        if is_genuine:
            confidence = voting_score * 100
        else:
            confidence = (1 - voting_score) * 100
        
        result = {
            'prediction': prediction,
            'confidence': float(confidence),
            'matched_signatures': int(matched_count),
            'total_signatures': int(total_count),
            'voting_score': float(voting_score),
            'cosine_threshold': self.cosine_threshold,
            'distance_threshold': self.distance_threshold,
            'voting_threshold': self.voting_threshold
        }
        
        if return_details:
            result.update({
                'average_similarity': metrics['average_similarity'],
                'max_similarity': metrics['max_similarity'],
                'min_similarity': metrics['min_similarity'],
                'std_similarity': metrics['std_similarity'],
                'average_distance': metrics['average_distance'],
                'max_distance': metrics['max_distance'],
                'min_distance': metrics['min_distance'],
                'cosine_similarities': metrics['cosine_similarities'],
                'euclidean_distances': metrics['euclidean_distances']
            })
        
        logger.info(f"Verification result: {prediction} (confidence: {confidence:.1f}%, "
                   f"matched: {matched_count}/{total_count})")
        
        return result
