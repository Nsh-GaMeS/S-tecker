from importlib.util import find_spec
from pathlib import Path
import os
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = SCRIPT_DIR / "venv" / "bin" / "python"


def bootstrap_python():
    if find_spec("selenium") is not None:
        return

    if VENV_PYTHON.exists() and os.environ.get("S_TEC_SCRAPER_BOOTSTRAPPED") != "1":
        os.environ["S_TEC_SCRAPER_BOOTSTRAPPED"] = "1"
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])


bootstrap_python()

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
import logging
from dotenv import load_dotenv
from scraper_paths import MODULE_LINKS_PATH, write_module_links

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("s_tec_scraper")

# Configure Chrome to avoid bot detection
chrome_options = Options()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# Add user agent to look more like a real browser
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36')

# Initialize the Chrome WebDriver with options
driver = webdriver.Chrome(options=chrome_options)

# Remove webdriver property to avoid detection
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    '''
})

# This is part 1 - Login and navigate to all modules page

# Open s-tec login page
driver.get("https://na.s-tec.shimano.com/login")
logger.info("Opened s-tec login page")

# wait until the username and password fields are visible(checking the xpath the fields)
wait = WebDriverWait(driver, 10)
username_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="user_name"]')))
password_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="password"]')))

# Enter username and password
username_field.send_keys(os.getenv("user"))
password_field.send_keys(os.getenv("password"))

# find and click the login button
submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signinform"]/fieldset[2]/div/button')))
submit_button.click()
logger.info("Clicked login button")

# wait for page to load after login
wait.until(EC.url_changes("https://na.s-tec.shimano.com/login"))
logger.info("Logged in successfully")

# Add extra wait to ensure page fully loads and overlays disappear
time.sleep(2)

logger.info("Opening training menu")
training_dropdown = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            '//*[@id="mainNav"]//a[contains(translate(normalize-space(.), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "training")]'
        )
    )
)
driver.execute_script("arguments[0].click();", training_dropdown)
logger.info("Training menu opened")

all_modules_option = wait.until(
    EC.element_to_be_clickable(
        (
            By.XPATH,
            '//*[@id="mainNav"]//a[contains(translate(normalize-space(.), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "all modules")]'
        )
    )
)
driver.execute_script("arguments[0].click();", all_modules_option)
logger.info("Opened all modules page")


# This is part 2 - Collect and save all module links

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#modules a[href*='/module/composite/']")))
module_links_section = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#modules")))
anchor_elements = module_links_section.find_elements(By.CSS_SELECTOR, "a[href]")

raw_hrefs = []
for anchor in anchor_elements:
    href = anchor.get_attribute("href")
    if not href or "/module/composite/" not in href:
        continue
    raw_hrefs.append(href.rstrip("/"))

module_hrefs = list(dict.fromkeys(raw_hrefs))
logger.info(
    "Found %s anchors, %s module links after filtering, %s unique links",
    len(anchor_elements),
    len(raw_hrefs),
    len(module_hrefs),
)

if not module_hrefs:
    raise RuntimeError("No module links were found on the all modules page")

logger.info("Saving %s module links to %s", len(module_hrefs), MODULE_LINKS_PATH)
write_module_links(module_hrefs)

for href in module_hrefs:
    logger.info(href)

driver.quit()