"""
LinkedIn Message Sending Automation
Sends personalized messages to connections with company validation
"""
import os
import time
import pyautogui
from typing import Optional, Set, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from linkedIn_follow.modules.open_chrome import driver, wait
from linkedIn_follow.modules.helpers import (
    print_lg, get_profiles_from_csv, save_seen_profiles,
    scroll_page, scroll_to_top
)
from linkedIn_follow.config.text import message_text
from linkedIn_follow.config.personals import skip_words

# Constants
CONNECTIONS_URL = "https://www.linkedin.com/mynetwork/invite-connect/connections/"
PAGE_LOAD_TIMEOUT = 3
MESSAGE_SEND_DELAY = 5
PAGE_WAIT_DELAY = 2
PROFILE_LOAD_TIMEOUT = 5
MESSAGE_RETRY_LIMIT = 3
LOAD_MORE_RETRY_LIMIT = 3
COMPANY_ATTR_PREFIX = "Current company:"
EXPERIENCE_SECTION = "Experience"


class MessageState:
    """Manages message sending state"""
    
    def __init__(self):
        self.seen_profiles: Set[str] = set()
        self.message_count = 0
        self.skipped_count = 0
        self.current_index = 0
        self.csv_profiles = get_profiles_from_csv()
        self.load_current_index()
    
    def add_seen_profile(self, profile_link: str, skipped: bool = False) -> None:
        """Mark profile as seen and save to CSV"""
        self.csv_profiles.add(profile_link)
        save_seen_profiles(profile_link)
        if skipped:
            self.skipped_count += 1
    
    def is_profile_seen(self, profile_link: str) -> bool:
        """Check if profile has already been processed"""
        return profile_link in self.csv_profiles
    
    def set_current_index(self, index: int) -> None:
        """Update current processing index and save to file"""
        self.current_index = index
        self.save_current_index()
    
    def save_current_index(self) -> None:
        """Save current index to file for resuming"""
        try:
            from linkedIn_follow.config.settings import logs_folder_path
            index_file = os.path.join(logs_folder_path, "current_message_index.txt")
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(str(self.current_index))
        except Exception as e:
            print_lg(f"Error saving current index: {e}")
    
    def load_current_index(self) -> None:
        """Load current index from file to resume from last position"""
        try:
            from linkedIn_follow.config.settings import logs_folder_path
            index_file = os.path.join(logs_folder_path, "current_message_index.txt")
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    self.current_index = int(f.read().strip())
                print_lg(f"Loaded last saved index: {self.current_index}")
            else:
                self.current_index = 0
        except Exception as e:
            print_lg(f"Error loading current index: {e}")
            self.current_index = 0
    
    def mark_message_sent(self) -> None:
        """Increment message counter"""
        self.message_count += 1
    
    def get_stats(self) -> dict:
        """Return processing statistics"""
        return {
            "messages_sent": self.message_count,
            "profiles_skipped": self.skipped_count,
            "total_processed": self.message_count + self.skipped_count
        }
    
    def reset(self) -> None:
        """Reset state for new session"""
        self.seen_profiles.clear()
        self.message_count = 0
        self.skipped_count = 0


class ProfileValidator:
    """Validates LinkedIn profiles before messaging"""
    
    @staticmethod
    def _extract_company(aria_label: str) -> Optional[str]:
        """Extract company name from aria label"""
        try:
            company = aria_label.split(COMPANY_ATTR_PREFIX)[1].split(".")[0].strip()
            return company
        except Exception:
            return None
    
    @staticmethod
    def _should_skip_company(company: str) -> bool:
        """Check if company is in skip list"""
        if not company:
            return False
        return company.lower() in skip_words
    
    @staticmethod
    def _has_experience(driver: WebDriver) -> bool:
        """Check if profile has experience section"""
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//section[.//span[text()="{EXPERIENCE_SECTION}"]]')
                ),
                timeout=3
            )
            return True
        except Exception:
            return False
    
    @staticmethod
    def _extract_company_from_experience(driver: WebDriver) -> Optional[str]:
        try:
            time.sleep(PROFILE_LOAD_TIMEOUT)
            scroll_page(driver)

            company_el = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '(//section[.//h2[normalize-space()="Experience"]] '
                    '//p[contains(text(),"·")])[1]'
                )))

            raw_text = company_el.text.strip()
            company = raw_text.split("·")[0].strip()

            print_lg(f"Extracted company from experience: {company}")
            return company

        except Exception:
            return None

    
    @staticmethod
    def validate(driver: WebDriver, profile_link: str, state: MessageState) -> bool:
        """
        Validate profile by opening in new window and checking company
        Handles 2 types of LinkedIn profile webpages:
        1. Type 1: Company button with aria-label
        2. Type 2: Experience section with company links
        Returns True if profile should be messaged
        """
        driver.execute_script("window.open(arguments[0], '_blank');", profile_link)
        driver.switch_to.window(driver.window_handles[-1])
        
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(PROFILE_LOAD_TIMEOUT)
            
            # Type 1: Try to find and check company via aria-label button
            try:
                company_btn = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//button[contains(@aria-label,"Current company:")]')
                    ),
                    timeout=3
                )
                scroll_page(driver)
                scroll_to_top(driver)
                time.sleep(PROFILE_LOAD_TIMEOUT)
                
                aria = company_btn.get_attribute("aria-label")
                company = ProfileValidator._extract_company(aria)
                
                if ProfileValidator._should_skip_company(company):
                    print_lg(f"Skipping company: {company}")
                    state.add_seen_profile(profile_link, skipped=True)
                    return False
                
                return True
                
            except Exception:
                # Type 2: Fallback - check if Experience section exists
                try:
                    wait.until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//section[.//span[text()="Experience"]]')
                        ),
                        timeout=3
                    )
                    return True
                
                except Exception:
                    # Type 2 Alt: Try alternative Experience section format
                    try:
                        company = ProfileValidator._extract_company_from_experience(driver)
                        
                        if company:
                            if ProfileValidator._should_skip_company(company):
                                print_lg(f"Skipping company: {company}")
                                state.add_seen_profile(profile_link, skipped=True)
                                return False
                            return True
                        else:
                            print_lg(f"Could not extract company from Experience section")
                            return False
                    
                    except Exception:
                        print_lg(f"No experience found on profile")
                        state.add_seen_profile(profile_link, skipped=True)
                        return False
        
        except Exception as e:
            print_lg(f"Error validating profile: {e}")
            return False
        
        finally:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])


