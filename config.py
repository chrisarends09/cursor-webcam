import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-please-change'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Scheduler configuration
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "UTC"
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',')
    
    # Sentry configuration
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Discord configuration
    DISCORD_WEBHOOK_URLS = [
        url.strip() 
        for url in os.environ.get('DISCORD_WEBHOOK_URLS', '').split(',') 
        if url.strip()
    ] 