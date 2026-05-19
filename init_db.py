#!/usr/bin/env python
"""
Initialize database with tables
"""

import os
import sys
from pathlib import Path

# Add app directory to path
app_path = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_path)
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.database.models import User, ReferenceSignature, VerificationHistory


def init_db():
    """Initialize database"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Print database info
        print(f"\nDatabase URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
        print(f"Model path: {app.config['MODEL_PATH']}")
        
        return True


def clear_db():
    """Clear database"""
    app = create_app()
    
    with app.app_context():
        response = input("\n⚠️  This will DELETE ALL DATA. Type 'yes' to confirm: ")
        if response.lower() == 'yes':
            print("Clearing database...")
            db.drop_all()
            print("✓ Database cleared!")
            return True
        else:
            print("Cancelled.")
            return False


def reset_db():
    """Reset database"""
    app = create_app()
    
    with app.app_context():
        response = input("\n⚠️  This will RESET the database. Type 'yes' to confirm: ")
        if response.lower() == 'yes':
            print("Resetting database...")
            db.drop_all()
            db.create_all()
            print("✓ Database reset successfully!")
            return True
        else:
            print("Cancelled.")
            return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database initialization utility')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--clear', action='store_true', help='Clear database')
    parser.add_argument('--reset', action='store_true', help='Reset database')
    
    args = parser.parse_args()
    
    if args.init or not any([args.clear, args.reset]):
        init_db()
    elif args.clear:
        clear_db()
    elif args.reset:
        reset_db()
