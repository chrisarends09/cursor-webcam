from app import scheduler, db
from app.models.webcam import UserWebcam
from app.utils.webcam_capture import capture_webcam
from datetime import datetime, timedelta
import logging
import pytz

def schedule_webcam_capture(user_webcam):
    """Schedule a webcam capture job"""
    job_id = f'capture_{user_webcam.webcam_id}_{user_webcam.user_id}'
    
    # Get timezone
    tz = pytz.timezone('America/Los_Angeles')
    
    # Calculate next run time
    next_run = datetime.now(tz) + timedelta(minutes=1)
    
    # Add new job
    scheduler.add_job(
        func=execute_webcam_capture,
        trigger='interval',
        hours=user_webcam.interval_hours,
        next_run_time=next_run,
        id=job_id,
        name=f"Capture {user_webcam.webcam.name}",
        args=[user_webcam.webcam_id, user_webcam.user_id],
        replace_existing=True
    )
    
    logging.info(f"Scheduled capture for {user_webcam.webcam.name} every {user_webcam.interval_hours} hours (next run: {next_run.strftime('%Y-%m-%d %I:%M:%S %p %Z')})")
    
    # Update next capture time in database
    user_webcam.next_capture = next_run
    db.session.commit()

def execute_webcam_capture(webcam_id, user_id):
    """Execute a scheduled webcam capture"""
    try:
        tz = pytz.timezone('America/Los_Angeles')
        user_webcam = UserWebcam.query.filter_by(
            webcam_id=webcam_id,
            user_id=user_id
        ).first()
        
        if not user_webcam:
            logging.error(f"UserWebcam not found for webcam_id={webcam_id}, user_id={user_id}")
            return
        
        logging.info(f"Executing scheduled capture for {user_webcam.webcam.name}")
        
        # Perform capture
        success = capture_webcam(user_webcam.webcam)
        
        # Update capture times
        if success:
            now = datetime.now(tz)
            next_capture = now + timedelta(hours=user_webcam.interval_hours)
            
            user_webcam.last_capture = now
            user_webcam.next_capture = next_capture
            db.session.commit()
            
            logging.info(f"Next capture scheduled for: {next_capture.strftime('%Y-%m-%d %I:%M:%S %p %Z')}")
        else:
            logging.error(f"Failed to capture {user_webcam.webcam.name}")
            
    except Exception as e:
        logging.error(f"Error in scheduled capture: {str(e)}")

def remove_webcam_schedule(user_webcam):
    """Remove a webcam capture schedule"""
    job_id = f'capture_{user_webcam.webcam_id}_{user_webcam.user_id}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logging.info(f"Removed job {job_id}") 