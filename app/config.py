import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from the root directory
root_dir = os.path.dirname(os.path.dirname(__file__))
dotenv_path = os.path.join(root_dir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

class Config:
    """Base configuration"""
    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:root@localhost:3306/signature_verification'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'processed')
    RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'results')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    
    # AI Model
    MODEL_PATH = os.getenv('MODEL_PATH', os.path.join(
        os.path.dirname(__file__), '..', 'model', 'siamese_signature_model.h5'
    ))
    
    # Siamese Network Configuration
    EMBEDDING_DIM = 128
    # Thresholds for MobileNetV2 L2-normalized embeddings.
    # For unit vectors: euclidean_dist = sqrt(2*(1-cos_sim))
    # Adjust SIMILARITY_THRESHOLD and DISTANCE_THRESHOLD together.
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.75))
    DISTANCE_THRESHOLD = float(os.getenv('DISTANCE_THRESHOLD', 0.72))
    
    # Image Preprocessing — 128x128 for MobileNetV2, 105x105 for custom Siamese
    IMG_SIZE = (128, 128)
    IMG_CHANNELS = 3      # RGB for MobileNetV2
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Logging
    LOG_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'logs')
    
    # Verification
    MIN_REFERENCE_SIGNATURES = 2
    MAX_REFERENCE_SIGNATURES = 5
    VOTING_THRESHOLD = float(os.getenv('VOTING_THRESHOLD', 0.6))  # 60% must match for GENUINE


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
