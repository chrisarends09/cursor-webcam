from app.extensions import db
from datetime import datetime

class Webcam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    url = db.Column(db.String(512), nullable=False)
    type = db.Column(db.String(32), nullable=False)
    resort = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserWebcam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    webcam_id = db.Column(db.Integer, db.ForeignKey('webcam.id'), nullable=False)
    interval_hours = db.Column(db.Integer)
    last_capture = db.Column(db.DateTime)
    next_capture = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    webcam = db.relationship('Webcam', backref='user_webcams') 