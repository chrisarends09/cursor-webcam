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

