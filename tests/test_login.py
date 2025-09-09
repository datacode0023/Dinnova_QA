import os
import time
import logging
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging early so it applies to the whole module/run
_log_level_name = os.environ.get("DINNOVA_LOG_LEVEL", "INFO").upper()
_log_level = getattr(logging, _log_level_name, logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("dinnova.qa.login")

LOGIN_URL = os.environ.get("DINNOVA_QA_LOGIN_URL", "google.com")
USERNAME = os.environ.get("DINNOVA_QA_USERNAME", "user@example.com")
PASSWORD = os.environ.get("DINNOVA_QA_PASSWORD", "supersecret")
HEADLESS  = os.getenv("HEADLESS", "1") == "1"   # default headless in CI

def make_driver():
    opts = Options()
    if HEADLESS:
        opts.add_argument("-headless")  # CI-friendly
    # Selenium Manager will fetch the right geckodriver automatically
    try:
        logger.info("installing using DriverManager")
        service = Service(ChromeDriverManager().install())
        logger.info("Initializing WebDriver")
        driver = webdriver.Chrome(service=service, options=opts)
        # driver = webdriver.Firefox(options=opts)
    except Exception as exc:
        logger.exception("Failed to initialize Firefox WebDriver: %s", exc)
        raise
    driver.set_page_load_timeout(30)
    logger.debug("Set page load timeout to 30s")
    return driver

@pytest.fixture
def driver():
    logger.info("Creating WebDriver fixture")
    d = make_driver()
    yield d
    logger.info("Quitting WebDriver fixture")
    try:
        d.quit()
    except Exception as exc:
        logger.warning("Error during WebDriver quit: %s", exc)

def test_login_success(driver):
    logger.info("Starting test_login_success -> navigating to %s", LOGIN_URL)
    driver.get(LOGIN_URL)
    # Adjust selectors to your page:
    logger.debug("Filling login form with provided credentials (username only logged)")
    wait = WebDriverWait(driver, 20)
    email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
    password_input = wait.until(EC.visibility_of_element_located((By.ID, "password")))

    logger.debug("Filling login form with provided credentials (username only logged)")
    email_input.send_keys(USERNAME)
    password_input.send_keys(PASSWORD)

    logger.debug("Submitting login form")
    driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()

    # Simple success condition examples (pick what fits your site):
    # 1) URL contains dashboard
    for attempt in range(30):
        current_url = driver.current_url
        logger.debug("Attempt %d: current_url=%s", attempt + 1, current_url)
        if "dashboard" in current_url:
            break
        time.sleep(1)
    condition_ok = "dashboard" in driver.current_url or \
                    bool(driver.find_elements(By.CSS_SELECTOR, ".welcome, .account-home"))
    logger.info("Login success condition: %s", condition_ok)
    assert condition_ok

def test_login_failure(driver):
    logger.info("Starting test_login_failure -> navigating to %s", LOGIN_URL)
    driver.get(LOGIN_URL)
    # Wait until email, password and button are visible/clickable
    wait = WebDriverWait(driver, 20)
    email_input = wait.until(EC.visibility_of_element_located((By.ID, "email")))
    password_input = wait.until(EC.visibility_of_element_located((By.ID, "password")))
    submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type=submit]")))

    logger.debug("Filling login form with provided credentials (username only logged)")
    email_input.send_keys("wronguser@email.com")
    password_input.send_keys("wrongPassword")

    logger.debug("Submitting login form")
    submit_btn.click()

    # Expect an error message element to appear
    errs = []
    for attempt in range(15):
        errs = driver.find_elements(By.CSS_SELECTOR, ".text-red-600")
        logger.debug("Attempt %d: error elements found=%d", attempt + 1, len(errs))
        if errs:
            break
        time.sleep(1)
    logger.info("Login failure error message present: %s", bool(errs))
    assert errs, "Expected an error message when logging in with bad creds"
