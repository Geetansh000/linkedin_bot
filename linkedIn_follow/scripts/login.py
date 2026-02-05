"""
LinkedIn Login & Main Automation Script
Handles user authentication and orchestrates connection and messaging tasks
"""
import os
from typing import Optional
from dotenv import load_dotenv
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

from linkedIn_follow.modules.open_chrome import driver, wait, restart_driver
from linkedIn_follow.modules.helpers import print_lg, manual_login_retry
from linkedIn_follow.modules.clickers_and_finders import text_input_by_ID, try_xp, try_linkText, find_by_class
from linkedIn_follow.config.personals import LINKEDIN_USERNAME, LINKEDIN_PASSWORD, SEARCH_STRING
from linkedIn_follow.config.text import welcome_message_text
from linkedIn_follow.scripts import connections, message as msg_script

load_dotenv()

# Constants
LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"
LOGIN_TIMEOUT = 10
RETRY_LIMIT = 2
MAX_RECONNECT_ATTEMPTS = 3


class LinkedInAuthenticator:
    """Handles LinkedIn authentication and session management"""
    
    @staticmethod
    def is_logged_in() -> bool:
        """Check if user is already logged into LinkedIn"""
        try:
            if driver.current_url == LINKEDIN_FEED_URL:
                return True
            
            login_indicators = [
                try_linkText(driver, "Sign in"),
                try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'),
                try_linkText(driver, "Join now")
            ]
            
            return not any(login_indicators)
        except Exception as e:
            print_lg(f"Error checking login status: {e}")
            return False
    
    @staticmethod
    def login(username: str, password: str) -> bool:
        """Attempt to login to LinkedIn with provided credentials"""
        global driver
        
        try:
            driver.get(LINKEDIN_LOGIN_URL)
            
            # Already logged in
            if LinkedInAuthenticator.is_logged_in():
                print_lg("Already logged in to LinkedIn")
                return True
            
            # Validate credentials
            if not LinkedInAuthenticator._validate_credentials(username, password):
                manual_login_retry(LinkedInAuthenticator.is_logged_in, RETRY_LIMIT)
                return LinkedInAuthenticator.is_logged_in()
            
            # Fill login form
            LinkedInAuthenticator._fill_login_form(username, password)
            
            # Wait for successful login
            wait.until(EC.url_to_be(LINKEDIN_FEED_URL))
            print_lg("Login successful!")
            return True
            
        except Exception as e:
            print_lg(f"Login failed: {e}")
            manual_login_retry(LinkedInAuthenticator.is_logged_in, RETRY_LIMIT)
            return LinkedInAuthenticator.is_logged_in()
    
    @staticmethod
    def _validate_credentials(username: str, password: str) -> bool:
        """Validate that credentials are not default placeholders"""
        if username == "username@example.com" or password == "example_password":
            pyautogui.alert(
                "Please configure LINKEDIN_USERNAME and LINKEDIN_PASSWORD in .env file",
                "Missing Credentials", "OK")
            print_lg("Credentials not configured in .env file")
            return False
        return True
    
    @staticmethod
    def _fill_login_form(username: str, password: str) -> None:
        """Fill in the LinkedIn login form"""
        try:
            wait.until(EC.presence_of_element_located(
                (By.LINK_TEXT, "Forgot password?")))
            
            try:
                text_input_by_ID(driver, "username", username, 1)
            except Exception:
                print_lg("Username field not found")
            
            try:
                text_input_by_ID(driver, "password", password, 1)
            except Exception:
                print_lg("Password field not found")
            
            # Submit login form
            login_button = driver.find_element(
                By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]')
            login_button.click()
            
        except Exception as e:
            print_lg(f"Error filling login form: {e}")
            # Try alternative login method
            try:
                profile_button = find_by_class(driver, "profile__details")
                profile_button.click()
            except Exception:
                print_lg("Could not initiate login")


