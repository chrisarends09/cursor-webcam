# Import blueprints
try:
    from app.routes.auth import auth_bp
except ImportError:
    auth_bp = None
    
try:
    from app.routes.main import main_bp
except ImportError:
    main_bp = None
    
try:
    from app.routes.api import api_bp
except ImportError:
    api_bp = None
    
try:
    from app.routes.webcam import webcam_bp
except ImportError:
    webcam_bp = None

# List available blueprints
__all__ = ['auth_bp', 'main_bp', 'api_bp', 'webcam_bp'] 