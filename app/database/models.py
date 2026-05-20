from datetime import datetime
from app.extensions import db
import json
import os


class User(db.Model):
    """User model for signature registration"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(200))
    password_hash = db.Column(db.String(255), nullable=True)
    is_registered = db.Column(db.Boolean, default=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reference_signatures = db.relationship('ReferenceSignature', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    verification_history = db.relationship('VerificationHistory', foreign_keys='[VerificationHistory.user_id]', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_registered': self.is_registered,
            'registration_date': self.registration_date.isoformat(),
            'signature_count': self.reference_signatures.count()
        }


class ReferenceSignature(db.Model):
    """Reference signature model for genuine signatures"""
    __tablename__ = 'reference_signatures'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    image_path = db.Column(db.String(255), nullable=False)
    processed_image_path = db.Column(db.String(255))
    embedding_path = db.Column(db.String(255), nullable=False)
    
    # Embedding stored as JSON
    embedding = db.Column(db.JSON, nullable=False)
    embedding_shape = db.Column(db.String(50))  # e.g., (128,)
    
    file_size = db.Column(db.Integer)  # bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ReferenceSignature user_id={self.user_id} id={self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'image_path': self.image_path,
            'embedding_shape': self.embedding_shape,
            'upload_date': self.upload_date.isoformat(),
            'file_size': self.file_size
        }


class VerificationHistory(db.Model):
    """Verification history model"""
    __tablename__ = 'verification_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Who performed the verification (may differ from user_id/target)
    verified_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Description/context provided by the verifier
    description = db.Column(db.String(500), nullable=True)
    
    test_image_path = db.Column(db.String(255), nullable=False)
    processed_image_path = db.Column(db.String(255))
    result_image_path = db.Column(db.String(255))
    
    prediction = db.Column(db.String(20), nullable=False)  # GENUINE or FORGED
    confidence = db.Column(db.Float)  # 0-100
    
    average_similarity = db.Column(db.Float)
    max_similarity = db.Column(db.Float)
    min_similarity = db.Column(db.Float)
    cosine_similarity = db.Column(db.Float)
    euclidean_distance = db.Column(db.Float)
    
    # Additional metrics
    matched_signatures = db.Column(db.Integer)  # How many reference signatures matched
    total_signatures = db.Column(db.Integer)  # Total reference signatures compared
    voting_score = db.Column(db.Float)  # Percentage that voted GENUINE
    
    # Comparison details
    similarity_scores = db.Column(db.JSON)  # List of similarity with each reference
    
    verification_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processing_time = db.Column(db.Float)  # seconds
    
    # Relationship to the user who performed the verification
    verified_by = db.relationship('User', foreign_keys=[verified_by_user_id], backref='verifications_performed')
    
    def __repr__(self):
        return f'<VerificationHistory id={self.id} prediction={self.prediction}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'verified_by_user_id': self.verified_by_user_id,
            'description': self.description,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'average_similarity': self.average_similarity,
            'max_similarity': self.max_similarity,
            'min_similarity': self.min_similarity,
            'cosine_similarity': self.cosine_similarity,
            'euclidean_distance': self.euclidean_distance,
            'matched_signatures': self.matched_signatures,
            'total_signatures': self.total_signatures,
            'voting_score': self.voting_score,
            'similarity_scores': self.similarity_scores,
            'verification_date': self.verification_date.isoformat(),
            'processing_time': self.processing_time
        }
