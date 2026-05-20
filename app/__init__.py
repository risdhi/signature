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
        
    # Seed hardcoded admin user
    try:
        with app.app_context():
            from app.database.models import User
            admin = User.query.filter_by(username='admins').first()
            if not admin:
                admin = User(
                    username='admins',
                    email='admin@signature.ai',
                    full_name='System Admin',
                    is_registered=True
                )
                admin.set_password('123456')
                db.session.add(admin)
                db.session.commit()
            else:
                admin.set_password('123456')
                admin.is_registered = True
                db.session.commit()
    except Exception as e:
        app.logger.warning(f"Could not seed admin user (tables might not exist yet): {e}")
    
    return app
