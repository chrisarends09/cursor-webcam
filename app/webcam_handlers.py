import os
import cv2
import requests
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import subprocess

class WebcamManager:
    def __init__(self):
        """Initialize WebcamManager with logging configuration"""
        # Set up logging
        logging.getLogger().setLevel(logging.DEBUG)
        
        # Ensure snapshots directory exists with proper permissions
        self.snapshots_dir = '/app/snapshots'
        try:
            os.makedirs(self.snapshots_dir, mode=0o777, exist_ok=True)
            logging.debug(f"Snapshots directory created/verified: {self.snapshots_dir}")
            logging.debug(f"Directory permissions: {oct(os.stat(self.snapshots_dir).st_mode)[-3:]}")
        except Exception as e:
            logging.error(f"Error creating snapshots directory: {str(e)}")
        
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        
        # Define capture methods
        self.capture_methods = {
            'direct_image': self.capture_direct_image,
            'embedded': self.capture_embedded_webcam,
            'mjpeg': self.capture_mjpeg_stream,
            'wetmet': self.capture_wetmet,
            'camstreamer': self.capture_camstreamer,
            'api': self.capture_api,
            'nest': self.capture_nest,
            'click2stream': self.capture_click2stream,
            'html_image': self.capture_html_image
        }

    def capture_direct_image(self, url, save_path):
        """Capture image from direct image URL"""
        try:
            logging.debug("Starting direct_image capture")
            logging.debug(f"Initial URL: {url}")
            logging.debug(f"Save path: {save_path}")
            
            # Add user agent header to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/jpeg,image/png,*/*',
                'Referer': url
            }
            
            logging.debug(f"Request headers: {headers}")
            
            # Make request with headers and verify SSL
            try:
                logging.debug("Making HTTP request...")
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=10,
                    verify=True,
                    allow_redirects=True
                )
                
                # Log redirect chain if any
                if response.history:
                    for r in response.history:
                        logging.debug(f"Redirect: {r.status_code} - {r.url}")
                    logging.debug(f"Final URL: {response.url}")
                
                logging.debug("HTTP request completed")
                
            except Exception as e:
                logging.error(f"HTTP request failed: {str(e)}")
                raise
            
            # Log response details
            logging.debug(f"Response status code: {response.status_code}")
            logging.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                logging.debug(f"Content-Type: {content_type}")
                content_length = len(response.content)
                logging.debug(f"Content length: {content_length} bytes")
                
                # Verify content is an image
                if not any(img_type in content_type.lower() for img_type in ['jpeg', 'jpg', 'png', 'image']):
                    logging.error(f"Unexpected content type: {content_type}")
                    logging.debug(f"Response preview (hex): {response.content[:100].hex()}")
                    return False
                
                # Create directory if it doesn't exist
                save_dir = os.path.dirname(save_path)
                logging.debug(f"Creating directory: {save_dir}")
                os.makedirs(save_dir, exist_ok=True)
                
                # Save image
                try:
                    logging.debug("Writing image to file...")
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    # Set file permissions
                    os.chmod(save_path, 0o666)
                    logging.debug("File write completed")
                    
                    # Verify file was created and is valid
                    if os.path.exists(save_path):
                        file_size = os.path.getsize(save_path)
                        file_perms = oct(os.stat(save_path).st_mode)[-3:]
                        logging.debug(f"File size on disk: {file_size} bytes")
                        logging.debug(f"File permissions: {file_perms}")
                        
                        if file_size > 0:
                            logging.info(f"Image saved successfully. File size: {file_size} bytes")
                            
                            # Verify image can be opened
                            try:
                                logging.debug("Verifying image with OpenCV...")
                                img = cv2.imread(save_path)
                                if img is not None:
                                    logging.debug("Image verification successful")
                                    return True
                                else:
                                    logging.error("OpenCV could not read the image")
                                    os.remove(save_path)
                                    return False
                            except Exception as e:
                                logging.error(f"Error verifying image with OpenCV: {str(e)}")
                                os.remove(save_path)
                                return False
                        else:
                            logging.error("Saved file is empty")
                            os.remove(save_path)
                            return False
                    else:
                        logging.error("File was not created")
                        return False
                    
                except Exception as e:
                    logging.error(f"Error saving image: {str(e)}")
                    return False
                
            else:
                logging.error(f"Failed to download image. Status code: {response.status_code}")
                logging.debug(f"Response content: {response.text[:500]}")
                return False
                
        except Exception as e:
            logging.error(f"Error in capture_direct_image: {str(e)}", exc_info=True)
            return False

    def capture_embedded_webcam(self, url, save_path):
        """Capture image from embedded webcam"""
        try:
            # Additional Chrome options for better stability
            self.chrome_options.add_argument('--disable-extensions')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=self.chrome_options)
            driver.get(url)
            
            # Wait longer for page load
            driver.implicitly_wait(10)
            
            # Wait for image to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "img"))
            )
            
            # Wait additional time for dynamic content
            time.sleep(5)
            
            # Take screenshot
            # Ensure .jpg extension
            save_path_png = save_path.rsplit('.', 1)[0] + '.png'
            driver.save_screenshot(save_path_png)
            
            # Convert PNG to JPG if needed
            if save_path.endswith('.jpg'):
                img = cv2.imread(save_path_png)
                cv2.imwrite(save_path, img)
                os.remove(save_path_png)
            
            driver.quit()
            return True
        except Exception as e:
            logging.error(f"Error capturing embedded webcam: {str(e)}")
            logging.error(f"URL: {url}")
            if 'driver' in locals():
                driver.quit()
        return False

    def capture_mjpeg_stream(self, url, save_path):
        """Capture frame from MJPEG stream"""
        try:
            cap = cv2.VideoCapture(url)
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(save_path, frame)
                cap.release()
                return True
            cap.release()
        except Exception as e:
            logging.error(f"Error capturing MJPEG stream: {str(e)}")
        return False

    def capture_wetmet(self, url, save_path):
        """Capture from WetMet webcam"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://api.wetmet.net/'
            }
            
            response = requests.get(url, headers=headers)
            logging.info(f"WetMet response status: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for video source in video.js setup
                scripts = soup.find_all('script')
                stream_url = None
                
                for script in scripts:
                    if script.string and 'videojs' in script.string.lower():
                        # Look for HLS stream URL
                        matches = re.findall(r'["\'](https?://[^\s<>"\']+?\.m3u8[^\s<>"\']*)["\']', script.string)
                        if matches:
                            stream_url = matches[0]
                            logging.info(f"Found HLS stream URL: {stream_url}")
                            break
                
                if stream_url:
                    # Use ffmpeg to capture frame from stream
                    command = [
                        'ffmpeg',
                        '-y',  # Overwrite output file
                        '-i', stream_url,  # Input stream
                        '-vframes', '1',  # Capture one frame
                        '-f', 'image2',  # Output format
                        save_path
                    ]
                    
                    # Wait for potential advertisement
                    time.sleep(4)
                    
                    try:
                        result = subprocess.run(command, capture_output=True, text=True)
                        if result.returncode == 0:
                            logging.info("Successfully captured frame from WetMet stream")
                            return True
                        else:
                            logging.error(f"FFmpeg error: {result.stderr}")
                    except Exception as e:
                        logging.error(f"FFmpeg execution error: {str(e)}")
                        return False
                else:
                    logging.error("No stream URL found in WetMet page")
                    return False
                
        except Exception as e:
            logging.error(f"Error capturing WetMet webcam: {str(e)}")
            if 'response' in locals():
                logging.error(f"Response content: {response.text[:500]}...")
        return False

    def capture_camstreamer(self, url, save_path):
        """Capture from CamStreamer"""
        try:
            return self.capture_embedded_webcam(url, save_path)
        except Exception as e:
            logging.error(f"Error capturing CamStreamer: {str(e)}")
        return False

    def capture_api(self, url, save_path):
        """Capture from API endpoint"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/jpeg,image/png,application/json,*/*',
                'Referer': 'https://www.mtbachelor.com/'
            }
            
            response = requests.get(url, headers=headers)
            logging.info(f"API response status: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                logging.info(f"Content-Type: {content_type}")
                
                # Check if response is a direct image
                if 'image' in content_type.lower():
                    logging.info("Received direct image response")
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    logging.info(f"Successfully saved direct image. Size: {len(response.content)} bytes")
                    return True
                    
                # Try to parse as JSON
                elif 'application/json' in content_type.lower():
                    try:
                        data = response.json()
                        logging.info(f"API response data: {data}")
                        
                        # Mt Bachelor specific API handling
                        if 'data' in data and 'url' in data['data']:
                            image_url = data['data']['url']
                            logging.info(f"Found image URL: {image_url}")
                            return self.capture_direct_image(image_url, save_path)
                    except ValueError as e:
                        logging.error(f"Failed to parse JSON response: {str(e)}")
                        
                # Unknown content type - try to save as image anyway
                else:
                    logging.warning(f"Unknown content type: {content_type}")
                    try:
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        # Verify it's a valid image
                        img = cv2.imread(save_path)
                        if img is not None:
                            logging.info(f"Successfully saved and verified image. Size: {len(response.content)} bytes")
                            return True
                        else:
                            logging.error("Invalid image data")
                            os.remove(save_path)
                    except Exception as e:
                        logging.error(f"Error saving response as image: {str(e)}")
                
            return False
            
        except Exception as e:
            logging.error(f"Error capturing from API: {str(e)}")
            if 'response' in locals():
                logging.error(f"Response headers: {dict(response.headers)}")
            return False

    def capture_nest(self, url, save_path):
        """Capture from Nest camera"""
        try:
            logging.info(f"Starting Nest capture for URL: {url}")
            
            # Additional Chrome options for video
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')
            
            driver = webdriver.Chrome(options=chrome_options)
            try:
                driver.get(url)
                
                # Wait for video element to be present
                logging.info("Waiting for video element...")
                video = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                
                # Wait for video to start playing
                logging.info("Waiting for video to load...")
                time.sleep(8)  # Give video time to start playing
                
                # Take screenshot
                logging.info("Taking screenshot...")
                driver.save_screenshot(save_path)
                
                # Verify the screenshot
                img = cv2.imread(save_path)
                if img is not None:
                    logging.info(f"Successfully captured Nest screenshot: {save_path}")
                    return True
                else:
                    logging.error("Failed to verify screenshot")
                    if os.path.exists(save_path):
                        os.remove(save_path)
                    return False
                    
            finally:
                driver.quit()
                
        except Exception as e:
            logging.error(f"Error capturing from Nest: {str(e)}")
            logging.error(f"URL: {url}")
            if 'driver' in locals():
                driver.quit()
            return False

    def capture_click2stream(self, url, save_path):
        """Capture from Click2Stream"""
        try:
            return self.capture_embedded_webcam(url, save_path)
        except Exception as e:
            logging.error(f"Error capturing from Click2Stream: {str(e)}")
        return False

    def capture_html_image(self, url, save_path):
        """Capture image embedded in HTML"""
        try:
            logging.info(f"Starting HTML image capture from {url}")
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for image with specific pattern in src attribute
                img_tag = soup.find('img', src=lambda x: x and 'DeadmanP-CabbageHill' in x)
                
                if img_tag and 'src' in img_tag.attrs:
                    # Clean the URL - strip whitespace and normalize
                    img_url = img_tag['src'].strip()
                    logging.info(f"Found image URL: {img_url}")
                    
                    # Handle relative URLs
                    if not img_url.startswith('http'):
                        base_url = '/'.join(url.split('/')[:3])  # Get domain
                        img_url = f"{base_url}/{img_url.lstrip('/')}"
                    
                    # Ensure URL is properly encoded
                    img_url = img_url.replace(' ', '%20')
                    logging.info(f"Cleaned image URL: {img_url}")
                    
                    return self.capture_direct_image(img_url, save_path)
                else:
                    logging.error("Could not find image with matching pattern")
                    # Log available images for debugging
                    all_images = soup.find_all('img')
                    for img in all_images:
                        logging.debug(f"Found image: {img.get('src', 'No src')}")
            else:
                logging.error(f"Failed to fetch page: {response.status_code}")
            
        except Exception as e:
            logging.error(f"Error capturing HTML image: {str(e)}")
        return False

    def capture_webcam(self, webcam_config, base_path):
        """Main method to capture webcam based on type"""
        try:
            # Debug logging
            logging.info(f"Capture methods available: {list(self.capture_methods.keys())}")
            logging.info(f"Webcam type received: {webcam_config['type']}")
            
            # Ensure base_path is absolute
            if not os.path.isabs(base_path):
                base_path = os.path.join(self.snapshots_dir, base_path)
            
            # Create directory if it doesn't exist
            try:
                os.makedirs(base_path, mode=0o777, exist_ok=True)
                logging.debug(f"Created/verified directory: {base_path}")
                logging.debug(f"Directory permissions: {oct(os.stat(base_path).st_mode)[-3:]}")
            except Exception as e:
                logging.error(f"Error creating directory: {str(e)}")
                return False
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{webcam_config['name'].replace(' ', '_')}_{timestamp}.jpg"
            save_path = os.path.join(base_path, filename)
            
            logging.debug(f"Full save path: {save_path}")
            
            # Verify directory is writable
            if not os.access(os.path.dirname(save_path), os.W_OK):
                logging.error(f"Directory not writable: {os.path.dirname(save_path)}")
                return False
            
            if webcam_config['type'] in self.capture_methods:
                success = self.capture_methods[webcam_config['type']](webcam_config['url'], save_path)
                if success:
                    logging.debug(f"File exists after capture: {os.path.exists(save_path)}")
                    if os.path.exists(save_path):
                        logging.debug(f"File size: {os.path.getsize(save_path)} bytes")
                        logging.debug(f"File permissions: {oct(os.stat(save_path).st_mode)[-3:]}")
                return success
            else:
                logging.error(f"Unsupported webcam type: {webcam_config['type']}")
                return False
            
        except Exception as e:
            logging.error(f"Error in capture_webcam: {str(e)}", exc_info=True)
            return False 