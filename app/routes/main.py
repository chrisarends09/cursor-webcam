from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.webcam import Webcam, UserWebcam

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    user_webcams = UserWebcam.query.filter_by(user_id=current_user.id).all()
    available_webcams = Webcam.query.all()
    return render_template('main/index.html', 
                         title='Home',
                         user_webcams=user_webcams,
                         available_webcams=available_webcams) 