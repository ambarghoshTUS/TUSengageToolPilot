"""
Database connection and session management
Handles SQLAlchemy database connections with PostgreSQL

Author: TUS Development Team
"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

# Setup logger
logger = logging.getLogger(__name__)

# Create base class for declarative models
Base = declarative_base()

# Database session (will be initialized in init_db)
db_session = None
engine = None


def get_database_url():
    """
    Construct database URL from environment variables
    
    Returns:
        str: PostgreSQL database connection URL
    """
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        # Construct from individual components
        db_user = os.getenv('DB_USER', 'tusadmin')
        db_password = os.getenv('DB_PASSWORD', 'changeme')
        db_host = os.getenv('DB_HOST', 'database')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'tus_engage_db')
        
        db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    return db_url


def init_db():
    """
    Initialize database connection and create session factory
    This function should be called when the application starts
    """
    global db_session, engine
    
    database_url = get_database_url()
    
    try:
        # Create engine with connection pooling
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
        )
        
        # Test connection
        with engine.connect() as conn:
            logger.info("Database connection established successfully")
        
        # Create session factory
        session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # Create scoped session
        db_session = scoped_session(session_factory)
        
        # Bind base to session query property
        Base.query = db_session.query_property()
        
        logger.info("Database session initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def get_db():
    """
    Get database session for dependency injection
    
    Yields:
        Session: SQLAlchemy database session
    """
    if db_session is None:
        init_db()
    
    session = db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def close_db():
    """
    Close database connection
    Should be called when application shuts down
    """
    global db_session, engine
    
    if db_session:
        db_session.remove()
        logger.info("Database session closed")
    
    if engine:
        engine.dispose()
        logger.info("Database engine disposed")


# Event listeners for connection management
@event.listens_for(engine, "connect", insert=True) if engine else lambda: None
def receive_connect(dbapi_conn, connection_record):
    """Set connection parameters on connect"""
    logger.debug("Database connection opened")


@event.listens_for(engine, "checkin", insert=True) if engine else lambda: None
def receive_checkin(dbapi_conn, connection_record):
    """Handle connection checkin"""
    logger.debug("Database connection returned to pool")
