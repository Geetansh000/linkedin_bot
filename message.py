import pyautogui
from selenium.webdriver.common.by import By
from config.text import message_text
from config.personals import skip_words, connection_end, connection_start
from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
import time

seen_profiles = set()

csv_profiles = get_profiles_from_csv()

def send_message(driver: WebDriver):
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(5)
    try:
        text = driver.find_element(
            By.XPATH, './/div[contains(@class,"artdeco-entity-lockup__subtitle")]').text
        if text and any(skip_word.strip() in text.lower() for skip_word in skip_words):
            print_lg("Skipping profile")
            return
    except Exception:
        print_lg("Title not found, skipping")
    try:
        driver.find_element(
            By.XPATH, './/div[contains(@class,"msg-s-message-list")]')
    except Exception:
        try:
            text_input = driver.find_element(
                By.XPATH,
                './/div[contains(@class, "msg-form__contenteditable")]'
            )
            text_input.click()
            text_input.send_keys(message_text)
            send_button = driver.find_element(
                By.XPATH,
                './/button[contains(@class, "msg-form__send-button")]'
            )
            time.sleep(5)
            send_button.click()
        except Exception as e:
            print_lg("Could not send message, skipping", e)
            time.sleep(5)


def message_connections(driver: WebDriver, cards: list):
    print_lg(f"Found {len(cards)} connection cards.")
    global seen_profiles
    for card in cards:
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", card
            )
            time.sleep(0.3)
            message_link = card.find_element(
                By.XPATH,
                './/div[@data-view-name="message-button"]//a[@aria-label="Message"]'
            )

            href = message_link.get_attribute("href")

            # 🔥 DEDUPE
            if href in seen_profiles:
                continue

            seen_profiles.add(href)

            driver.execute_script("window.open(arguments[0], '_blank');", href)

            driver.switch_to.window(driver.window_handles[-1])
            retry = 0
            try:
                while True:
                    try:
                        send_message(driver)
                        break
                    except:
                        if retry >= 3:
                            raise Exception(
                                "Max retries reached for sending message")
                        print_lg("Retrying to send message...")
                        time.sleep(2)
                        retry += 1
            except Exception as e:
                print_lg("Failed to send message:", e)

            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

        except Exception:
            print_lg("Message button not rendered yet, skipping")
            continue


def message_connection(driver: WebDriver, href: str):
    global seen_profiles
    try:
        if href in seen_profiles:
            return

        seen_profiles.add(href)

        driver.execute_script("window.open(arguments[0], '_blank');", href)
        driver.switch_to.window(driver.window_handles[-1])

        retry = 0
        while retry < 3:
            try:
                return send_message(driver)
            except Exception:
                print_lg("Retrying to send message...")
                retry += 1
                time.sleep(2)
    except Exception:
        print_lg("Message button not rendered yet, skipping")
    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])


def scroll_to_bottom(driver: WebDriver):
    try:
        load_more_button = driver.find_element(
            By.XPATH,
            './/button[.//span[text()="Load more"]]'
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", load_more_button
        )
        time.sleep(1)
        load_more_button.click()
        print_lg("Clicked Load More button")
    except Exception:
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)


def open_and_validate_profile(driver: WebDriver, profile_link: str) -> bool:
    driver.execute_script("window.open(arguments[0], '_blank');", profile_link)
    driver.switch_to.window(driver.window_handles[-1])
    try:
        # Ensure page is loaded
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        # 🔥 BEST WAY: Current company via aria-label
        company_btn = wait.until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//button[contains(@aria-label,"Current company:")]')
            )
        )
        scroll_page(driver)
        scroll_to_top(driver)
        time.sleep(2)
        aria = company_btn.get_attribute("aria-label")

        company = aria.split("Current company:")[1].split(".")[0].strip()
        if company.lower() in skip_words:
            print_lg(f"Skipping company: {company} for {profile_link}")
            return False

        return True

    except Exception:
        # 🧠 Fallback: check if Experience section exists
        try:
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, '//section[.//span[text()="Experience"]]')
                )
            )
            return True

        except Exception:
            print_lg(
                f"Neither current company nor experience found for {profile_link}")
            return False

    finally:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])



def check_profile(driver: WebDriver, cards: list):
    global csv_profiles
    for card in cards:
        try:
            profile_link = card.find_element(
                By.XPATH, './/a[@data-view-name="connections-profile"]').get_attribute("href")
            if profile_link in csv_profiles:
                print_lg(f"Already messaged profile: {profile_link}, skipping")
                continue
            message_link = card.find_element(
                By.XPATH,
                './/div[@data-view-name="message-button"]//a[@aria-label="Message"]'
            ).get_attribute("href")

            if open_and_validate_profile(driver, profile_link):
                time.sleep(2)
                #scroll to card
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", card
                )
                time.sleep(2)
                message_connection(driver, message_link)
                csv_profiles.add(profile_link)
                save_seen_profiles(profile_link)
                time.sleep(2)
        except Exception:
            print_lg("Error checking profile, skipping")


def find_connections(driver: WebDriver):
    search_url = "https://www.linkedin.com/mynetwork/invite-connect/connections/"
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

        except Exception as e:
            print_lg(f"Error finding connections: {e}")
            retry += 1
    print_lg(
        f"Finished messaging connections.")
    pyautogui.alert(
        text="Finished messaging connections.", title="Task Completed", button="OK")
