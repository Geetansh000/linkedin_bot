from selenium.webdriver.common.by import By
from config.text import message_text
from config.personals import skip_words
from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
import time

seen_profiles = set()


def send_message(driver: WebDriver):
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(5)
    try:
        text = driver.find_element(
            By.XPATH, './/div[contains(@class,"artdeco-entity-lockup__subtitle")]').text
        if any(skip_word in text for skip_word in skip_words):
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
                '//div[@data-view-name="connections-list"]//div[.//div[@data-view-name="message-button"]]'
            )
            if len(cards) > old_length:
                retry = 0  # Reset retry if new cards are found
            elif len(cards) == old_length and len(cards) > 0:
                break  # Exit if no new cards are found
            # Process only new cards
            message_connections(driver, cards[old_length:])
            # Scroll to the bottom to load all connections
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

        except Exception as e:
            print_lg(f"Error finding connections: {e}")
            retry += 1
