#!/usr/bin/env python3
import argparse
import time
import logging
from datetime import datetime
import os
from app.webcam_handlers import WebcamManager
import yaml

def setup_logging():
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('webcam_test.log')
        ]
    )

def load_test_config():
    """Load test configuration from test_webcams.yaml"""
    if not os.path.exists('test_webcams.yaml'):
        # Create default test config if it doesn't exist
        test_config = {
            'webcams': {
                'test_resort': [
                    {
                        'name': 'test_webcam',
                        'type': 'direct_image',
                        'url': 'https://example.com/test.jpg',
                        'description': 'Test Webcam'
                    }
                ]
            }
        }
        with open('test_webcams.yaml', 'w') as f:
            yaml.dump(test_config, f)
        
    with open('test_webcams.yaml', 'r') as f:
        return yaml.safe_load(f)

def run_test_cycle(manager, webcams):
    """Run one test cycle for all configured webcams"""
    output_dir = "test_snapshots"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    for resort, cams in webcams['webcams'].items():
        for cam in cams:
            logging.info(f"Testing webcam: {cam['name']}")
            success = manager.capture_webcam(cam, output_dir)
            results.append({
                'name': cam['name'],
                'success': success,
                'timestamp': datetime.now().isoformat()
            })
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Test Webcam Captures')
    parser.add_argument('--interval', type=int, default=5,
                       help='Interval between captures in minutes (default: 5)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Total test duration in minutes (default: 60)')
    parser.add_argument('--once', action='store_true',
                       help='Run test once and exit')
    
    args = parser.parse_args()
    
    setup_logging()
    manager = WebcamManager()
    webcams = load_test_config()
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=args.duration)
    
    logging.info(f"Starting webcam tests - Interval: {args.interval} minutes")
    
    try:
        while True:
            results = run_test_cycle(manager, webcams)
            
            # Log results
            for result in results:
                status = "✅" if result['success'] else "❌"
                logging.info(f"{status} {result['name']} - {result['timestamp']}")
            
            if args.once:
                break
                
            if datetime.now() >= end_time:
                logging.info("Test duration completed")
                break
                
            # Sleep until next interval
            time.sleep(args.interval * 60)
            
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
    except Exception as e:
        logging.error(f"Error during test: {str(e)}")
        raise

if __name__ == '__main__':
    main() 