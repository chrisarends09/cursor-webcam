#!/bin/bash

# Remove any existing X server lock file
rm -f /tmp/.X99-lock

# Start Xvfb
Xvfb :99 -screen 0 1280x1024x24 &
sleep 2

# Start Flask application
export PYTHONPATH=/app
cd /app && FLASK_APP=app.main python -m flask run --host=0.0.0.0 