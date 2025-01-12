from flask import Flask
import logging
import os
from app.extensions import db, migrate, login_manager, mail, scheduler

# Try to import Config, fall back to environment variables if not found
try:
    from config import Config
except ImportError:
    class Config:
        SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
        SQLALCHEMY_TRACK_MODIFICATIONS = False

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p %Z',
        level=logging.INFO
    )
    
    # Initialize extensions with app context
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    
    with app.app_context():
        try:
            # Create database tables if they don't exist
            db.create_all()
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating database tables: {str(e)}")
        
        # Start scheduler if not running
        if not scheduler.running:
            try:
                scheduler.start()
                logging.info("Scheduler started successfully")
            except Exception as e:
                logging.error(f"Error starting scheduler: {str(e)}")
        
        # Register blueprints
        from app.routes import auth_bp, main_bp, api_bp, webcam_bp
        
        if auth_bp:
            app.register_blueprint(auth_bp)
            logging.info("Registered auth blueprint")
        else:
            logging.warning("Auth blueprint not available")
            
        if main_bp:
            app.register_blueprint(main_bp)
            logging.info("Registered main blueprint")
        else:
            logging.warning("Main blueprint not available")
            
        if api_bp:
            app.register_blueprint(api_bp)
            logging.info("Registered API blueprint")
        else:
            logging.warning("API blueprint not available")
            
        if webcam_bp:
            app.register_blueprint(webcam_bp)
            logging.info("Registered webcam blueprint")
        else:
            logging.warning("Webcam blueprint not available")
        
        # Initialize CLI commands
        try:
            from app.cli import init_app as init_cli
            init_cli(app)
            logging.info("CLI commands initialized")
        except ImportError:
            logging.warning("CLI commands not available")
    
    return app 