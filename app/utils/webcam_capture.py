import os
from datetime import datetime
from app.webcam_handlers import WebcamManager
import logging

def capture_webcam(webcam):
    """Capture a snapshot from a webcam"""
    try:
        manager = WebcamManager()
        output_dir = os.path.join(os.getcwd(), 'snapshots')
        os.makedirs(output_dir, exist_ok=True)
        
        webcam_config = {
            'name': webcam.name,
            'type': webcam.type,
            'url': webcam.url,
            'description': webcam.description
        }
        
        # Debug logging
        logging.info(f"Attempting to capture webcam: {webcam_config}")
        
        return manager.capture_webcam(webcam_config, output_dir)
        
    except Exception as e:
        logging.error(f"Error capturing webcam: {str(e)}")
        return False 