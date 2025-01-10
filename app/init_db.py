from app import create_app, db
from app.models.user import User
from app.models.webcam import Webcam
import yaml

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default user if it doesn't exist
        if not User.query.filter_by(username='chris').first():
            user = User(username='chris', email='chris@example.com')
            user.set_password('chris')
            db.session.add(user)
        
        # Load webcams from YAML
        with open('webcams.yaml', 'r') as f:
            webcams_data = yaml.safe_load(f)
            
        # Add webcams if they don't exist
        for resort, webcams in webcams_data['webcams'].items():
            for webcam_data in webcams:
                if not Webcam.query.filter_by(name=webcam_data['name']).first():
                    webcam = Webcam(
                        name=webcam_data['name'],
                        description=webcam_data['description'],
                        url=webcam_data['url'],
                        type=webcam_data['type'],
                        resort=resort
                    )
                    db.session.add(webcam)
        
        db.session.commit()

if __name__ == '__main__':
    init_db() 