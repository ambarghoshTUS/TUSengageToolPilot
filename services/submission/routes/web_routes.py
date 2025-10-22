"""
Web interface routes for TUS Data Submission Portal
Serves HTML pages for user-friendly file upload interface

Author: TUS Development Team
"""

import logging
from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from database.db_connection import db_session
from database.submission_models import User

# Initialize blueprint and logger
web_bp = Blueprint('web', __name__)
logger = logging.getLogger(__name__)


@web_bp.route('/')
def index():
    """
    Main landing page - redirect to upload interface or login
    """
    # Check if user has a valid session or token
    auth_token = request.cookies.get('auth_token') or session.get('auth_token')
    
    if auth_token:
        # If authenticated, go to upload page
        return redirect(url_for('web.upload_page'))
    else:
        # If not authenticated, go to login page
        return redirect(url_for('web.login_page'))


@web_bp.route('/login')
def login_page():
    """
    Login page for web interface
    """
    return render_template('web/login.html')


@web_bp.route('/upload')
def upload_page():
    """
    Main file upload interface
    Requires authentication
    """
    # For now, we'll create a simple demo auth check
    # In production, this should use proper JWT validation
    
    auth_token = request.cookies.get('auth_token') or session.get('auth_token')
    if not auth_token:
        return redirect(url_for('web.login_page'))
    
    # Get user information (demo implementation)
    user_name = session.get('user_name', 'Demo User')
    
    return render_template('web/upload.html', 
                         user_name=user_name,
                         auth_token=auth_token)


@web_bp.route('/uploads')
def uploads_list():
    """
    List all uploads for the current user
    """
    auth_token = request.cookies.get('auth_token') or session.get('auth_token')
    if not auth_token:
        return redirect(url_for('web.login_page'))
    
    user_name = session.get('user_name', 'Demo User')
    
    return render_template('web/uploads_list.html',
                         user_name=user_name,
                         auth_token=auth_token)


@web_bp.route('/login', methods=['POST'])
def do_login():
    """
    Process login form submission
    Simple demo implementation - replace with proper authentication
    """
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Demo authentication - replace with proper validation
    if username and password:
        # For demo purposes, accept any non-empty credentials
        session['auth_token'] = 'demo_jwt_token'
        session['user_name'] = username
        session['user_role'] = 'staff'  # Default role
        
        # Set cookie as well for JavaScript access
        response = redirect(url_for('web.upload_page'))
        response.set_cookie('auth_token', 'demo_jwt_token', max_age=86400)  # 24 hours
        return response
    else:
        return render_template('web/login.html', 
                             error="Please enter both username and password")


@web_bp.route('/logout')
def logout():
    """
    Logout user and clear session
    """
    session.clear()
    response = redirect(url_for('web.login_page'))
    response.delete_cookie('auth_token')
    return response


@web_bp.route('/api/auth/demo-login', methods=['POST'])
def api_demo_login():
    """
    Demo API login endpoint for JavaScript
    Replace with proper JWT authentication
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Demo authentication - in production, validate against database
        if len(username) > 0 and len(password) > 0:
            # Create demo JWT token (replace with proper JWT)
            token = create_access_token(
                identity=username,
                additional_claims={'role': 'staff', 'demo': True}
            )
            
            return jsonify({
                'access_token': token,
                'user': {
                    'username': username,
                    'role': 'staff',
                    'name': username.title()
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        logger.error(f"Demo login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500


@web_bp.route('/health-web')
def health_check_web():
    """
    Health check for web interface
    """
    return jsonify({
        'status': 'healthy',
        'service': 'web_interface',
        'version': '1.0.0'
    }), 200


# Error handlers for web interface
@web_bp.errorhandler(404)
def web_not_found(error):
    """Handle 404 errors for web interface"""
    return render_template('web/error.html', 
                         error_code=404,
                         error_message="Page not found"), 404


@web_bp.errorhandler(500)
def web_internal_error(error):
    """Handle 500 errors for web interface"""
    return render_template('web/error.html',
                         error_code=500,
                         error_message="Internal server error"), 500
