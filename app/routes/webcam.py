from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.webcam import Webcam, UserWebcam
from app.forms.webcam import WebcamForm
from app.utils.webcam_capture import capture_webcam
from webcam_snapshot import send_to_discord
from datetime import datetime, timedelta
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from app.utils.scheduler import schedule_webcam_capture, remove_webcam_schedule

webcam_bp = Blueprint('webcam', __name__, url_prefix='/webcam')

DISCORD_WEBHOOKS = [url.strip() for url in os.getenv('DISCORD_WEBHOOK_URLS', '').split(',') if url.strip()]
logging.info(f"Loaded {len(DISCORD_WEBHOOKS)} Discord webhook URLs")
if not DISCORD_WEBHOOKS:
    logging.warning("No Discord webhook URLs found in environment variables")

# Initialize the scheduler with more robust configuration
scheduler = BackgroundScheduler({
    'apscheduler.timezone': 'UTC',
    'apscheduler.job_defaults.coalesce': True,
    'apscheduler.job_defaults.max_instances': 1
})
scheduler.start()

def scheduled_capture(webcam_id, user_id, app):
    """Execute scheduled capture for a webcam"""
    with app.app_context():
        try:
            logging.info(f"Starting scheduled capture for webcam {webcam_id} and user {user_id}")
            user_webcam = UserWebcam.query.filter_by(
                user_id=user_id,
                webcam_id=webcam_id
            ).first()
            
            if user_webcam:
                webcam = Webcam.query.get(webcam_id)
                if webcam:
                    logging.info(f"Executing scheduled capture for {webcam.name}")
                    success = capture_webcam(webcam)
                    if success:
                        # Update last_capture time
                        user_webcam.last_capture = datetime.utcnow()
                        # Set next capture time
                        user_webcam.next_capture = datetime.utcnow() + timedelta(hours=user_webcam.interval_hours)
                        db.session.commit()
                        logging.info(f"Scheduled capture completed for {webcam.name}")
                        
                        # Find the most recent file for this webcam
                        snapshot_dir = '/app/snapshots'
                        files = [f for f in os.listdir(snapshot_dir) if f.startswith(webcam.name)]
                        if files:
                            # Sort by modification time, newest first
                            files.sort(key=lambda x: os.path.getmtime(os.path.join(snapshot_dir, x)), reverse=True)
                            latest_file = os.path.join(snapshot_dir, files[0])
                            
                            try:
                                send_to_discord(latest_file, f"Scheduled capture - {webcam.name}: {webcam.description}")
                                logging.info(f"Successfully sent scheduled capture to Discord for {webcam.name}")
                            except Exception as e:
                                logging.error(f"Failed to send Discord notification: {str(e)}", exc_info=True)
                        else:
                            logging.error(f"No capture files found for {webcam.name}")
                        
                        # Log next scheduled capture
                        job = scheduler.get_job(f"capture_{webcam_id}_{user_id}")
                        if job:
                            logging.info(f"Next capture scheduled for: {job.next_run_time}")
                        else:
                            logging.error("Job not found in scheduler")
                        return True
                    else:
                        logging.error(f"Scheduled capture failed for {webcam.name}")
                else:
                    logging.error(f"Webcam {webcam_id} not found")
            else:
                logging.error(f"UserWebcam not found for user {user_id} and webcam {webcam_id}")
            return False
        except Exception as e:
            logging.error(f"Error in scheduled capture: {str(e)}", exc_info=True)
            return False

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
    
    # Create or update UserWebcam record first
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
    
    # Commit the database changes before scheduling
    db.session.commit()
    
    # Now handle the scheduler
    job_id = f"capture_{webcam_id}_{current_user.id}"
    try:
        scheduler.remove_job(job_id)
        logging.info(f"Removed existing job {job_id}")
    except JobLookupError:
        logging.info(f"No existing job found for {job_id}")
    
    if interval:
        # Add new scheduled job
        scheduler.add_job(
            scheduled_capture,
            'interval',
            hours=interval,
            id=job_id,
            name=f"Capture {webcam.name}",
            args=[webcam_id, current_user.id, current_app._get_current_object()],
            next_run_time=datetime.utcnow() + timedelta(seconds=5),  # Start first capture after 5 seconds
            replace_existing=True
        )
        logging.info(f"Added new scheduled job {job_id} with {interval} hour interval")
    
    # Log all current jobs
    jobs = scheduler.get_jobs()
    logging.info(f"Current scheduled jobs: {[job.id for job in jobs]}")
    
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
    
    # Get the timestamp for the filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{webcam.name}_{timestamp}.jpg"
    output_path = os.path.join('/app/snapshots', filename)
    
    success = capture_webcam(webcam)
    
    if success:
        # Import the send_to_discord function
        from webcam_snapshot import send_to_discord
        
        # Attempt to send to Discord
        discord_success = send_to_discord(output_path, webcam.description)
        if discord_success:
            flash('Webcam captured and sent to Discord successfully!', 'success')
        else:
            flash('Webcam captured but failed to send to Discord.', 'warning')
    else:
        flash('Failed to capture webcam.', 'error')
    
    return redirect(url_for('main.index'))

@webcam_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_webcam(id):
    webcam = Webcam.query.get_or_404(id)
    form = WebcamForm(obj=webcam)
    
    if form.validate_on_submit():
        webcam.name = form.name.data
        webcam.description = form.description.data
        webcam.url = form.url.data
        webcam.type = form.type.data
        webcam.resort = form.resort.data
        
        db.session.commit()
        flash('Webcam updated successfully!', 'success')
        return redirect(url_for('webcam.list'))
        
    return render_template('webcam/edit.html', form=form, webcam=webcam)

@webcam_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_webcam(id):
    webcam = Webcam.query.get_or_404(id)
    
    # Delete associated UserWebcam entries first
    UserWebcam.query.filter_by(webcam_id=id).delete()
    
    db.session.delete(webcam)
    db.session.commit()
    
    flash('Webcam deleted successfully!', 'success')
    return redirect(url_for('webcam.list'))

@webcam_bp.route('/list')
@login_required
def list():
    """Display list of all webcams"""
    webcams = Webcam.query.all()
    return render_template('webcam/list.html', webcams=webcams)

@webcam_bp.route('/webcam/select/<int:webcam_id>', methods=['POST'])
@login_required
def select_webcam(webcam_id):
    interval = request.form.get('interval', type=int)
    
    user_webcam = UserWebcam.query.filter_by(
        user_id=current_user.id,
        webcam_id=webcam_id
    ).first()
    
    if user_webcam:
        # Update existing schedule
        user_webcam.interval_hours = interval
        if interval:
            schedule_webcam_capture(user_webcam)
        else:
            remove_webcam_schedule(user_webcam)
    else:
        # Create new schedule
        user_webcam = UserWebcam(
            user_id=current_user.id,
            webcam_id=webcam_id,
            interval_hours=interval
        )
        db.session.add(user_webcam)
        if interval:
            schedule_webcam_capture(user_webcam)
    
    db.session.commit()
    return redirect(url_for('main.index')) 