class LinkedInAutomationController:
    """Main controller for LinkedIn automation workflow"""
    
    @staticmethod
    def get_user_action() -> Optional[str]:
        """Prompt user to choose an action"""
        choice = pyautogui.confirm(
            "What would you like to do?",
            buttons=["Search & Add Connections", "Send Messages", "Exit"])
        return choice
    
    @staticmethod
    def execute_connection_search(driver: WebDriver) -> None:
        """Execute connection search and send requests"""
        page_count = pyautogui.prompt(
            "How many pages to search? (Leave blank for unlimited)",
            "Search Parameters")
        
        page_limit = None
        if page_count and page_count.isdigit():
            page_limit = int(page_count)
        
        connection_count = connections.search_and_add_connections(driver, 1, page_limit)
        
        pyautogui.alert(
            f"Added {connection_count} connections for '{SEARCH_STRING}'",
            "Search Complete",
            "OK")
    
    @staticmethod
    def execute_messaging(driver: WebDriver) -> None:
        """Execute message sending to connections"""
        print_lg("Starting message sending process...")
        msg_script.set_range(driver)
    
    @staticmethod
    def handle_action(driver: WebDriver, action: str) -> bool:
        """Handle user action selection. Returns True if should continue."""
        if action == "Search & Add Connections":
            try:
                LinkedInAutomationController.execute_connection_search(driver)
            except Exception as e:
                print_lg(f"Error during connection search: {e}")
                pyautogui.alert("Error during search. Please try again.", "Error", "OK")
            return True
            
        elif action == "Send Messages":
            try:
                LinkedInAutomationController.execute_messaging(driver)
            except Exception as e:
                print_lg(f"Error during messaging: {e}")
                pyautogui.alert("Error during messaging. Please try again.", "Error", "OK")
            return True
            
        elif action == "Exit":
            return False
        
        return True
    
    @staticmethod
    def handle_continuation(driver: WebDriver) -> bool:
        """Ask user if they want to continue or exit. Returns True if continue."""
        choice = pyautogui.confirm(
            "Continue with more actions?",
            buttons=["Yes", "No"])
        
        if choice == "Yes":
            try:
                driver.get(LINKEDIN_FEED_URL)
            except Exception:
                print_lg("Reconnecting to LinkedIn...")
                try:
                    restart_driver()
                except Exception as e:
                    print_lg(f"Failed to reconnect: {e}")
                    return False
            return True
        else:
            return False
    
    @staticmethod
    def shutdown(driver: WebDriver) -> None:
        """Gracefully close browser and show completion message"""
        try:
            driver.quit()
        except Exception:
            pass
        
        pyautogui.alert(
            welcome_message_text,
            "Automation Complete ✅",
            "Awesome!")


def validate_environment() -> tuple[Optional[str], Optional[str]]:
    """Validate environment variables and return credentials"""
    email = os.getenv("LINKEDIN_EMAIL") or os.getenv("LINKEDIN_USERNAME")
    password = os.getenv("LINKEDIN_PASSWORD")
    
    if not email or not password:
        error_msg = "Please set LINKEDIN_EMAIL/LINKEDIN_USERNAME and LINKEDIN_PASSWORD in .env file"
        print_lg(error_msg)
        pyautogui.alert(error_msg, "Configuration Error", "OK")
        return None, None
    
    return email, password


def main() -> None:
    """Main entry point for LinkedIn automation"""
    global driver
    
    try:
        # Validate environment
        email, password = validate_environment()
        if not email or not password:
            return
        
        # Authenticate
        print_lg("Attempting to login to LinkedIn...")
        if not LinkedInAuthenticator.login(email, password):
            print_lg("Failed to authenticate. Exiting.")
            return
        
        # Main automation loop
        while True:
            action = LinkedInAutomationController.get_user_action()
            if not action:
                break
            
            if not LinkedInAutomationController.handle_action(driver, action):
                break
            
            if not LinkedInAutomationController.handle_continuation(driver):
                break
        
    except KeyboardInterrupt:
        print_lg("Automation interrupted by user")
    except Exception as e:
        print_lg(f"Critical error in automation: {e}")
        pyautogui.alert(f"An error occurred: {e}", "Error", "OK")
    finally:
        LinkedInAutomationController.shutdown(driver)


if __name__ == "__main__":
    main()
