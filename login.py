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


def is_logged_in_LN() -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * Returns: `True` if user is logged-in or `False` if not
    '''
    if driver.current_url == "https://www.linkedin.com/feed/":
        return True
    if try_linkText(driver, "Sign in"):
        return False
    if try_xp(driver, '//button[@type="submit" and contains(text(), "Sign in")]'):
        return False
    if try_linkText(driver, "Join now"):
        return False
    print_lg("Didn't find Sign in link, so assuming user is logged in!")
    return True


def login_LN(username: str, password: str) -> None:
    '''
    Function to login for LinkedIn
    * Tries to login using given `username` and `password` from .env file
    * If failed, tries to login using saved LinkedIn profile button if available
    * If both failed, asks user to login manually
    '''
    # Find the username and password fields and fill them with user credentials
    global driver
    driver.get("https://www.linkedin.com/login")
    if username == "username@example.com" and password == "example_password":
        pyautogui.alert(
            "User did not configure username and password in .env file, hence can't login automatically! Please login manually!", "Login Manually", "Okay")
        print_lg("User did not configure username and password in .env file, hence can't login automatically! Please login manually!")
        manual_login_retry(is_logged_in_LN, 2)
        return
    try:
        wait.until(EC.presence_of_element_located(
            (By.LINK_TEXT, "Forgot password?")))
        try:
            text_input_by_ID(driver, "username", username, 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
        try:
            text_input_by_ID(driver, "password", password, 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
        # Find the login submit button and click it
        driver.find_element(
            By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            print_lg("Couldn't Login!")

    try:
        # Wait until successful redirect, indicating successful login
        wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
        print_lg("Login successful!")
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        manual_login_retry(is_logged_in_LN, 2)
    return driver
# >


def send_without_note_keyboard(driver):

    driver.execute_script("""
    const el =
      document.querySelector('[role="dialog"] button') ||
      document.querySelector('button.artdeco-button--primary');
    if (el) el.focus();
    """)

    time.sleep(0.2)
    # driver.switch_to.active_element.send_keys(Keys.ENTER)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.TAB)
    driver.switch_to.active_element.send_keys(Keys.ENTER)
    time.sleep(1.5)
    print("Sent connection request via focused ENTER")


def search_and_add_connections(driver):
    """
    Searches for 'It Hr' on LinkedIn and sends connection requests safely.
    """
    try:
        print_lg(f"Searching for '{SEARCH_STRING}' and adding connections...")
        page = 1
        connection_count = 0

        search_url = f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_STRING.replace(' ', '%20')}"
        while True:
            driver.get(search_url)

            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)

            profile_divs = driver.find_elements(
                By.XPATH, '//div[@data-view-name="edge-creation-connect-action"]'
            )

            print_lg(f"Found {len(profile_divs)} profiles to connect with.")
            count = 0

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
                        print_lg("Clicked Connect button")
                    except Exception:
                        driver.execute_script(
                            "arguments[0].click();", connect_btn)
                        print_lg("Clicked Connect button via JS")
                    try:
                        time.sleep(2)
                        send_without_note_keyboard(driver)
                        print_lg("Sent connection request via keyboard")
                        count += 1
                    except Exception as e:
                        print_lg(f"Failed to connect: {e}")
                except Exception as e:
                    print_lg(f"Error processing profile div: {e}")
                    continue

            connection_count += count
            print_lg(
                f"Sent {connection_count} connection requests for '{SEARCH_STRING}'.")
            page += 1
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={SEARCH_STRING.replace(' ', '%20')}&page={page}"
            time.sleep(2)

    except Exception as e:
        print_lg(f"Error during search and add connections: {e}")


def main():
    """Main function to demonstrate login."""
    # Get credentials from environment variables
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")

    if not email or not password:
        error_msg = "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file"
        print(error_msg)
        pyautogui.alert(error_msg, title="Missing Credentials")
        return

    try:
        driver = login_LN(email, password)
        # After login, search and add connections for the specified search string
        # add a choice to proceed with searching and adding connections or messaging
        choice = pyautogui.confirm("Choose an action:", buttons=[
            "Search and Add Connections", "Send Messages"])
        if choice == "Search and Add Connections":
            search_and_add_connections(driver)
        elif choice == "Send Messages":
            print_lg("Sending messages to connections...")
            find_connections(driver)
        # Keep browser open for manual actions (optional)
        input("Press Enter to close the browser...")
    except Exception as e:
        error_msg = f"Failed to login: {e}"
        print(error_msg)
        pyautogui.alert(error_msg, title="Login Failed")
    finally:

        pyautogui.alert(
            text="""        🎉 Mission Accomplished!

        Your LinkedIn automation has completed successfully.

        Connection requests and messages have been sent.
        You can now open LinkedIn and review the activity.

        ✨ Thank you for using this tool.
        See you again soon — keep networking and growing!

        — Geetansh's Automation Assistant""",
            title="Automation Complete ✅",
            button="Awesome!"
        )

        # Close the browser
        print_lg("Closing the browser...")
        driver.quit()
        # Welcome message before quitting with pyautogui


if __name__ == "__main__":
    main()
