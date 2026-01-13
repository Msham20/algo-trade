"""
Authentication module for Zerodha login with email and phone number
"""
import pyotp
from kiteconnect import KiteConnect
import logging
import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from config import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL))
logger = logging.getLogger(__name__)

TOKEN_FILE = "zerodha_token.json"

class ZerodhaAuth:
    """Handle Zerodha authentication with email/phone and TOTP"""
    
    def __init__(self):
        self.api_key = Config.ZERODHA_API_KEY
        self.api_secret = Config.ZERODHA_API_SECRET
        self.user_id = Config.ZERODHA_USER_ID
        self.password = Config.ZERODHA_PASSWORD
        self.totp_secret = Config.ZERODHA_TOTP_SECRET
        self.kite = None
        self.access_token = None
        self._load_token()
        
    def login(self):
        """
        Login to Zerodha using email/phone and password with TOTP
        Returns KiteConnect instance if successful
        """
        try:
            # Initialize KiteConnect
            self.kite = KiteConnect(api_key=self.api_key)
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret)
            totp_token = totp.now()
            
            # Request access token
            data = self.kite.generate_session(
                request_token=None,  # Will be obtained via login
                api_secret=self.api_secret
            )
            
            # If we need to login first (for first time setup)
            # This requires manual login flow or selenium automation
            logger.info("Attempting to login to Zerodha...")
            
            # For automated login, we need request_token
            # This is typically obtained via browser login flow
            # For production, use selenium or manual login to get request_token
            
            return self.kite
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    def login_with_request_token(self, request_token):
        """
        Complete login using request token obtained from browser
        """
        try:
            self.kite = KiteConnect(api_key=self.api_key)
            data = self.kite.generate_session(
                request_token=request_token,
                api_secret=self.api_secret
            )
            
            self.access_token = data['access_token']
            self.kite.set_access_token(self.access_token)
            
            # Save token for future use
            self._save_token(self.access_token)
            
            logger.info("Successfully logged in to Zerodha")
            return self.kite
            
        except Exception as e:
            logger.error(f"Login with request token failed: {str(e)}")
            raise
    
    def get_login_url(self):
        """
        Get the login URL for manual authentication
        Returns URL that user needs to visit
        """
        if not self.kite:
            self.kite = KiteConnect(api_key=self.api_key)
        
        login_url = self.kite.login_url()
        return login_url
    
    def is_authenticated(self):
        """Check if currently authenticated"""
        try:
            if self.kite and self.access_token:
                # Try to get profile to verify authentication
                profile = self.kite.profile()
                return True
        except:
            return False
        return False
    
    def get_kite_instance(self):
        """Get authenticated KiteConnect instance"""
        if not self.is_authenticated():
            raise Exception("Not authenticated. Please login first.")
        return self.kite
    
    def _save_token(self, access_token):
        """Save access token to file"""
        try:
            token_data = {
                'access_token': access_token,
                'api_key': self.api_key
            }
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f)
            logger.info("Access token saved")
        except Exception as e:
            logger.warning(f"Failed to save token: {str(e)}")
    
    def _load_token(self):
        """Load access token from file"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                    if token_data.get('api_key') == self.api_key:
                        self.access_token = token_data.get('access_token')
                        if self.access_token:
                            self.kite = KiteConnect(api_key=self.api_key)
                            self.kite.set_access_token(self.access_token)
                            logger.info("Access token loaded from file")
        except Exception as e:
            logger.warning(f"Failed to load token: {str(e)}")
    
    def clear_token(self):
        """Clear saved token"""
        try:
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            self.access_token = None
            self.kite = None
            logger.info("Token cleared")
        except Exception as e:
            logger.warning(f"Failed to clear token: {str(e)}")
    
    def automated_login(self):
        """
        Fully automated login using Selenium
        This method automatically logs in to Zerodha and gets all permissions
        """
        try:
            logger.info("Starting automated login to Zerodha...")
            
            # Initialize KiteConnect
            self.kite = KiteConnect(api_key=self.api_key)
            login_url = self.kite.login_url()
            
            # Setup Chrome driver
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            # Initialize driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                logger.info("Opening Zerodha login page...")
                driver.get(login_url)
                time.sleep(3)
                
                # Enter user ID
                logger.info("Entering user ID...")
                user_id_input = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "userid"))
                )
                user_id_input.clear()
                user_id_input.send_keys(self.user_id)
                
                # Enter password
                logger.info("Entering password...")
                password_input = driver.find_element(By.ID, "password")
                password_input.clear()
                password_input.send_keys(self.password)
                
                # Click login button
                logger.info("Clicking login button...")
                login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                time.sleep(3)
                
                # Enter TOTP
                logger.info("Entering TOTP...")
                totp = pyotp.TOTP(self.totp_secret)
                totp_token = totp.now()
                
                totp_input = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, "totp"))
                )
                totp_input.clear()
                totp_input.send_keys(totp_token)
                
                # Click verify button
                verify_button = driver.find_element(By.XPATH, "//button[@type='submit']")
                verify_button.click()
                time.sleep(5)
                
                # Extract request token from URL
                current_url = driver.current_url
                logger.info(f"Current URL: {current_url}")
                
                # Extract request_token from URL
                match = re.search(r'request_token=([^&]+)', current_url)
                if match:
                    request_token = match.group(1)
                    logger.info(f"Request token extracted: {request_token[:20]}...")
                    
                    # Complete authentication
                    logger.info("Completing authentication...")
                    kite = self.login_with_request_token(request_token)
                    
                    logger.info("✅ Automated login successful!")
                    return kite
                else:
                    # Check if already authenticated (token might be in URL or page)
                    if 'status=success' in current_url or 'dashboard' in current_url.lower():
                        # Try to get token from page or cookies
                        logger.info("Login successful, extracting token...")
                        # Get request token from redirect URL
                        time.sleep(2)
                        final_url = driver.current_url
                        match = re.search(r'request_token=([^&]+)', final_url)
                        if match:
                            request_token = match.group(1)
                            kite = self.login_with_request_token(request_token)
                            return kite
                    
                    raise Exception("Could not extract request token from URL")
                    
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Automated login failed: {str(e)}")
            logger.info("Falling back to manual login method...")
            raise
    
    def ensure_authenticated(self):
        """
        Ensure authentication is valid, re-authenticate if needed
        This is called automatically before trading operations
        """
        try:
            if self.is_authenticated():
                logger.info("Already authenticated")
                return True
            else:
                logger.info("Not authenticated, attempting automated login...")
                self.automated_login()
                return self.is_authenticated()
        except Exception as e:
            logger.error(f"Authentication check failed: {str(e)}")
            return False