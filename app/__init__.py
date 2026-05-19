from flask import Flask
from app.config import config
from app.extensions import db, migrate, setup_logging
import os


def create_app(config_name='development'):
    """Application factory"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Create upload folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    setup_logging(app)
    
    # Register blueprints
    from app.routes.web import web_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Shell context for flask shell
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db}
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(error):
        return {'error': 'Page not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app
