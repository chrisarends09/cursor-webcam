from abc import ABC, abstractmethod
import requests
import logging
import cv2
import numpy as np
import subprocess
import re
import time
from bs4 import BeautifulSoup
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

class WebcamHandler(ABC):
    @abstractmethod
    def capture_frame(self, url, output_path, webcam_config=None):
        pass

class DirectImageHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info(f"Attempting to download direct image from {url}")
            
            # Add scheme if missing
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            
            # Create a session to handle cookies and redirects
            session = requests.Session()
            
            # Special handling for HDRelay
            if 'hdrelay.com' in url:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Referer': 'https://www.mthood.com/'
                }
                
                # First request to get the redirect
                try:
                    response = session.get(url, headers=headers, allow_redirects=False)
                    if response.status_code in [301, 302, 303, 307, 308]:
                        redirect_url = response.headers.get('Location')
                        if redirect_url:
                            logging.info(f"Following redirect to: {redirect_url}")
                            if not redirect_url.startswith(('http://', 'https://')):
                                redirect_url = f"https://img.hdrelay.com{redirect_url}"
                            img_response = session.get(redirect_url, headers=headers)
                            img_response.raise_for_status()
                            with open(output_path, 'wb') as f:
                                f.write(img_response.content)
                            logging.info("Successfully saved image from HDRelay redirect")
                            return True
                except Exception as e:
                    logging.error(f"Error following HDRelay redirect: {str(e)}")
                    return False
            
            # Standard handling for other URLs
            try:
                response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                if 'Not Allowed' in str(e):
                    url = url.replace('https://', 'http://')
                    response = session.get(url, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
                    response.raise_for_status()
            
            # Save the image
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logging.info("Successfully saved direct image")
            return True
            
        except Exception as e:
            logging.error(f"Error in DirectImageHandler: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False

class WetmetHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            # Get the HTML page first
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://api.wetmet.net/'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Extract stream URL from HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')
            stream_url = None
            
            for script in scripts:
                if script.string and 'videojs' in script.string.lower():
                    urls = re.findall(r'["\'](https?://[^\s<>"\']+?\.m3u8[^\s<>"\']*)["\']', script.string)
                    if urls:
                        stream_url = urls[0]
                        break
            
            if not stream_url:
                logging.error("Could not find stream URL in wetmet page")
                return False
                
            # Use ffmpeg to capture frame from stream
            command = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-i', stream_url,  # Input stream
                '-vframes', '1',  # Capture one frame
                '-f', 'image2',  # Output format
                output_path
            ]
            
            # Wait for potential advertisement
            time.sleep(4)
            
            result = subprocess.run(command, capture_output=True)
            return result.returncode == 0
            
        except Exception as e:
            logging.error(f"Error in WetmetHandler: {str(e)}")
            return False

class CamstreamerHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info("Attempting to capture from Camstreamer")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.mtbachelor.com/'
            }
            
            session = requests.Session()
            
            # First request to get the redirect
            logging.info(f"Getting initial URL: {url}")
            response = session.get(url, headers=headers, allow_redirects=False)
            
            # Follow redirect if present
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location')
                if redirect_url:
                    logging.info(f"Following redirect to: {redirect_url}")
                    
                    # Check if it's a YouTube embed
                    if 'youtube.com/embed/' in redirect_url:
                        logging.info("Detected YouTube embed, using Selenium to capture")
                        
                        # Setup Chrome options
                        chrome_options = Options()
                        chrome_options.add_argument('--headless')
                        chrome_options.add_argument('--no-sandbox')
                        chrome_options.add_argument('--disable-dev-shm-usage')
                        chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
                        
                        # Create Chrome driver
                        driver = webdriver.Chrome(options=chrome_options)
                        try:
                            # Set window size for better capture
                            driver.set_window_size(1280, 720)
                            
                            # Load the YouTube embed
                            driver.get(redirect_url)
                            
                            # Wait for video to load and start playing
                            logging.info("Waiting for video to load...")
                            time.sleep(8)  # Increased wait time for video to start
                            
                            # Take screenshot
                            driver.save_screenshot(output_path)
                            logging.info("Successfully captured screenshot from YouTube embed")
                            return True
                            
                        finally:
                            driver.quit()
                    
                    # Handle other types of redirects as before...
                    # (keep existing code for non-YouTube redirects)
            
            # Try to find stream URL in the page
            stream_url = None
            
            # Look for HLS stream URL
            matches = re.findall(r'(https?://[^"\']+\.m3u8[^"\']*)', response.text)
            if matches:
                stream_url = matches[0]
                logging.info(f"Found HLS stream URL: {stream_url}")
            
            # If no HLS stream, look for RTMP or other stream URLs
            if not stream_url:
                matches = re.findall(r'source:\s*["\']([^"\']+)["\']', response.text)
                if matches:
                    stream_url = matches[0]
                    logging.info(f"Found stream URL: {stream_url}")
            
            if not stream_url:
                # Try looking in script tags for streamUrl variable
                soup = BeautifulSoup(response.text, 'html.parser')
                for script in soup.find_all('script'):
                    if script.string and 'streamUrl' in script.string:
                        matches = re.findall(r'streamUrl\s*=\s*["\']([^"\']+)["\']', script.string)
                        if matches:
                            stream_url = matches[0]
                            logging.info(f"Found stream URL in script: {stream_url}")
                            break
            
            if not stream_url:
                logging.error("No stream URL found in page")
                return False
            
            # Add headers to ffmpeg command
            command = [
                'ffmpeg',
                '-y',
                '-headers', f'Referer: {url}\r\nUser-Agent: {headers["User-Agent"]}\r\n',
                '-i', stream_url,
                '-vframes', '1',
                '-f', 'image2',
                output_path
            ]
            
            # Wait a bit for stream to initialize
            time.sleep(2)
            
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                logging.info("Successfully captured frame from Camstreamer")
                return True
            else:
                logging.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"Error in CamstreamerHandler: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False

class NestHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info("Attempting to capture from Nest stream")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Create Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Load the page
                logging.info(f"Loading Nest page: {url}")
                driver.get(url)
                
                # Wait for and click the play button
                try:
                    play_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "vjs-big-play-button"))
                    )
                    play_button.click()
                    logging.info("Clicked play button")
                except Exception as e:
                    logging.warning(f"Could not find play button: {str(e)}")
                
                # Wait for video to start playing
                time.sleep(5)
                
                # Take screenshot
                driver.save_screenshot(output_path)
                logging.info("Successfully captured screenshot from Nest stream")
                return True
                
            finally:
                driver.quit()
                
        except Exception as e:
            logging.error(f"Error in NestHandler: {str(e)}")
            return False

class APIHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info(f"Attempting to fetch image from API: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, image/*'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Check if response is JSON
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                # You might need to adjust this based on the actual API response structure
                if 'imageUrl' in data:
                    image_url = data['imageUrl']
                    image_response = requests.get(image_url)
                    image_response.raise_for_status()
                    with open(output_path, 'wb') as f:
                        f.write(image_response.content)
                    logging.info("Successfully saved image from API")
                    return True
                else:
                    logging.error("No image URL found in API response")
                    return False
            else:
                # Direct image response
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logging.info("Successfully saved direct image from API")
                return True
                
        except Exception as e:
            logging.error(f"Error in APIHandler: {str(e)}")
            return False

class MJPEGHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info(f"Attempting to capture MJPEG stream from: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'multipart/x-mixed-replace',
                'Connection': 'keep-alive'
            }
            
            # Try to capture the frame directly
            logging.info(f"Accessing stream with URL: {url}")
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'multipart/x-mixed-replace' not in content_type:
                logging.error(f"Unexpected content type: {content_type}")
                return False

            boundary = content_type.split('boundary=')[-1]
            if not boundary:
                logging.error("No boundary found in content type")
                return False

            buffer = b''
            for chunk in response.iter_content(chunk_size=1024):
                buffer += chunk
                if b'\r\n\r\n' in buffer:
                    # Find the JPEG data
                    parts = buffer.split(b'\r\n\r\n', 1)
                    if len(parts) == 2:
                        jpeg_data = parts[1]
                        with open(output_path, 'wb') as f:
                            f.write(jpeg_data)
                        logging.info("Successfully captured MJPEG frame")
                        return True
                
                if len(buffer) > 100000:  # Prevent buffer from growing too large
                    logging.error("Buffer limit exceeded without finding image")
                    return False
                    
            return False
            
        except Exception as e:
            logging.error(f"Error capturing MJPEG stream: {str(e)}")
            return False

class Click2StreamHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info(f"Attempting to capture from Click2Stream: {url}")
            
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')  # Disable CORS
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # Create Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Load the page
                driver.get(url)
                
                # Wait for iframe to be present and switch to it
                logging.info("Waiting for iframe...")
                iframe = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "iframe"))
                )
                driver.switch_to.frame(iframe)
                
                # Wait for either video or img element
                logging.info("Waiting for video or image element...")
                element = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, "video, img, canvas, #player"
                    ))
                )
                
                # Additional wait for content to load
                time.sleep(8)
                
                # Switch back to default content for full page screenshot
                driver.switch_to.default_content()
                
                # Take screenshot
                driver.save_screenshot(output_path)
                logging.info("Successfully captured Click2Stream webcam")
                return True
                
            finally:
                driver.quit()
                
        except Exception as e:
            logging.error(f"Error in Click2StreamHandler: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False

class HTMLImageHandler(WebcamHandler):
    def capture_frame(self, url, output_path, webcam_config=None):
        try:
            logging.info(f"Attempting to capture HTML image from: {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': url
            }
            
            # Get the webpage content
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get the selector from webcam_config
            selector = webcam_config.get('image_selector') if webcam_config else "img"
            logging.info(f"Using selector: {selector}")
            
            # Find image using selector
            img_element = soup.select_one(selector)
            if not img_element:
                logging.error(f"Could not find image element in HTML using selector: {selector}")
                return False
                
            # Get image URL and clean it
            img_url = img_element.get('src')
            if not img_url:
                logging.error("Image element has no src attribute")
                return False
            
            # Clean the URL - remove extra spaces and encode properly
            img_url = img_url.strip()
            
            # Convert relative URL to absolute if needed
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif not img_url.startswith('http'):
                img_url = urljoin(url, img_url)
                
            logging.info(f"Found image URL: {img_url}")
            
            # Try both http and https
            for protocol in ['https', 'http']:
                try:
                    current_url = img_url.replace('http://', f'{protocol}://')
                    current_url = current_url.replace('https://', f'{protocol}://')
                    logging.info(f"Trying {current_url}")
                    
                    img_response = requests.get(
                        current_url, 
                        headers=headers,
                        allow_redirects=True,
                        verify=False  # Sometimes needed for tripcheck.com
                    )
                    img_response.raise_for_status()
                    
                    # Save the image
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                        
                    logging.info(f"Successfully saved image to {output_path}")
                    return True
                    
                except Exception as e:
                    logging.warning(f"Failed with {protocol}: {str(e)}")
                    continue
            
            logging.error("Failed to download image with both http and https")
            return False
            
        except Exception as e:
            logging.error(f"Error capturing HTML image: {str(e)}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return False

class WebcamManager:
    def __init__(self):
        self.handlers = {
            'direct_image': DirectImageHandler(),
            'wetmet': WetmetHandler(),
            'camstreamer': CamstreamerHandler(),
            'nest': NestHandler(),
            'api': APIHandler(),
            'mjpeg': MJPEGHandler(),
            'click2stream': Click2StreamHandler(),
            'html_image': HTMLImageHandler()
        }

    def load_webcams(self, yaml_path):
        import yaml
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)

    def capture_webcam(self, webcam_config, base_path):
        """Main method to capture webcam based on type"""
        try:
            # Create timestamped filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"{base_path}/{webcam_config['name']}_{timestamp}.jpg"
            
            logging.info(f"Attempting to capture {webcam_config['name']} using {webcam_config['type']} handler")
            # Pass webcam_config to the handler
            success = self.handlers[webcam_config['type']].capture_frame(webcam_config['url'], output_path, webcam_config)
            
            if success:
                logging.info(f"Successfully captured {webcam_config['name']}")
                logging.debug(f"File exists after capture: {os.path.exists(output_path)}")
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    logging.debug(f"File size: {file_size} bytes")
                    logging.debug(f"File permissions: {oct(os.stat(output_path).st_mode)[-3:]}")
                    
                    # Verify image is valid
                    try:
                        img = cv2.imread(output_path)
                        if img is None:
                            logging.error("Captured file is not a valid image")
                            return False
                    except Exception as e:
                        logging.error(f"Error verifying image: {str(e)}")
                        return False
                        
                    # Attempt to send to Discord
                    if not send_to_discord(output_path, webcam_config['name']):
                        logging.error("Failed to send image to Discord")
                        return False
                        
                return True
            else:
                logging.error(f"Failed to capture {webcam_config['name']}")
                return False
                
        except Exception as e:
            logging.error(f"Error in capture_webcam: {str(e)}", exc_info=True)
            return False 