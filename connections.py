from message import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import os
from dotenv import load_dotenv
import pyautogui
from selenium.webdriver.common.keys import Keys
import time
from config.personals import SEARCH_STRING
from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
import time
# Load environment variables from .env file
load_dotenv()


def send_without_note_keyboard(driver):

    driver.execute_script("""
    const el =
      document.querySelector('[role="dialog"] button') ||
      document.querySelector('button.artdeco-button--primary');
    if (el) el.focus();
    """)

    time.sleep(0.2)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    time.sleep(1.5)


def find_connections(driver: WebDriver):
    search_url = "https://www.linkedin.com/mynetwork/invite-connect/connections/"
    print_lg("Navigating to Connections page...", driver)
    driver.get(search_url)

    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(3)
    retry = old_length = 0
    cards = []
    while retry < 3:
        try:
            # ✅ get actual connection cards
            old_length = len(cards)  # Store the length of the previous cards
            cards = driver.find_elements(
                By.XPATH,
                '//div[@data-view-name="connections-list"]'
            )
            print_lg(f"Total connections found so far: {len(cards)}")
            if len(cards) > old_length:
                retry = 0  # Reset retry if new cards are found
            elif len(cards) == old_length and len(cards) > 0:
                break  # Exit if no new cards are found
            # Process only new cards
            if connection_start is not None or connection_end is not None:
                start = old_length
                end = len(cards)
                if connection_start is not None:
                    if connection_start >= len(cards):
                        scroll_to_bottom(driver)
                        continue
                    start = old_length if connection_start < old_length else connection_start
                end = connection_end if connection_end is not None and connection_end <= len(
                    cards) else len(cards)
                print_lg(
                    f"Processing connections from {start} to {end} {len(cards)}")
                check_profile(driver, cards[start:end])
                if connection_end is not None and connection_end < len(cards):
                    break  # Exit if we've reached the end
            else:
                check_profile(driver, cards[old_length:])
            # Scroll to the bottom to load all connections
            scroll_to_bottom(driver)

        except:
            print_lg(f"Error finding connections")
            retry += 1
    print_lg(
        f"Finished messaging connections.")
    pyautogui.alert(
        text="Finished messaging connections.", title="Task Completed", button="OK")


def search_and_add_connections(driver, page=1, end=None) -> int:
    """
    Searches for 'It Hr' on LinkedIn and sends connection requests safely.
    """
    connection_count = 0
    print_lg(
        f"Starting to search and add connections for '{SEARCH_STRING}' from page {page} to {end if end else 'end'}")
    try:
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_STRING.replace(' ', '%20')}&page={page}"
        while True and (end is None or page <= end):
            driver.get(search_url)

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            profile_divs = driver.find_elements(
                By.XPATH, '//div[@data-view-name="edge-creation-connect-action"]'
            )

            for div in profile_divs:
                try:
                    connect_btn = None
                    try:
                        connect_btn = div.find_element(
                            By.XPATH, './/button[.//span[text()="Connect"]]')
                    except Exception:
                        try:
                            connect_btn = div.find_element(
                                By.XPATH, './/a[.//span[text()="Connect"]]')
                        except Exception:
                            continue

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", connect_btn
                    )
                    time.sleep(0.5)
                    if not (connect_btn.is_displayed() and connect_btn.is_enabled()):
                        continue

                    try:
                        connect_btn.click()
                    except Exception:
                        driver.execute_script(
                            "arguments[0].click();", connect_btn)
                    try:
                        time.sleep(2)
                        send_without_note_keyboard(driver)
                        connection_count += 1
                    except Exception as e:
                        print_lg(f"Failed to connect: {e}")
                except Exception as e:
                    print_lg(f"Error processing profile div: {e}")
                    continue

            page += 1
            time.sleep(2)
    except:
        print_lg(f"Error during search and add connections")
    else:
        choice = pyautogui.confirm(
            "Do you want to search for more connections?", buttons=["Yes", "No"])
        if choice == "No":
            return

        count = pyautogui.prompt(
            "Reached the end of page count. How many more pages u want to search? (Leave blank for no limit):", "Search Pages")
        if count == "":
            return search_and_add_connections(driver, page, None)
        if count and count.isdigit():
            count = int(count)
            if count > 0:
                return search_and_add_connections(driver, page, page+count-1)
        else:
            return connection_count
    finally:
        return connection_count
