"""
Configuration settings for the Submission Service
Handles all environment-based configuration

Author: TUS Development Team
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class for submission service"""
    
    # ============================================
    # FLASK CONFIGURATION
    # ============================================
    SECRET_KEY = os.getenv('SESSION_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    TESTING = False
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    # PostgreSQL connection string
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://tusadmin:changeme@database:5432/tus_engage_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG
    
    # Connection pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }
    
    # ============================================
    # JWT CONFIGURATION
    # ============================================
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # ============================================
    # FILE UPLOAD CONFIGURATION
    # ============================================
    # Maximum file size (10MB default)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024))
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = set(
        os.getenv('ALLOWED_EXTENSIONS', 'xlsx,xls,csv,tsv').split(',')
    )
    
    # Upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'templates', 'upload_templates')
    
    # ============================================
    # SECURITY CONFIGURATION
    # ============================================
    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Session security
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ============================================
    # LOGGING CONFIGURATION
    # ============================================
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'submission_service.log')
    
    # ============================================
    # VALIDATION CONFIGURATION
    # ============================================
    # Maximum rows per file upload
    MAX_ROWS_PER_FILE = int(os.getenv('MAX_ROWS_PER_FILE', 10000))
    
    # Required template headers (update based on your needs)
    REQUIRED_HEADERS = [
        'submission_date',
        'department',
        'category'
    ]
    
    # ============================================
    # APPLICATION SETTINGS
    # ============================================
    APP_NAME = 'TUS Engage Tool - Submission Service'
    APP_VERSION = '1.0.0'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    TESTING = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
