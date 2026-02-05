from message import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv
import pyautogui
from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from connections import *
from config.text import welcome_message_text
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


def check_logged_in_LN(driver: WebDriver) -> bool:
    '''
    Function to check if user is logged-in in LinkedIn
    * If not logged-in, returns `False`
    * If logged-in, returns `True`
    '''
    if driver.current_url == "https://www.linkedin.com/feed/":
        return True
    return False


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
    if check_logged_in_LN(driver):
        print_lg("Already logged in!")
        return driver
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


def make_choice(driver: WebDriver):
    choice = pyautogui.confirm("Choose an action:", buttons=[
        "Search and Add Connections", "Send Messages"])
    if choice == "Search and Add Connections":
        page_count = pyautogui.prompt(
            "Enter number of pages to search for connections (Leave blank for no limit):", "Search Pages")
        if page_count and page_count.isdigit():
            page_count = int(page_count)
        else:
            page_count = None
        connection_count = search_and_add_connections(driver, 1, page_count)
        pyautogui.alert(
            text=f"Finished searching and adding connections for '{SEARCH_STRING}'. Added {connection_count} connections.", title="Connections successfully added", button="OK")
    elif choice == "Send Messages":
        print_lg("Sending messages to connections...")
        set_range(driver)


def main():
    """Main function to demonstrate login."""
    # Get credentials from environment variables
    email = os.getenv("LINKEDIN_EMAIL")
    password = os.getenv("LINKEDIN_PASSWORD")
    global driver

    if not email or not password:
        error_msg = "Error: Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file"
        print(error_msg)
        pyautogui.alert(error_msg, title="Missing Credentials")
        return
    try:
        try:
            driver = login_LN(email, password)

        except Exception:
            pyautogui.alert(
                "An error occurred during login. Please try again.", "Login Error", "OK"
            )
        make_choice(driver)
    except Exception as e:
        print_lg(f"Error in main function")
    finally:
        choice = pyautogui.confirm(
            "Do you want to quit now?", buttons=["Yes", "No"])
        if choice == "No":
            ''' if driver is closed reopen it '''
            try:
                print_lg("Reopening the browser...", driver)
                driver.get("https://www.linkedin.com/feed/")
            except Exception as e:
                print_lg(f"Couldn't reopen the browser! Error: {e}")
                options, driver, actions, wait = restart_driver()
                print_lg("Reopened the browser!", driver)
            driver.get("https://www.linkedin.com/feed/")
            main()

        # Close the browser
        print_lg("Closing the browser...")
        driver.quit()
        pyautogui.alert(
            text=welcome_message_text,
            title="Automation Complete ✅",
            button="Awesome!"
        )


if __name__ == "__main__":
    main()
