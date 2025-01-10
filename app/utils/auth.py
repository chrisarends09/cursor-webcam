from functools import wraps
from flask import request, jsonify
from flask_login import current_user
import jwt
from datetime import datetime, timedelta
from app import db
from app.models.user import User

def generate_api_token(user):
    """Generate a JWT token for API access"""
    payload = {
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def require_api_token(f):
    """Decorator to require API token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Missing API token'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'message': 'Invalid API token'}), 401
                
            # Store user in flask.g for access in the view
            g.current_user = user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Expired API token'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid API token'}), 401
            
        return f(*args, **kwargs)
    return decorated 