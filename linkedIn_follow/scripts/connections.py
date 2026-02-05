"""
LinkedIn Connection Search & Request Automation
Searches for users and sends connection requests
"""
import time
import pyautogui
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from linkedIn_follow.modules.open_chrome import driver, wait, restart_driver
from linkedIn_follow.modules.helpers import print_lg
from linkedIn_follow.config.personals import SEARCH_STRING

# Constants
CONNECT_BUTTON_XPATH = './/button[.//span[text()="Connect"]]'
CONNECT_LINK_XPATH = './/a[.//span[text()="Connect"]]'
ALT_CONNECT_XPATH = '//button[contains(@aria-label, "to connect")]'
CONNECTION_DIALOG_SELECTOR = '[role="dialog"] button'
PRIMARY_BUTTON_SELECTOR = 'button.artdeco-button--primary'
PAGE_LOAD_TIMEOUT = 2
BUTTON_CLICK_DELAY = 0.5
KEYBOARD_ACTION_DELAY = 0.2
DIALOG_DISMISS_DELAY = 3
BUTTON_SUBMIT_DELAY = 1.5
MAX_RETRY_ATTEMPTS = 3
RECONNECT_DELAY = 5


class ConnectionRequestHandler:
    """Handles sending connection requests via keyboard automation"""
    
    @staticmethod
    def _focus_dialog() -> None:
        """Focus on the connection dialog"""
        driver.execute_script(f"""
        const el = document.querySelector('{CONNECTION_DIALOG_SELECTOR}') ||
                   document.querySelector('{PRIMARY_BUTTON_SELECTOR}');
        if (el) el.focus();
        """)
    
    @staticmethod
    def send_without_note_standard() -> None:
        """Send connection request without note (standard flow)"""
        try:
            ConnectionRequestHandler._focus_dialog()
            time.sleep(KEYBOARD_ACTION_DELAY)
            
            for _ in range(3):
                driver.switch_to.active_element.send_keys(Keys.TAB)
            
            time.sleep(DIALOG_DISMISS_DELAY)
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(BUTTON_SUBMIT_DELAY)
        except Exception as e:
            print_lg(f"Error in standard connection flow: {e}")
    
    @staticmethod
    def send_without_note_simplified() -> None:
        """Send connection request without note (simplified flow)"""
        try:
            ConnectionRequestHandler._focus_dialog()
            time.sleep(KEYBOARD_ACTION_DELAY)
            
            driver.switch_to.active_element.send_keys(Keys.TAB)
            driver.switch_to.active_element.send_keys(Keys.TAB)
            
            time.sleep(DIALOG_DISMISS_DELAY)
            driver.switch_to.active_element.send_keys(Keys.ENTER)
            time.sleep(BUTTON_SUBMIT_DELAY)
        except Exception as e:
            print_lg(f"Error in simplified connection flow: {e}")


class ProfileConnector:
    """Handles connecting to profiles found on search results"""
    
    @staticmethod
    def _find_connect_button(profile_div: WebElement) -> WebElement:
        """Find connect button within a profile div"""
        try:
            return profile_div.find_element(By.XPATH, CONNECT_BUTTON_XPATH)
        except Exception:
            try:
                return profile_div.find_element(By.XPATH, CONNECT_LINK_XPATH)
            except Exception:
                return None
    
    @staticmethod
    def _is_button_ready(button: WebElement) -> bool:
        """Check if button is displayed and enabled"""
        try:
            return button and button.is_displayed() and button.is_enabled()
        except Exception:
            return False
    
    @staticmethod
    def _click_button(button: WebElement) -> bool:
        """Click button with fallback to JavaScript click"""
        try:
            button.click()
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", button)
                return True
            except Exception:
                return False
    
    @staticmethod
    def process_profile(profile_div: WebElement) -> bool:
        """Process a single profile and send connection request"""
        try:
            connect_btn = ProfileConnector._find_connect_button(profile_div)
            if not connect_btn:
                return False
            
            # Scroll button into view
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", connect_btn)
            time.sleep(BUTTON_CLICK_DELAY)
            
            # Check if button is ready
            if not ProfileConnector._is_button_ready(connect_btn):
                return False
            
            # Click button
            if not ProfileConnector._click_button(connect_btn):
                return False
            
            # Send request without note
            ConnectionRequestHandler.send_without_note_standard()
            return True
            
        except Exception as e:
            print_lg(f"Error processing profile: {e}")
            return False
    
    @staticmethod
    def process_profiles(profile_divs: List[WebElement]) -> int:
        """Process multiple profiles and return count of successful requests"""
        count = 0
        for div in profile_divs:
            try:
                if ProfileConnector.process_profile(div):
                    count += 1
            except Exception as e:
                print_lg(f"Error with profile: {e}")
                continue
        return count
    
    @staticmethod
    def process_alt_buttons(buttons: List[WebElement]) -> int:
        """Process alternative connect buttons"""
        count = 0
        for btn in buttons:
            try:
                if "connect" not in btn.text.lower():
                    continue
                
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", btn)
                time.sleep(BUTTON_CLICK_DELAY)
                
                if not ProfileConnector._is_button_ready(btn):
                    continue
                
                if ProfileConnector._click_button(btn):
                    ConnectionRequestHandler.send_without_note_simplified()
                    count += 1
                    
            except Exception as e:
                print_lg(f"Error with alternative button: {e}")
                continue
        
        return count


