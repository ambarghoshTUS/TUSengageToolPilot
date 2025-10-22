"""
TUS Engage Tool Pilot - Data Submission Service
Main application entry point for the submission service

This Flask application handles secure file uploads, validation,
and data insertion into PostgreSQL database.

Author: TUS Development Team
Date: October 2025
License: See LICENSE file
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Import application modules
from config.submission_config import Config
from routes.submission_routes import submission_bp
from routes.auth_routes import auth_bp
from database.db_connection import init_db, db_session
from utils.submission_logger import setup_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger('submission_service')


def create_app(config_class=Config):
    """
    Application factory pattern for creating Flask app
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    CORS(app, resources={
        r"/*": {
            "origins": os.getenv("CORS_ORIGINS", "*").split(","),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    jwt = JWTManager(app)
    
    # Initialize database
    init_db()
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(submission_bp, url_prefix='/api/submission')
    
    # Register web interface blueprint
    from routes.web_routes import web_bp
    app.register_blueprint(web_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint for container monitoring"""
        return jsonify({
            'status': 'healthy',
            'service': 'submission_service',
            'version': '1.0.0'
        }), 200
    
    # Root endpoint - redirect to web interface
    @app.route('/api', methods=['GET'])
    def api_info():
        """API information endpoint"""
        return jsonify({
            'service': 'TUS Engage Tool - Data Submission Service',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'submission': '/api/submission',
                'health': '/health'
            },
            'documentation': 'See README.md for API documentation'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Teardown database session
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """Remove database session at the end of request"""
        if db_session:
            db_session.remove()
    
    logger.info("Submission service initialized successfully")
    return app


if __name__ == '__main__':
    """
    Run the application
    Only used for development. In production, use gunicorn or similar WSGI server
    """
    app = create_app()
    
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting submission service on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
