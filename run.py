#!/usr/bin/env python
"""
Main entry point for Signature Verification Application
"""

import os
import sys
from pathlib import Path

# Add app directory to path
app_path = os.path.join(os.path.dirname(__file__), 'app')
sys.path.insert(0, app_path)
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db, setup_logging

def main():
    """Run the application"""
    # Get environment
    env = os.getenv('FLASK_ENV', 'development')
    
    # Create app
    app = create_app(env)
    
    # Setup logging
    setup_logging(app)
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)
    
    # Create embeddings directory
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'embeddings'), exist_ok=True)
    
    app.logger.info(f"Starting application in {env} mode...")
    
    # Run server
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = env == 'development'
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
