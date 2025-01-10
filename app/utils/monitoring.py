import logging
import traceback
from functools import wraps
from flask import current_app, request, jsonify
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

def setup_monitoring(app):
    """Configure error monitoring"""
    if app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            integrations=[FlaskIntegration()],
            traces_sample_rate=1.0,
            environment=app.config['FLASK_ENV']
        )

def monitor_errors(f):
    """Decorator to monitor API errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log error details
            current_app.logger.error(f"API Error in {f.__name__}: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            
            # Capture in Sentry if configured
            if current_app.config.get('SENTRY_DSN'):
                sentry_sdk.capture_exception(e)
            
            # Return error response
            return jsonify({
                'error': 'Internal server error',
                'message': str(e) if app.debug else 'An unexpected error occurred'
            }), 500
            
    return decorated_function 