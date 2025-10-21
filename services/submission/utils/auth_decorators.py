"""
Custom authentication decorators for role-based access control

Author: TUS Development Team
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt


def role_required(allowed_roles):
    """
    Decorator to check if user has required role
    
    Args:
        allowed_roles (list): List of roles allowed to access the endpoint
    
    Usage:
        @role_required(['admin', 'executive'])
        def admin_only_endpoint():
            pass
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get('role', 'public')
            
            if user_role not in allowed_roles:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': allowed_roles,
                    'your_role': user_role
                }), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator
