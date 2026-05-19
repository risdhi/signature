from extensions import db
from database.models import User, ReferenceSignature, VerificationHistory


def init_database():
    """Initialize database with tables"""
    db.create_all()
    print("Database tables created successfully!")


def clear_database():
    """Clear all data from database (use with caution)"""
    db.drop_all()
    print("Database cleared!")


def reset_database():
    """Reset database - drop and recreate tables"""
    clear_database()
    init_database()
    print("Database reset successfully!")
