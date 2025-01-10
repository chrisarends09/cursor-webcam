from functools import wraps
from flask import request, jsonify, current_app
import redis
from datetime import datetime
import time

redis_client = redis.Redis(host='redis', port=6379, db=0)

class RateLimitExceeded(Exception):
    pass

def handle_rate_limit_exceeded(e):
    response = jsonify({
        'error': 'Too many requests',
        'retry_after': e.retry_after
    })
    response.status_code = 429
    response.headers['Retry-After'] = str(e.retry_after)
    return response

def configure_rate_limiting(app):
    app.register_error_handler(RateLimitExceeded, handle_rate_limit_exceeded)

def rate_limit(limit=60, window=60):
    """
    Rate limiting decorator
    :param limit: Maximum number of requests allowed in the window
    :param window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier (IP or user ID if authenticated)
            identifier = str(g.current_user.id) if hasattr(g, 'current_user') else request.remote_addr
            key = f'rate_limit:{identifier}:{f.__name__}'
            
            try:
                # Get current count and timestamp
                current = int(redis_client.get(key) or 0)
                
                if current >= limit:
                    raise RateLimitExceeded(retry_after=window)
                
                # Increment counter
                pipe = redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                pipe.execute()
                
            except redis.RedisError:
                # If Redis is unavailable, log error and continue
                current_app.logger.error('Redis error in rate limiting')
                return f(*args, **kwargs)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 