class MessageSender:
    """Handles sending messages to connections"""
    
    @staticmethod
    def _check_skip_words(driver: WebDriver) -> bool:
        """Check if profile has skip words in title"""
        try:
            text = driver.find_element(
                By.XPATH, './/div[contains(@class,"artdeco-entity-lockup__subtitle")]'
            ).text
            
            if text and any(skip_word.strip().lower() in text.lower() for skip_word in skip_words):
                print_lg("Skipping profile based on job title")
                return True
        except Exception:
            print_lg("Could not find job title, proceeding with message")
        
        return False
    
    @staticmethod
    def _has_existing_messages(driver: WebDriver) -> bool:
        """Check if conversation already has messages"""
        try:
            driver.find_element(
                By.XPATH, './/div[contains(@class,"msg-s-message-list")]')
            return True
        except Exception:
            return False
    
    @staticmethod
    def _send_message(driver: WebDriver) -> bool:
        """Send message to connection"""
        try:
            text_input = driver.find_element(
                By.XPATH, './/div[contains(@class, "msg-form__contenteditable")]')
            text_input.click()
            text_input.send_keys(message_text)
            
            send_button = driver.find_element(
                By.XPATH, './/button[contains(@class, "msg-form__send-button")]')
            time.sleep(MESSAGE_SEND_DELAY)
            send_button.click()
            
            return True
        except Exception as e:
            print_lg(f"Could not send message: {e}")
            return False
    
    @staticmethod
    def send(driver: WebDriver, message_href: str, state: MessageState) -> bool:
        """
        Send message to connection with retry logic
        Returns True if message was sent successfully
        """
        if message_href in state.seen_profiles:
            return False
        
        state.seen_profiles.add(message_href)
        
        try:
            driver.execute_script("window.open(arguments[0], '_blank');", message_href)
            driver.switch_to.window(driver.window_handles[-1])
            
            for attempt in range(MESSAGE_RETRY_LIMIT):
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(MESSAGE_SEND_DELAY)
                    
                    if MessageSender._check_skip_words(driver):
                        return False
                    
                    if MessageSender._has_existing_messages(driver):
                        print_lg("Conversation already exists")
                        return False
                    
                    if MessageSender._send_message(driver):
                        state.mark_message_sent()
                        return True
                    
                except Exception as e:
                    if attempt < MESSAGE_RETRY_LIMIT - 1:
                        print_lg(f"Message send attempt {attempt + 1} failed, retrying...")
                        time.sleep(PAGE_WAIT_DELAY)
                    else:
                        print_lg(f"Failed to send message after {MESSAGE_RETRY_LIMIT} attempts")
                        return False
            
            return False
        
        except Exception as e:
            print_lg(f"Error in message sending: {e}")
            return False
        
        finally:
            try:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception:
                pass


class ConnectionLoader:
    """Loads and manages connections list"""
    
    @staticmethod
    def _load_more_connections(driver: WebDriver) -> bool:
        """Click load more button or scroll to bottom"""
        try:
            load_more_button = driver.find_element(
                By.XPATH, './/button[.//span[text()="Load more"]]')
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", load_more_button)
            time.sleep(1)
            load_more_button.click()
            print_lg("Clicked Load More button")
            return True
        except Exception:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            return False
    
    @staticmethod
    def load_connections(driver: WebDriver) -> List[WebElement]:
        """Load connections list with retry logic"""
        driver.get(CONNECTIONS_URL)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(PAGE_LOAD_TIMEOUT)
        
        retry = 0
        cards = []
        
        while retry < LOAD_MORE_RETRY_LIMIT:
            try:
                new_cards = driver.find_elements(
                    By.XPATH, '//div[@data-view-name="connections-list"]')
                
                if len(new_cards) > len(cards):
                    cards = new_cards
                    retry = 0
                    print_lg(f"Loaded {len(cards)} connections")
                else:
                    break
                
                ConnectionLoader._load_more_connections(driver)
                time.sleep(PAGE_WAIT_DELAY)
            
            except Exception as e:
                print_lg(f"Error loading connections: {e}")
                retry += 1
        
        return cards


