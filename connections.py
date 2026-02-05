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
    time.sleep(3)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    time.sleep(1.5)


def send_without_note_keyboard_alt(driver):

    driver.execute_script("""
    const el =
      document.querySelector('[role="dialog"] button') ||
      document.querySelector('button.artdeco-button--primary');
    if (el) el.focus();
    """)

    time.sleep(0.2)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    time.sleep(3)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    time.sleep(1.5)


def connect_alter_buttons(driver, buttons):
    count = 0
    try:
        for btn in buttons:
            try:
                if "connect" in btn.text.lower():
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", btn)
                    time.sleep(0.5)
                    if btn.is_displayed() and btn.is_enabled():
                        try:
                            btn.click()
                        except Exception:
                            driver.execute_script(
                                "arguments[0].click();", btn)

                    send_without_note_keyboard_alt(driver)
                    count += 1
            except Exception:
                print_lg(f"Error clicking connect button")
                continue

        return count
    except Exception:
        print_lg("Error in connect_alter_buttons")


def add_profiles_from_page(driver, profile_divs) -> int:
    connection_count = 0
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
            print_lg(f"Found {len(profile_divs)} profiles on page {page}.")
            if not profile_divs:
                try:
                    time.sleep(5)
                    profile_divs = driver.find_elements(
                        By.XPATH, '//button[contains(@aria-label, "to connect")]'
                    )
                    if not profile_divs:
                        print_lg(f"No connect buttons found on page {page}.")
                        page += 1
                        continue
                    print_lg(
                        f"Found {len(profile_divs)} profiles using alternative XPath.")
                    connection_count += connect_alter_buttons(
                        driver, profile_divs)
                except Exception as e:
                    print_lg(f"Error finding profile divs: {e}")
            else:
                connection_count += add_profiles_from_page(
                    driver, profile_divs)
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
