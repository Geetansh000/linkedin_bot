from message import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pyautogui
from selenium.webdriver.common.keys import Keys
from config.personals import SEARCH_STRING
from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
import time


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


def search_and_add_connections(driver, page=1, end=None) -> int:
    """
    Searches for 'It Hr' on LinkedIn and sends connection requests safely.
    """
    connection_count = 0
    print_lg(
        f"Starting to search and add connections for '{SEARCH_STRING}' from page {page} to {end if end else 'end'}")
    try:
        while True and (end is None or page <= end):
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_STRING.replace(' ', '%20')}&page={page}"
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
        return connection_count
    else:
        choice = pyautogui.confirm(
            "Do you want to search for more connections?", buttons=["Yes", "No"])
        if choice == "No":
            return

        count = pyautogui.prompt(
            "Reached the end of page count. How many more pages u want to search? (Leave blank for no limit):", "Search Pages")
        if count == "":
            return search_and_add_connections(driver, page, None) + connection_count
        if count and count.isdigit():
            count = int(count)
            if count > 0:
                return search_and_add_connections(driver, page, page+count-1) + connection_count
        else:
            return connection_count