def search_and_add_connections(driver: WebDriver, page: int = 1, end_page: int = None) -> int:
    """
    Search for profiles and send connection requests
    
    Args:
        driver: Selenium WebDriver instance
        page: Starting page number
        end_page: Ending page number (None for unlimited)
    
    Returns:
        Total number of connection requests sent
    """
    connection_count = 0
    print_lg(f"Starting connection search for '{SEARCH_STRING}' from page {page}")
    
    try:
        while end_page is None or page <= end_page:
            retry_count = 0
            
            while retry_count < MAX_RETRY_ATTEMPTS:
                try:
                    # Verify driver is still active
                    try:
                        _ = driver.current_url
                    except Exception as e:
                        print_lg(f"Driver connection lost, attempting reconnect...")
                        try:
                            restart_driver()
                            time.sleep(RECONNECT_DELAY)
                        except Exception as reconnect_e:
                            print_lg(f"Failed to reconnect: {reconnect_e}")
                            raise
                    
                    # Build search URL
                    search_url = (
                        f"https://www.linkedin.com/search/results/people/"
                        f"?keywords={SEARCH_STRING.replace(' ', '%20')}&page={page}"
                    )
                    driver.get(search_url)
                    
                    # Wait for page load
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(PAGE_LOAD_TIMEOUT)
                    
                    # Find profiles
                    profile_divs = driver.find_elements(
                        By.XPATH, '//div[@data-view-name="edge-creation-connect-action"]')
                    
                    if profile_divs:
                        print_lg(f"Found {len(profile_divs)} profiles on page {page}")
                        connection_count += ProfileConnector.process_profiles(profile_divs)
                    else:
                        # Try alternative method
                        alt_buttons = driver.find_elements(By.XPATH, ALT_CONNECT_XPATH)
                        if alt_buttons:
                            print_lg(f"Found {len(alt_buttons)} profiles (alt method) on page {page}")
                            connection_count += ProfileConnector.process_alt_buttons(alt_buttons)
                        else:
                            print_lg(f"No profiles found on page {page}")
                    
                    page += 1
                    time.sleep(PAGE_LOAD_TIMEOUT + 1)  # Extra delay between pages
                    break  # Successfully processed page, exit retry loop
                    
                except Exception as e:
                    retry_count += 1
                    print_lg(f"Error processing page {page} (attempt {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
                    
                    if retry_count < MAX_RETRY_ATTEMPTS:
                        time.sleep(RECONNECT_DELAY)
                    else:
                        print_lg(f"Max retries exceeded for page {page}, moving to next page")
                        page += 1
                        break
    
    except Exception as e:
        print_lg(f"Error in connection search: {e}")
    
    # Ask if user wants to continue
    if end_page is None:
        choice = pyautogui.confirm(
            "Continue searching for more connections?",
            buttons=["Yes", "No"])
        
        if choice == "Yes":
            more_pages = pyautogui.prompt(
                "How many more pages to search?",
                "Additional Pages")
            
            if more_pages and more_pages.isdigit():
                more_count = int(more_pages)
                if more_count > 0:
                    return connection_count + search_and_add_connections(
                        driver, page, page + more_count - 1)
    
    return connection_count
