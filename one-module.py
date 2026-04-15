from reader import start_quiz
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import logging
from dotenv import load_dotenv  
import argparse
from scraper_paths import read_module_links


argparse = argparse.ArgumentParser(description='S-TEC Quiz Automation')
argparse.add_argument('--start-module', type=int, default=1, help='Module number to start from (default: 1)')
argparse.add_argument('--module-link', '-ml', type=str, help='Direct link to the module to start from (overrides --start-module)')
args = argparse.parse_args()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("s_tec_scraper")

load_dotenv()

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

args = argparse.parse_args()


def resolve_module_url(parsed_args):
    if parsed_args.module_link:
        return parsed_args.module_link

    module_urls = read_module_links()

    if not module_urls:
        raise ValueError("No module links available in module_links.txt")

    index = parsed_args.start_module - 1
    if index < 0 or index >= len(module_urls):
        raise IndexError(
            f"start-module {parsed_args.start_module} is out of range for {len(module_urls)} module links"
        )

    return module_urls[index]

# Open s-tec login page
module_url = resolve_module_url(args)
driver.get(module_url)
logger.info("Opened s-tec module page: %s", module_url)

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

start_quiz(driver, module_url)

# Keep browser open to inspect
input("\nPress Enter to close browser...")
driver.quit()