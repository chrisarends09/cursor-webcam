import threading
import time
from datetime import datetime, timedelta
from app import create_app, db
from app.models.webcam import UserWebcam
from app.utils.webcam_capture import capture_webcam

class WebcamScheduler:
    def __init__(self):
        self.app = create_app()
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _run(self):
        while self.running:
            with self.app.app_context():
                self._check_and_capture()
            time.sleep(60)  # Check every minute

    def _check_and_capture(self):
        try:
            now = datetime.utcnow()
            due_webcams = UserWebcam.query.filter(
                UserWebcam.next_capture <= now,
                UserWebcam.interval_hours.isnot(None)
            ).all()

            for user_webcam in due_webcams:
                if capture_webcam(user_webcam.webcam):
                    user_webcam.last_capture = now
                    user_webcam.next_capture = now + timedelta(hours=user_webcam.interval_hours)
                    db.session.commit()

        except Exception as e:
            print(f"Error in scheduler: {str(e)}")

# Create global scheduler instance
scheduler = WebcamScheduler() 