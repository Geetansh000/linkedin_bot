from modules.helpers import (
    get_default_temp_profile,
    make_directories,
    find_default_profile_directory,
    critical_error_log,
    print_lg,
)
from config.settings import (
    run_in_background,
    stealth_mode,
    disable_extensions,
    safe_mode,
    logs_folder_path,
)

import shutil
import sys
import subprocess
import re

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import SessionNotCreatedException

if stealth_mode:
    import undetected_chromedriver as uc
else:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service


# ---------------------------
# Chrome version detection
# ---------------------------
def get_chrome_major_version():
    try:
        output = subprocess.check_output(
            ["google-chrome", "--version"],
            stderr=subprocess.DEVNULL
        ).decode()

        # Example: Google Chrome 144.0.7559.109
        match = re.search(r"(\d+)\.", output)
        if match:
            return int(match.group(1))
    except Exception:
        pass

    return None


# ---------------------------
# Chrome session creator
# ---------------------------
def createChromeSession(isRetry: bool = False):
    make_directories([logs_folder_path])

    options = uc.ChromeOptions() if stealth_mode else Options()

    # ❌ Never headless in stealth mode
    if run_in_background and not stealth_mode:
        options.add_argument("--headless=new")

    if disable_extensions:
        options.add_argument("--disable-extensions")

    # Stability flags (safe)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=0")

    print_lg(
        "IF YOU HAVE MORE THAN 10 TABS OPENED, PLEASE CLOSE OR BOOKMARK THEM!"
    )

    profile_dir = find_default_profile_directory()

    # ---------------------------
    # PROFILE LOGIC (CRITICAL FIX)
    # ---------------------------
    if stealth_mode:
        # UC must ALWAYS use temp profile
        options.add_argument(f"--user-data-dir={get_default_temp_profile()}")

    elif isRetry:
        print_lg("Retrying with guest profile")
        options.add_argument(f"--user-data-dir={get_default_temp_profile()}")

    elif profile_dir and not safe_mode:
        options.add_argument(f"--user-data-dir={profile_dir}")

    else:
        options.add_argument(f"--user-data-dir={get_default_temp_profile()}")

    # ---------------------------
    # DRIVER CREATION
    # ---------------------------
    if stealth_mode:
        print_lg("Starting Chrome in STEALTH mode")

        chrome_version = get_chrome_major_version()

        driver = uc.Chrome(
            options=options,
            version_main=chrome_version,
            use_subprocess=True   # 🔥 REQUIRED
        )

    else:
        chromedriver_path = shutil.which("chromedriver")
        if chromedriver_path is None:
            print_lg("chromedriver not found in PATH")
            sys.exit(1)

        driver = webdriver.Chrome(
            service=Service(chromedriver_path),
            options=options
        )

    driver.maximize_window()
    wait = WebDriverWait(driver, 5)
    actions = ActionChains(driver)

    return options, driver, actions, wait


# ---------------------------
# Bootstrap
# ---------------------------
options, driver, actions, wait = None, None, None, None

try:
    options, driver, actions, wait = createChromeSession()

except SessionNotCreatedException as e:
    critical_error_log(
        "Failed to create Chrome Session, retrying with guest profile", e
    )
    options, driver, actions, wait = createChromeSession(True)

except Exception as e:
    msg = (
        "Seems like Google Chrome is out dated. Update browser and try again!\n\n"
        "If issue persists, try Safe Mode. Set safe_mode = True in config.py\n\n"
        "Check GitHub discussions/support:\n"
        "https://github.com/GodsScion/Auto_job_applier_linkedIn\n\n"
        "OR reach out on Discord:\n"
        "https://discord.gg/fFp7uUzWCY"
    )

    if isinstance(e, TimeoutError):
        msg = "Couldn't download Chrome-driver. Set stealth_mode = False in config!"

    print_lg(msg)
    critical_error_log("In Opening Chrome", e)

    try:
        from pyautogui import alert
        alert(msg, "Error in opening chrome")
    except Exception:
        pass

    if driver:
        driver.quit()

    sys.exit(1)
