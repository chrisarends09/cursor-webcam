FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    python3-pip \
    wget \
    curl \
    unzip \
    gnupg \
    xvfb \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install matching ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | awk '{print $3}') \
    && MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d. -f1) \
    && echo "Chrome version: $CHROME_VERSION" \
    && echo "Major version: $MAJOR_VERSION" \
    && wget -q -O /tmp/LATEST_RELEASE "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$MAJOR_VERSION" \
    && CHROMEDRIVER_VERSION=$(cat /tmp/LATEST_RELEASE) \
    && echo "ChromeDriver version: $CHROMEDRIVER_VERSION" \
    && wget -q -O /tmp/chromedriver.zip "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 /tmp/LATEST_RELEASE \
    && chmod +x /usr/local/bin/chromedriver

# Install Python dependencies
RUN pip3 install youtube-dl selenium opencv-python-headless requests beautifulsoup4 schedule colorama pyyaml

# Copy the application code and configuration
COPY webcam_snapshot.py .
COPY webcam_handlers.py .
COPY webcams.yaml .

# Set environment variables
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Create a script to start Xvfb and the application
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1280x1024x24 &\n\
sleep 1\n\
exec python -u webcam_snapshot.py --interactive\n\
' > /app/start.sh \
    && chmod +x /app/start.sh

# Run the start script
ENTRYPOINT ["/app/start.sh"]

