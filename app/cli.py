import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models.user import User
from app.models.webcam import Webcam
import yaml
import os

def init_app(app):
    app.cli.add_command(init_db_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database with default data."""
    # Create tables
    db.create_all()
    
    # Load webcams from YAML
    webcams_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'webcams.yaml')
    with open(webcams_file, 'r') as f:
        webcams_data = yaml.safe_load(f)
    
    # Add webcams
    for resort, webcams in webcams_data['webcams'].items():
        for webcam_data in webcams:
            # Check if webcam already exists
            existing = Webcam.query.filter_by(name=webcam_data['name']).first()
            if not existing:
                webcam = Webcam(
                    name=webcam_data['name'],
                    description=webcam_data['description'],
                    url=webcam_data['url'],
                    type=webcam_data['type'],
                    resort=resort
                )
                db.session.add(webcam)
                click.echo(f"Added webcam: {webcam.name}")
    
    # Add default admin user
    if not User.query.filter_by(username='chris').first():
        user = User(username='chris', email='admin@example.com')
        user.set_password('chris')
        db.session.add(user)
        click.echo("Added default admin user: chris")
    
    # Commit changes
    db.session.commit()
    click.echo('Database initialized successfully.') 