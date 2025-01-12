#!/usr/bin/env python3
import os
import sys
from flask_migrate import init, migrate, upgrade
from app import create_app, db

def setup_database():
    """Set up the database and migrations"""
    app = create_app()
    
    with app.app_context():
        # Check if migrations directory exists
        if not os.path.exists('migrations'):
            print("Initializing migrations directory...")
            init()
        
        print("Creating migration...")
        migrate(message="Initial database setup")
        
        print("Applying migration...")
        upgrade()
        
        print("Database setup complete!")

if __name__ == '__main__':
    setup_database() 