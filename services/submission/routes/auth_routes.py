"""
Authentication routes for user login and token management
Handles JWT-based authentication

Author: TUS Development Team
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from flask_bcrypt import Bcrypt

from database.db_connection import db_session
from database.submission_models import User, AuditLog
from utils.auth_decorators import role_required

# Initialize blueprint and bcrypt
auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()
logger = logging.getLogger(__name__)


@auth_bp.route('/register', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def register_user():
    """
    Register a new user (Admin only)
    
    Request JSON:
        username (str): Unique username
        email (str): User email address
        password (str): User password (will be hashed)
        full_name (str): User's full name
        role (str): User role (executive, staff, public, admin)
    
    Returns:
        JSON response with user details or error
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'role']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        existing_user = db_session.query(User).filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Hash password
        password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            full_name=data.get('full_name'),
            role=data['role'],
            created_by=get_jwt_identity()
        )
        
        db_session.add(new_user)
        db_session.commit()
        
        # Log the action
        current_user_id = get_jwt_identity()
        log_entry = AuditLog(
            user_id=current_user_id,
            action='USER_CREATED',
            table_name='users',
            record_id=new_user.user_id,
            new_values={'username': new_user.username, 'role': data['role']},
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db_session.add(log_entry)
        db_session.commit()
        
        logger.info(f"New user registered: {new_user.username}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({'error': 'Failed to register user'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Request JSON:
        username (str): Username or email
        password (str): User password
    
    Returns:
        JSON response with access and refresh tokens
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Find user by username or email
        user = db_session.query(User).filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()
        
        if not user:
            logger.warning(f"Login attempt with invalid username: {data['username']}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.username}")
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Verify password
        if not bcrypt.check_password_hash(user.password_hash, data['password']):
            logger.warning(f"Failed login attempt for user: {user.username}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db_session.commit()
        
        # Create tokens
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                'username': user.username,
                'role': user.role.value if user.role else 'public'
            }
        )
        
        refresh_token = create_refresh_token(identity=str(user.user_id))
        
        # Log successful login
        log_entry = AuditLog(
            user_id=user.user_id,
            action='USER_LOGIN',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db_session.add(log_entry)
        db_session.commit()
        
        logger.info(f"User logged in: {user.username}")
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token
    
    Returns:
        JSON response with new access token
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Get user from database
        user = db_session.query(User).filter_by(user_id=current_user_id).first()
        
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid user'}), 401
        
        # Create new access token
        access_token = create_access_token(
            identity=str(user.user_id),
            additional_claims={
                'username': user.username,
                'role': user.role.value if user.role else 'public'
            }
        )
        
        return jsonify({
            'access_token': access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current user information
    
    Returns:
        JSON response with user details
    """
    try:
        current_user_id = get_jwt_identity()
        
        user = db_session.query(User).filter_by(user_id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return jsonify({'error': 'Failed to get user information'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    
    Request JSON:
        old_password (str): Current password
        new_password (str): New password
    
    Returns:
        JSON response with success message
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('old_password') or not data.get('new_password'):
            return jsonify({'error': 'Missing old or new password'}), 400
        
        user = db_session.query(User).filter_by(user_id=current_user_id).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify old password
        if not bcrypt.check_password_hash(user.password_hash, data['old_password']):
            return jsonify({'error': 'Invalid old password'}), 401
        
        # Update password
        user.password_hash = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
        user.updated_at = datetime.utcnow()
        
        # Log the action
        log_entry = AuditLog(
            user_id=user.user_id,
            action='PASSWORD_CHANGED',
            table_name='users',
            record_id=user.user_id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        db_session.add(log_entry)
        db_session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return jsonify({
            'message': 'Password changed successfully'
        }), 200
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500