def process_connections(
    driver: WebDriver,
    cards: List[WebElement],
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    message_limit: Optional[int] = None,
    state: Optional[MessageState] = None
) -> None:
    """Process connections and send messages"""
    if state is None:
        state = MessageState()
    
    # Determine range
    start = start_index if start_index is not None else state.current_index
    end = end_index if end_index is not None else len(cards)
    
    # Log appropriately based on whether we're resuming or starting
    if start_index == 0:
        print_lg(f"Starting from connection index: {start}")
    else:
        print_lg(f"Resuming from connection index: {start}")
    
    # Process cards in range
    for i, card in enumerate(cards[start:end], start=start):
        # Update and save current index
        state.set_current_index(i)
        
        if message_limit and state.message_count >= message_limit:
            print_lg(f"Reached message limit of {message_limit}")
            break
        
        try:
            profile_link = None
            message_link = None
            
            # Extract profile and message links
            profile_link = card.find_element(
                By.XPATH, './/a[@data-view-name="connections-profile"]'
            ).get_attribute("href")
            
            if state.is_profile_seen(profile_link):
                continue
            
            message_link = card.find_element(
                By.XPATH, './/div[@data-view-name="message-button"]//a[@aria-label="Message"]'
            ).get_attribute("href")
            
            # Validate profile
            if not ProfileValidator.validate(driver, profile_link, state):
                # Profile was skipped due to company or no experience
                # It's already marked as seen in validate() method
                continue
            
            # Prepare and send message
            time.sleep(PAGE_WAIT_DELAY)
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", card)
            time.sleep(PAGE_WAIT_DELAY)
            
            # Send message and mark as seen
            MessageSender.send(driver, message_link, state)
            state.add_seen_profile(profile_link)
            print_lg(f"[{i+1}] Profile processed and added to seen list: {profile_link}")
            time.sleep(PAGE_WAIT_DELAY)
        
        except Exception as e:
            print_lg(f"Error processing card {i}: {e}")
            if profile_link:
                try:
                    state.add_seen_profile(profile_link)
                    print_lg(f"Profile marked as seen due to processing error: {profile_link}")
                except Exception:
                    pass
            continue


def find_connections(
    driver: WebDriver,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    message_limit: Optional[int] = None
) -> None:
    """Main function to find and message connections"""
    state = MessageState()
    
    # If start_index is explicitly 0 from "From Start", don't load saved index
    if start_index == 0:
        state.current_index = 0
    
    try:
        cards = ConnectionLoader.load_connections(driver)
        
        if not cards:
            print_lg("No connections found")
            return
        
        print_lg(f"Processing {len(cards)} connections")
        process_connections(driver, cards, start_index, end_index, message_limit, state)
    
    except Exception as e:
        print_lg(f"Error in find_connections: {e}")
    
    finally:
        stats = state.get_stats()
        print_lg(f"Finished messaging. Sent {stats['messages_sent']} messages.")
        print_lg(f"Skipped {stats['profiles_skipped']} profiles (company in skip list or no experience).")
        print_lg(f"Total processed: {stats['total_processed']} profiles.")
        pyautogui.alert(
            f"✅ Finished messaging {stats['total_processed']} connections.\n\n"
            f"📧 Messages sent: {stats['messages_sent']}\n"
            f"⏭️ Skipped: {stats['profiles_skipped']} (company/no exp)\n"
            f"📝 All profiles added to seen list.\n"
            f"📍 Last processed index saved for resuming.",
            title="Done",
            button="OK")
        
        # Reset index after successful completion
        state.set_current_index(0)
        print_lg("Reset connection index for next session")


def set_range(driver: WebDriver) -> None:
    """Get message parameters from user and start messaging"""
    start_index = None
    end_index = None
    message_limit = None
    
    # Get starting point
    choice = pyautogui.confirm(
        "Where do you want to start?",
        buttons=["Resume Last Index", "From Start", "Specific Range", "Cancel"])
    
    if choice == "Cancel":
        return
    
    if choice == "Resume Last Index":
        # Load and use the last saved index
        state = MessageState()
        start_index = state.current_index
        pyautogui.alert(
            f"Resuming from connection index: {start_index}",
            "Resuming",
            "OK")
    
    elif choice == "From Start":
        start_index = 0
    
    elif choice == "Specific Range":
        start_input = pyautogui.prompt("Start index:", "Start")
        end_input = pyautogui.prompt("End index:", "End")
        
        if start_input and start_input.isdigit():
            start_index = int(start_input)
        if end_input and end_input.isdigit():
            end_index = int(end_input)
    
    # Get message limit
    count_input = pyautogui.prompt("Number of connections to message:", "Message Limit")
    if count_input and count_input.isdigit():
        message_limit = int(count_input)
    
    # Start messaging
    find_connections(driver, start_index, end_index, message_limit)
