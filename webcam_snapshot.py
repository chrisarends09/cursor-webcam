import cv2
import time
import os
import logging
import requests
import numpy as np
from datetime import datetime, timedelta
import subprocess
import tempfile
import json
from bs4 import BeautifulSoup
import re
import schedule
import sys
import argparse

DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1325728300475088916/Tm1O2ubFDci_7y12Qn0eeFTwnaJlipV4glXCBdby7gt9FBAJCt1nIk23Mh5BDxCFuOuC"

def get_stream_url(html_content, camera_name):
    """Extract the actual stream URL from the HTML content."""
    try:
        logging.info(f"Parsing HTML content for {camera_name}")
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for video source elements
        logging.info(f"Searching for video source elements for {camera_name}")
        video_sources = soup.find_all('source')
        for source in video_sources:
            src = source.get('src')
            if src:
                logging.info(f"Found stream URL in video source for {camera_name}: {src}")
                return src

        # Alternative: look for video.js data setup
        logging.info(f"Searching for video.js setup in scripts for {camera_name}")
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'videojs' in script.string.lower():
                logging.info(f"Found videojs script for {camera_name}")
                # Look for URLs in the script content
                urls = re.findall(r'["\'](https?://[^\s<>"\']+?)["\'"]', script.string)
                for url in urls:
                    if any(ext in url.lower() for ext in ['.m3u8', '.mp4', '.jpg', '.jpeg']):
                        logging.info(f"Found stream URL in script for {camera_name}: {url}")
                        return url

        # If no URL found, log the HTML content for debugging
        logging.error(f"Could not find stream URL in HTML for {camera_name}")
        logging.debug(f"HTML content for {camera_name}: {html_content[:500]}...")  # First 500 chars
        return None

    except Exception as e:
        logging.error(f"Error parsing HTML for {camera_name}: {str(e)}")
        logging.exception("Stack trace:")
        return None

