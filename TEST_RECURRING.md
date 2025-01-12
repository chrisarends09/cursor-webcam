# Webcam Testing Guide

This guide explains how to use the test_webcams.py script to verify webcam functionality.

## Setup

1. Create a test configuration file:    
test_webcams.yaml

webcams:
resort_name:
name: webcam_name
type: direct_image # or other supported type
url: https://example.com/webcam
description: Test Webcam


2. Ensure Discord webhook URLs are configured in your .env file:

DISCORD_WEBHOOK_URLS=https://discordapp.com/api/webhooks/


## Running Tests

### Basic Test (Run Once)
bash
python test_webcams.py --once


### Recurring Test

bash
Run every 5 minutes for 1 hour
python test_webcams.py --interval 5 --duration 60

Run every 10 minutes indefinitely
python test_webcams.py --interval 10 --duration 0



### Test Options
- `--interval`: Minutes between captures (default: 5)
- `--duration`: Total test duration in minutes (default: 60, 0 for indefinite)
- `--once`: Run one test cycle and exit

## Supported Webcam Types
- direct_image
- wetmet
- camstreamer
- nest
- api
- mjpeg
- click2stream
- html_image

## Monitoring Results
- Results are logged to webcam_test.log
- Successful captures are marked with ✅
- Failed captures are marked with ❌
- Images are saved to test_snapshots/ directory
- Discord notifications are sent for each capture

## Troubleshooting
1. Check webcam_test.log for detailed error messages
2. Verify webcam URLs are accessible
3. Ensure correct webcam type is specified
4. Check Discord webhook URLs are valid


These changes provide a robust testing framework for the webcams. The test script can be run with different intervals and durations, making it easy to verify webcam functionality over time.
To test a specific webcam configuration:
1. Add the webcam details to test_webcams.yaml
2. Run a quick test:
python test_webcams.py --once

3. Run a longer test:
python test_webcams.py --interval 5 --duration 30