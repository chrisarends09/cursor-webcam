#Troubleshooting
docker compose down
docker compose build
docker compose up -d 
docker compose logs -f web  see what the logs say when using localhost:5000
assumes you have done the initial setup:



# Webcam Snapshot Manager

A Docker-based application that captures and manages snapshots from various types of webcams, including live streams, static images, and embedded video feeds. The application can take one-time snapshots or run on a schedule, automatically sending the captured images to Discord channels.

## Features

- Support for multiple webcam types:
  - Direct image URLs
  - Live video streams (HLS, RTMP)
  - Embedded webcams (YouTube, Nest)
  - API-based webcams
  - HTML-embedded images
  - MJPEG streams
  - Click2Stream webcams
- Flexible scheduling options (1, 8, 12, or 24-hour intervals)
- Multi-server Discord integration
- Automatic error handling and retries
- Detailed logging
- Interactive command-line interface

## Prerequisites

- Docker and Docker Compose
- A Discord webhook URL

## Initial Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd webcam-snapshot-manager
```

2. Create required directories with proper permissions:
```bash
mkdir -p snapshots
chmod 777 snapshots
```

3. Create and configure environment files:
```bash
# Create .env file
cp .env.example .env

# Generate a secret key and add it to .env
python3 -c 'import secrets; print(secrets.token_urlsafe(32))' >> .env
```

4. Build and start the Docker containers:
```bash
docker compose down
docker compose build
docker compose up -d
```

5. Initialize the database:
```bash
docker compose exec web flask db upgrade
docker compose exec web python -m app.init_db
```

6. Verify the setup:
```bash
# Check the logs
docker compose logs -f web

# Access the web interface
open http://localhost:5000
```

7. Configure Discord webhooks:
Edit the `.env` file and add your Discord webhook URL(s):
```env
DISCORD_WEBHOOK_URLS=https://discord.com/api/webhooks/your_webhook_url_here
```

## Setup

1. Make the run script executable:
```bash
chmod +x run.sh
```

2. Create a `.env` file in the project root with your Discord webhook URL(s):
```env
# Single Discord webhook
DISCORD_WEBHOOK_URLS=https://discord.com/api/webhooks/your_webhook_url_here

# Multiple Discord webhooks (comma-separated)
# DISCORD_WEBHOOK_URLS=https://discord.com/api/webhooks/url1,https://discord.com/api/webhooks/url2
```

## Usage

The `run.sh` script provides an interactive menu to control the webcam snapshot functionality:

1. **Start new capture**
   - Choose 'Run once' to take a single set of snapshots
   - Choose 'Run recurring' to take snapshots at regular intervals
   - Recurring intervals available: 1, 8, 12, or 24 hours
   - All snapshots are saved locally and sent to Discord

2. **Stop current capture**
   - Stops any running capture process
   - Safe to use even if no capture is running

3. **View logs**
   - Shows detailed logs of the capture process
   - Includes timing and status of all snapshots

4. **Exit**
   - Exits the control menu
   - Does NOT stop running captures (use option 2 first)

## Output

- Snapshots are saved in the `snapshots` directory
- Images are automatically sent to configured Discord channel(s)
- Schedule status updates are sent to Discord in recurring mode

## Configuration

Webcams are configured in `webcams.yaml`. The application supports various types of webcams and can be extended to support more.

## Logging

Detailed logs are written to `webcam_snapshot.log` for troubleshooting and monitoring.

## Note

Make sure to set up your Discord webhook URL in the `.env` file before running the application.

## Deployment

### Using Docker (Recommended)

1. Build and start the containers:
```bash
docker-compose up -d
```

2. Initialize the database:
```bash
docker-compose exec web flask db upgrade
docker-compose exec web python -m app.init_db
```

### Manual Deployment

1. Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pip python3-venv nginx
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Gunicorn service:
```bash
sudo nano /etc/systemd/system/webcam-manager.service
```

Add the following content:
```ini
[Unit]
Description=Webcam Manager
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/webcam-manager
Environment="PATH=/path/to/webcam-manager/venv/bin"
ExecStart=/path/to/webcam-manager/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"

[Install]
WantedBy=multi-user.target
```

5. Set up Nginx:
```bash
sudo nano /etc/nginx/sites-available/webcam-manager
```

Add the following content:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/webcam-manager/app/static;
    }

    location /snapshots {
        alias /path/to/webcam-manager/snapshots;
    }
}
```

6. Enable and start services:
```bash
sudo ln -s /etc/nginx/sites-available/webcam-manager /etc/nginx/sites-enabled/
sudo systemctl start webcam-manager
sudo systemctl enable webcam-manager
sudo systemctl restart nginx
```

## API Documentation

The application provides a REST API for webcam management:

### Endpoints

#### GET /api/webcams
Get all available webcams.

Response:
```json
[
    {
        "id": 1,
        "name": "Webcam Name",
        "description": "Description",
        "url": "http://example.com/webcam",
        "type": "direct_image",
        "resort": "Resort Name"
    }
]
```

#### GET /api/webcams/user
Get webcams configured for the current user.

Response:
```json
[
    {
        "id": 1,
        "name": "Webcam Name",
        "interval_hours": 1,
        "last_capture": "2024-01-20T12:00:00Z",
        "next_capture": "2024-01-20T13:00:00Z"
    }
]
```

#### POST /api/webcams/{webcam_id}/capture
Trigger a webcam capture.

Response:
```json
{
    "status": "success"
}
```

### Authentication

All API endpoints require authentication. Include your session cookie in the requests.


### Create secret key
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

