from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.webcam import Webcam, UserWebcam
from app.forms.webcam import WebcamForm
from app.utils.webcam_capture import capture_webcam
from datetime import datetime, timedelta
import logging

webcam_bp = Blueprint('webcam', __name__, url_prefix='/webcam')

@webcam_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = WebcamForm()
    if form.validate_on_submit():
        webcam = Webcam(
            name=form.name.data,
            description=form.description.data,
            url=form.url.data,
            type=form.type.data,
            resort=form.resort.data
        )
        db.session.add(webcam)
        db.session.commit()
        flash('Webcam added successfully!')
        return redirect(url_for('main.index'))
    return render_template('webcam/add.html', title='Add Webcam', form=form)

@webcam_bp.route('/select/<int:webcam_id>', methods=['POST'])
@login_required
def select(webcam_id):
    interval = request.form.get('interval', type=int)
    webcam = Webcam.query.get_or_404(webcam_id)
    
    # Check if user already has this webcam
    user_webcam = UserWebcam.query.filter_by(
        user_id=current_user.id,
        webcam_id=webcam_id
    ).first()
    
    if user_webcam:
        user_webcam.interval_hours = interval
        if interval:
            user_webcam.next_capture = datetime.utcnow() + timedelta(hours=interval)
    else:
        user_webcam = UserWebcam(
            user_id=current_user.id,
            webcam_id=webcam_id,
            interval_hours=interval,
            next_capture=datetime.utcnow() + timedelta(hours=interval) if interval else None
        )
        db.session.add(user_webcam)
    
    db.session.commit()
    flash(f'Successfully configured {webcam.name}')
    return redirect(url_for('main.index'))

@webcam_bp.route('/delete/<int:webcam_id>', methods=['POST'])
@login_required
def delete(webcam_id):
    user_webcam = UserWebcam.query.filter_by(
        user_id=current_user.id,
        webcam_id=webcam_id
    ).first_or_404()
    
    db.session.delete(user_webcam)
    db.session.commit()
    flash('Webcam removed from your list')
    return redirect(url_for('main.index'))

@webcam_bp.route('/capture/<int:webcam_id>', methods=['POST'])
@login_required
def capture(webcam_id):
    webcam = Webcam.query.get_or_404(webcam_id)
    logging.info(f"Attempting to capture webcam {webcam_id} of type {webcam.type}")
    success = capture_webcam(webcam)
    if success:
        flash('Webcam captured successfully!', 'success')
    else:
        flash('Failed to capture webcam.', 'error')
    return redirect(url_for('main.index')) 