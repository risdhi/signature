import json
import logging
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime

logger = logging.getLogger(__name__)


def format_response(success=True, message="", data=None, status_code=200):
    """
    Format JSON response
    
    Args:
        success: Whether operation was successful
        message: Message to include
        data: Data to include
        status_code: HTTP status code
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': success,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return response, status_code


def error_response(message, status_code=400, details=None):
    """Format error response"""
    response = {
        'success': False,
        'error': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['details'] = details
    
    return response, status_code


def check_content_type(required_type='application/json'):
    """Decorator to check content type"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != 'GET':
                if request.content_type and required_type not in request.content_type:
                    return error_response(
                        f"Content-Type must be {required_type}",
                        status_code=415
                    )
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_data(*fields):
    """Decorator to require specific data fields"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.json:
                return error_response("Request must be JSON", status_code=400)
            
            data = request.json
            missing_fields = [field for field in fields if field not in data]
            
            if missing_fields:
                return error_response(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    status_code=400
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def format_bytes(bytes_size):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"


def safe_float(value, default=0.0):
    """Safely convert to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default
