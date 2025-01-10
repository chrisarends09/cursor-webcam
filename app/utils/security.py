from functools import wraps
from flask import make_response, request, current_app
from datetime import datetime, timedelta

def add_security_headers(response):
    """Add security headers to response"""
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; img-src 'self' data:; font-src 'self' cdn.jsdelivr.net"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def cors_preflight(methods=['GET', 'POST', 'PUT', 'DELETE']):
    """Handle CORS preflight requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'OPTIONS':
                response = make_response()
                response.headers['Access-Control-Allow-Methods'] = ', '.join(methods)
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                response.headers['Access-Control-Max-Age'] = '3600'
                return response
            return f(*args, **kwargs)
        return decorated_function
    return decorator 