def send_to_discord(filepath, camera_name):
    """Send image to Discord webhook"""
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (os.path.basename(filepath), f)}
            payload = {
                'content': f"New snapshot from {camera_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
            response = requests.post(DISCORD_WEBHOOK, data=payload, files=files)
            response.raise_for_status()
            logging.info(f"Successfully sent snapshot to Discord for {camera_name}")
    except Exception as e:
        logging.error(f"Failed to send snapshot to Discord for {camera_name}: {str(e)}")

def capture_from_m3u8(stream_url, output_path, camera_name):
    """Capture a single frame from an HLS stream using ffmpeg."""
    logging.info(f"Starting ffmpeg capture for {camera_name}")
    try:
        # Wait for advertisement to finish
        logging.info(f"Waiting 4 seconds for potential advertisement to finish for {camera_name}")
        time.sleep(4)

        # Use ffmpeg to capture a single frame
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-i', stream_url,  # Input stream URL
            '-vframes', '1',  # Capture only one frame
            '-f', 'image2',  # Output format
            output_path
        ]
        
        logging.info(f"Executing ffmpeg command for {camera_name}")
        # Run ffmpeg command
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        if result.returncode == 0:
            logging.info(f"FFmpeg successfully captured frame for {camera_name}")
            return True
        else:
            logging.error(f"FFmpeg error for {camera_name}: {result.stderr.decode()}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error(f"FFmpeg process timed out for {camera_name}")
        return False
    except Exception as e:
        logging.error(f"Error capturing frame with ffmpeg for {camera_name}: {str(e)}")
        return False

def capture_snapshot_from_url(url, camera_name, output_dir, send_to_discord_webhook=True):
    logging.info(f"Starting snapshot capture process for {camera_name}")
    logging.info(f"Attempting to access stream page for {camera_name} at {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://api.wetmet.net/',
    }

    try:
        # First get the HTML page
        logging.info(f"Fetching HTML page for {camera_name}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Extract the actual stream URL
        stream_url = get_stream_url(response.text, camera_name)
        if not stream_url:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{camera_name}_{timestamp}.jpg"
        filepath = os.path.join(output_dir, filename)

        # For m3u8 streams, use ffmpeg to capture
        if '.m3u8' in stream_url.lower():
            if capture_from_m3u8(stream_url, filepath, camera_name):
                logging.info(f"Snapshot saved: {filepath}")
                if send_to_discord_webhook:
                    send_to_discord(filepath, camera_name)
            else:
                logging.error(f"Failed to capture snapshot for {camera_name}")
            return

        # For direct image URLs, use the previous method
        logging.info(f"Attempting direct image capture for {camera_name}")
        headers['Accept'] = 'image/webp,image/apng,image/*,*/*;q=0.8'
        response = requests.get(stream_url, headers=headers, timeout=10)
        response.raise_for_status()

        if 'image' in response.headers.get('content-type', ''):
            image_array = np.frombuffer(response.content, np.uint8)
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imwrite(filepath, frame)
                logging.info(f"Snapshot saved: {filepath}")
                if send_to_discord_webhook:
                    send_to_discord(filepath, camera_name)
            else:
                logging.error(f"Failed to decode image for {camera_name}")
        else:
            logging.error(f"Unexpected content type for {camera_name}: {response.headers.get('content-type')}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing URL for {camera_name}: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error for {camera_name}: {str(e)}")
        logging.exception("Stack trace:")

def capture_all_cameras(cameras, output_dir):
    """Capture snapshots from all cameras"""
    logging.info("Starting capture for all cameras")
    for camera in cameras:
        capture_snapshot_from_url(camera["url"], camera["name"], output_dir)
    logging.info("Finished capture for all cameras")

def get_schedule_choice():
    """Prompt user for schedule choice"""
    logging.info("Starting webcam snapshot script")
    print("\nHow would you like to run the webcam snapshots?")
    print("\n1. Run once")
    print("   • Takes one snapshot of each camera immediately")
    print("   • Sends images to Discord")
    print("   • Exits after completion")
    print("\n2. Run recurring")
    print("   • Takes snapshots at regular intervals")
    print("   • Continues running until stopped")
    print("   • Sends images to Discord after each capture")
    print("   • Can choose interval: 1, 8, 12, or 24 hours")
    print("\nNote: All snapshots are saved in the 'snapshots' directory")
    print("      and sent to Discord automatically.\n")
    
    while True:
        try:
            choice = input("Enter your choice (1 Run Once or 2 Run Recurring): ").strip()
            if choice in ['1', '2']:
                logging.info(f"User selected {'one-time' if choice == '1' else 'recurring'} execution")
                return choice
            print("\nInvalid choice. Please enter:")
            print("1 - for a single snapshot now")
            print("2 - for recurring snapshots at intervals")
        except Exception as e:
            print("\nInvalid input. Please try again.")

def get_interval_choice():
    """Prompt user for interval choice if running recurring"""
    print("\nHow often should snapshots be taken?")
    print("\n1. Every 1 hour")
    print("   • Best for detailed monitoring")
    print("   • Generates 24 snapshots per day")
    print("\n2. Every 8 hours")
    print("   • Good for tracking major changes")
    print("   • Generates 3 snapshots per day")
    print("\n3. Every 12 hours")
    print("   • Twice daily snapshots")
    print("   • Morning and evening coverage")
    print("\n4. Every 24 hours")
    print("   • Once daily snapshot")
    print("   • Minimal storage usage")
    
    intervals = {
        '1': 1,
        '2': 8,
        '3': 12,
        '4': 24
    }
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            if choice in intervals:
                hours = intervals[choice]
                logging.info(f"User selected {hours} hour{'s' if hours > 1 else ''} interval")
                return hours
            print("\nInvalid choice. Please enter a number between 1 and 4:")
            print("1 - Every hour")
            print("2 - Every 8 hours")
            print("3 - Every 12 hours")
            print("4 - Every 24 hours")
        except Exception as e:
            print("\nInvalid input. Please try again.")

def send_schedule_status_to_discord(schedule_info):
    """Send schedule status to Discord webhook"""
    try:
        payload = {
            'content': f"📅 Current Schedule Status:\n{schedule_info}"
        }
        response = requests.post(DISCORD_WEBHOOK, json=payload)
        response.raise_for_status()
        logging.info("Successfully sent schedule status to Discord")
    except Exception as e:
        logging.error(f"Failed to send schedule status to Discord: {str(e)}")

def get_next_run_time(interval_hours):
    """Get the next scheduled run time"""
    next_run = datetime.now() + timedelta(hours=interval_hours)
    return next_run.strftime('%Y-%m-%d %H:%M:%S')

def get_run_settings():
    """Get run settings either from arguments or interactive input"""
    # First try to get from command line
    parser = argparse.ArgumentParser(description='Webcam Snapshot Script')
    parser.add_argument('--mode', type=str, choices=['once', 'recurring'],
                       help='Run mode: "once" for single run or "recurring" for scheduled runs')
    parser.add_argument('--interval', type=int, choices=[1, 8, 12, 24],
                       help='Interval in hours (required if mode is recurring)')
    parser.add_argument('--interactive', action='store_true',
                       help='Use interactive prompts instead of command line arguments')
    
    args = parser.parse_args()
    
    # If interactive flag is set or no mode specified, use prompts
    if args.interactive or args.mode is None:
        mode_choice = get_schedule_choice()
        mode = 'once' if mode_choice == '1' else 'recurring'
        interval = None if mode == 'once' else get_interval_choice()
        return mode, interval
    
    # Otherwise use command line arguments
    if args.mode == 'recurring' and args.interval is None:
        parser.error('--interval is required when mode is recurring')
    
    return args.mode, args.interval

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('webcam_snapshot.log')
        ]
    )

    # Get settings either from arguments or prompts
    mode, interval = get_run_settings()
    logging.info(f"Starting script in {mode} mode")

    # Directory to save snapshots
    output_dir = "snapshots"
    os.makedirs(output_dir, exist_ok=True)

    # Camera URLs and names
    cameras = [
        {
            "name": "Base_Area",
            "url": "https://api.wetmet.net/widgets/stream/frame.php?uid=072e3c1a6016174851619e4180909d3d"
        },
        {
            "name": "Top_of_Blue",
            "url": "https://api.wetmet.net/widgets/stream/frame.php?uid=c878c340832e23aab90526673b71cc17"
        }
    ]

    if mode == 'once':
        # Run once
        logging.info("Running one-time capture")
        capture_all_cameras(cameras, output_dir)
        schedule_info = "✅ One-time capture completed. Script will now exit."
        send_schedule_status_to_discord(schedule_info)
        logging.info("One-time capture completed")
        return
    
    # Schedule recurring captures
    interval_hours = interval
    schedule.every(interval_hours).hours.do(capture_all_cameras, cameras, output_dir)
    next_run = get_next_run_time(interval_hours)
    
    # Do initial capture
    logging.info("Performing initial capture")
    capture_all_cameras(cameras, output_dir)
    
    # Send schedule status to Discord
    schedule_info = (
        f"🔄 Schedule Status:\n"
        f"• Running every {interval_hours} hour{'s' if interval_hours > 1 else ''}\n"
        f"• Next capture scheduled for: {next_run}\n"
        f"• Initial capture completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    send_schedule_status_to_discord(schedule_info)
    
    # Keep the script running
    logging.info(f"Script will run every {interval_hours} hour{'s' if interval_hours > 1 else ''}")
    logging.info(f"Next capture scheduled for: {next_run}")
    
    last_log_time = datetime.now()
    log_interval = timedelta(minutes=15)  # Log every 15 minutes
    
    while True:
        schedule.run_pending()
        current_time = datetime.now()
        
        # Only log if 15 minutes have passed since last log
        if current_time - last_log_time >= log_interval:
            if schedule.next_run():
                next_run = schedule.next_run().strftime('%Y-%m-%d %H:%M:%S')
                logging.info(f"Waiting for next capture at: {next_run}")
            last_log_time = current_time
            
        time.sleep(60)  # Still check schedule every minute

if __name__ == "__main__":
    main()
