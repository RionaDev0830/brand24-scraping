from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, WebDriverException
from dotenv import load_dotenv
import os
import time
import sys
import platform
import subprocess
import json
import urllib.request
import zipfile
import io
import shutil
import ssl
import certifi
from urllib3.exceptions import MaxRetryError
import socket

class Brand24Scraper:
    def __init__(self):
        self.url = "https://app.brand24.com/panel/results/1397059472?p=1&or=0&cdt=days&dr=4&va=1&d1=2025-05-03&d2=2025-06-02"
        self.setup_driver()
        load_dotenv()
        self.email = os.getenv('BRAND24_EMAIL')
        self.password = os.getenv('BRAND24_PASSWORD')
        self.target_url = "https://app.brand24.com/panel/results/1397059472?p=1&or=0&cdt=days&dr=4&va=1&d1=2025-05-03&d2=2025-06-02"

    def get_chrome_version(self):
        """Get the installed Chrome version."""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version = winreg.QueryValueEx(key, "version")[0]
            return version
        except Exception as e:
            print(f"Could not determine Chrome version: {str(e)}")
            return None

    def download_chromedriver(self, version):
        """Download the appropriate ChromeDriver version."""
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Get the major version number
                major_version = version.split('.')[0]
                
                # Create a custom SSL context
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                
                # Get the latest ChromeDriver version for this Chrome version
                url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
                
                # Create a custom opener with SSL context
                opener = urllib.request.build_opener(
                    urllib.request.HTTPSHandler(context=ssl_context)
                )
                urllib.request.install_opener(opener)
                
                # Add headers to mimic a browser request
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
                }
                
                request = urllib.request.Request(url, headers=headers)
                response = urllib.request.urlopen(request, timeout=60)  # Increased timeout
                data = json.loads(response.read())
                
                # Find the matching version
                matching_version = None
                for version_info in data['versions']:
                    if version_info['version'].startswith(f"{major_version}."):
                        matching_version = version_info
                        break
                
                if not matching_version:
                    raise Exception(f"Could not find ChromeDriver for Chrome version {version}")
                
                # Get the download URL for Windows
                download_url = None
                for download in matching_version['downloads']['chromedriver']:
                    if download['platform'] == 'win64':
                        download_url = download['url']
                        break
                
                if not download_url:
                    raise Exception("Could not find Windows ChromeDriver download URL")
                
                # Download and extract ChromeDriver
                print(f"Downloading ChromeDriver {matching_version['version']}...")
                request = urllib.request.Request(download_url, headers=headers)
                response = urllib.request.urlopen(request, timeout=60)  # Increased timeout
                zip_data = io.BytesIO(response.read())
                
                with zipfile.ZipFile(zip_data) as zip_file:
                    # Extract chromedriver.exe
                    for file in zip_file.namelist():
                        if file.endswith('chromedriver.exe'):
                            with zip_file.open(file) as source, open('chromedriver.exe', 'wb') as target:
                                shutil.copyfileobj(source, target)
                                break
                
                print("ChromeDriver downloaded successfully!")
                return os.path.abspath('chromedriver.exe')
                
            except (TimeoutException, WebDriverException, MaxRetryError, socket.timeout) as e:
                if attempt < max_retries - 1:
                    print(f"Download attempt {attempt + 1} failed: {str(e)}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Error downloading ChromeDriver after {max_retries} attempts: {str(e)}")
                    raise
            except Exception as e:
                print(f"Error downloading ChromeDriver: {str(e)}")
                raise

    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        try:
            print("Setting up Chrome WebDriver...")
            print(f"Python version: {sys.version}")
            print(f"Platform: {platform.platform()}")
            print(f"Architecture: {platform.architecture()}")
            
            chrome_version = self.get_chrome_version()
            print(f"Chrome version: {chrome_version}")
            
            if not chrome_version:
                raise Exception("Could not determine Chrome version")
            
            # Download the appropriate ChromeDriver
            chromedriver_path = self.download_chromedriver(chrome_version)
            
            chrome_options = Options()
            # Enable headless mode
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add proxy settings if needed
            # chrome_options.add_argument('--proxy-server=http://your-proxy:port')
            
            service = Service(executable_path=chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(60)  # Increased timeout
            
            # Create wait object with longer timeout
            self.wait = WebDriverWait(self.driver, 30)  # Increased timeout
            
            print("WebDriver setup successful!")
            
        except Exception as e:
            print(f"Error setting up WebDriver: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Make sure Chrome browser is installed and up to date")
            print("2. Try running these commands:")
            print("   pip uninstall selenium")
            print("   pip install selenium==4.18.1 certifi")
            print("3. If you're behind a proxy, uncomment and configure the proxy settings in the code")
            print("4. If the issue persists, try manually downloading ChromeDriver from:")
            print("   https://googlechromelabs.github.io/chrome-for-testing/")
            raise

    def wait_for_element(self, by, value, timeout=30, retries=3):
        """Wait for an element to be present and visible with retry logic."""
        for attempt in range(retries):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                # Add a small delay after finding the element
                time.sleep(0.5)
                return element
            except TimeoutException:
                if attempt < retries - 1:
                    print(f"Attempt {attempt + 1} to find element {value} timed out. Retrying...")
                    time.sleep(5)  # Wait before retrying
                else:
                    print(f"Timeout waiting for element: {value} after {retries} attempts")
                    return None

    def login(self):
        try:
            # First, navigate to the target URL
            print("Navigating to target URL...")
            self.driver.get(self.target_url)
            time.sleep(10)  # Increased initial wait time
            
            # Check if we're on the login page
            current_url = self.driver.current_url
            print(f"Current URL: {current_url}")
            
            if "login" in current_url.lower():
                print("Redirected to login page, waiting for page to fully load...")
                time.sleep(5)  # Additional wait for page load
                
                # Wait for and fill in email using exact selector
                print("Looking for email field...")
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "login"))
                )
                print("Found email field")
                email_field.clear()
                time.sleep(1)
                email_field.send_keys(self.email)
                time.sleep(1)
                
                # Wait for and fill in password using exact selector
                print("Looking for password field...")
                password_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                print("Found password field")
                password_field.clear()
                time.sleep(1)
                password_field.send_keys(self.password)
                time.sleep(1)
                
                # Find and click the login button using exact selector
                print("Looking for login button...")
                login_button = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "login_button"))
                )
                print("Found login button")
                
                # Click login button
                print("Clicking login button...")
                login_button.click()
                
                # Wait for redirect to complete with increased timeout
                print("Waiting for redirect and page load...")
                time.sleep(15)  # Increased wait time after login
                
                # Wait for the page to be fully loaded
                try:
                    # Wait for the page to be in a ready state
                    self.wait.until(
                        lambda driver: driver.execute_script('return document.readyState') == 'complete'
                    )
                    print("Page is fully loaded")
                except TimeoutException:
                    print("Warning: Page load timeout, but continuing...")
                
                # Additional wait to ensure all dynamic content is loaded
                time.sleep(5)
                
                # Check if we've been redirected back to the target URL
                current_url = self.driver.current_url
                print(f"Current URL after login attempt: {current_url}")
                
                # Extract base URL and main parameters for comparison
                def normalize_url(url):
                    # Remove protocol and domain
                    path = url.split('//')[-1].split('/', 1)[-1]
                    # Split into base path and parameters
                    base_path = path.split('?')[0]
                    params = path.split('?')[1] if '?' in path else ''
                    # Sort parameters for consistent comparison
                    if params:
                        param_dict = dict(param.split('=') for param in params.split('&'))
                        # Remove dr parameter as it can vary
                        param_dict.pop('dr', None)
                        # Reconstruct sorted parameters
                        sorted_params = '&'.join(f"{k}={v}" for k, v in sorted(param_dict.items()))
                        return f"{base_path}?{sorted_params}"
                    return base_path

                target_normalized = normalize_url(self.target_url)
                current_normalized = normalize_url(current_url)
                
                print(f"Normalized target URL: {target_normalized}")
                print(f"Normalized current URL: {current_normalized}")
                
                if target_normalized == current_normalized:
                    print("Login successful! Redirected to target page.")
                    return True
                else:
                    print(f"Login may have failed. URL mismatch.")
                    print(f"Target URL: {target_normalized}")
                    print(f"Current URL: {current_normalized}")
                    return False
            else:
                # If we're already on the target page, we might be logged in
                if normalize_url(self.target_url) == normalize_url(current_url):
                    print("Already logged in and on target page.")
                    return True
                else:
                    print(f"Unexpected URL after initial navigation: {current_url}")
                    return False
                
        except TimeoutException as e:
            print(f"Timeout while waiting for elements: {str(e)}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("login_error.png")
                print("Screenshot saved as 'login_error.png'")
            except:
                pass
            return False
        except Exception as e:
            print(f"Error during login: {str(e)}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("login_error.png")
                print("Screenshot saved as 'login_error.png'")
            except:
                pass
            return False

    def scrape_data(self):
        """Scrape the data from all pages and create a JSON file."""
        try:
            print("Starting to scrape data...")
            # Wait for the content to be loaded
            time.sleep(10)  # Increased initial wait time
            
            # Initialize list to store all results
            all_results = []
            current_page = 1
            
            while True:
                print(f"Scraping page {current_page}...")
                
                # Wait for the content to be fully loaded
                try:
                    # Wait for the main content container
                    self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "sc-hWdGLs"))
                    )
                    # Additional wait to ensure all dynamic content is loaded
                    time.sleep(5)
                except TimeoutException:
                    print("Timeout waiting for content to load")
                    continue
                
                # Find all divs with the specified class
                content_divs = self.driver.find_elements(By.CLASS_NAME, "sc-hWdGLs")
                print(f"Found {len(content_divs)} content divs on page {current_page}")
                
                if len(content_divs) == 0:
                    print("No content found on page, retrying...")
                    time.sleep(5)
                    continue
                
                # Process each div
                for div in content_divs:
                    try:
                        # Wait for the div to be fully loaded
                        self.wait.until(
                            EC.presence_of_element_located((By.TAG_NAME, "header"))
                        )
                        
                        # Find the header and img within the div
                        header = div.find_element(By.TAG_NAME, "header")
                        
                        # Find the avatar div and its image
                        avatar_div = header.find_element(By.CLASS_NAME, "sc-kAuIVs")
                        avatar_img = avatar_div.find_element(By.TAG_NAME, "img")
                        avatar_src = avatar_img.get_attribute("src")
                        
                        # Find the visited status image
                        try:
                            img = header.find_element(By.TAG_NAME, "img")
                            img_class = img.get_attribute("class")
                            visited_status = "yes" if "kYnewM" in img_class else "no"
                        except NoSuchElementException:
                            visited_status = "no"
                        
                        # Find the segment text
                        try:
                            segment_div = div.find_element(By.CLASS_NAME, "sc-gInZnl")
                            segment_span = segment_div.find_element(By.TAG_NAME, "span")
                            segment_text = segment_span.text
                        except NoSuchElementException:
                            segment_text = ""
                        
                        # Find the mention text
                        try:
                            mention_div = div.find_element(By.CLASS_NAME, "sc-eAeVAz")
                            mention_container = mention_div.find_element(By.CLASS_NAME, "sc-jccYHG")
                            mention_li = mention_container.find_element(By.TAG_NAME, "li")
                            mention_text = mention_li.text
                        except NoSuchElementException:
                            mention_text = ""
                        
                        # Find the post date
                        try:
                            post_date_div = mention_div.find_element(By.CLASS_NAME, "sc-hgRfpC")
                            post_date_li = post_date_div.find_element(By.TAG_NAME, "li")
                            post_date = post_date_li.text
                        except NoSuchElementException:
                            post_date = ""
                        
                        # Initialize views and influence_score as empty strings
                        views = ""
                        influence_score = ""
                        
                        # Try to find and get views
                        try:
                            views_div = div.find_element(By.XPATH, ".//div[@aria-label='Número mensual de visitas in situ']")
                            views = views_div.text
                        except NoSuchElementException:
                            pass
                        
                        # Try to find and get influence score
                        try:
                            influence_div = div.find_element(By.CLASS_NAME, "sc-nTrUm")
                            influence_text = influence_div.text
                            # Extract only the score part (e.g., "3/10" from "Influence Score: 3/10")
                            if "Influence Score:" in influence_text:
                                influence_score = influence_text.split("Influence Score:")[1].strip()
                            else:
                                influence_score = influence_text
                        except NoSuchElementException:
                            pass
                        
                        # Initialize title, mention_url, and content as empty strings
                        title = ""
                        mention_url = ""
                        content = ""
                        
                        # Try to find and get title from span
                        try:
                            title_div = div.find_element(By.CLASS_NAME, "sc-jephDI")
                            title_span = title_div.find_element(By.TAG_NAME, "span")
                            title = title_span.text
                        except NoSuchElementException:
                            pass
                        
                        # Try to find and get mention_url and content
                        try:
                            content_div = div.find_element(By.CLASS_NAME, "sc-eJKXev")
                            # Get the mention_url from a tag's href
                            mention_link = content_div.find_element(By.TAG_NAME, "a")
                            mention_url = mention_link.get_attribute("href")
                            # Get the content from p tag
                            content_p = content_div.find_element(By.TAG_NAME, "p")
                            content = content_p.text
                        except NoSuchElementException:
                            pass
                        
                        # Add to results with all collected data
                        all_results.append({
                            "visite": visited_status,
                            "avatar_img": avatar_src,
                            "segment": segment_text,
                            "mention": mention_text,
                            "post_date": post_date,
                            "views": views,
                            "influence_score": influence_score,
                            "title": title,
                            "mention_url": mention_url,
                            "content": content
                        })
                        
                    except NoSuchElementException:
                        continue
                
                # Check for next page
                try:
                    # Find the pagination element
                    pagination = self.driver.find_element(By.CLASS_NAME, "sc-bwsPYA")
                    # Find the next page button
                    next_button = pagination.find_element(By.XPATH, ".//button[@aria-label='Go to next page']")
                    
                    # Check if next button is disabled (no more pages)
                    if "Mui-disabled" in next_button.get_attribute("class"):
                        print("No more pages to scrape")
                        break
                    
                    # Click next page
                    next_button.click()
                    time.sleep(10)  # Increased wait time after clicking next page
                    current_page += 1
                    
                except NoSuchElementException:
                    print("No pagination found or reached last page")
                    break
            
            # Save results to JSON file
            print(f"Saving {len(all_results)} total results to JSON file...")
            with open("scraped_data.json", "w", encoding="utf-8") as f:
                json.dump(all_results, f, indent=2)
            
            print("Data successfully saved to scraped_data.json")
            return True
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot("scraping_error.png")
                print("Screenshot saved as 'scraping_error.png'")
            except:
                pass
            return False

    def close(self):
        """Close the browser."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing browser: {str(e)}")
        
        # Clean up chromedriver.exe
        try:
            if os.path.exists('chromedriver.exe'):
                os.remove('chromedriver.exe')
        except Exception as e:
            print(f"Error cleaning up ChromeDriver: {str(e)}")

def main():
    scraper = None
    try:
        scraper = Brand24Scraper()
        if scraper.login():
            print("Successfully logged in to Brand24")
            # Scrape the data
            if scraper.scrape_data():
                print("Successfully scraped data")
            else:
                print("Failed to scrape data")
        else:
            print("Failed to log in to Brand24")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main() 