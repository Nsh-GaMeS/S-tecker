from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os
from dotenv import load_dotenv
from reader import start_quiz

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

# This is part 1 - Login and navigate to all modules page

# Open s-tec login page
driver.get("https://na.s-tec.shimano.com/login")
print("Opened s-tec login page")

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
print("Clicked login button")

# wait for page to load after login
wait.until(EC.url_changes("https://na.s-tec.shimano.com/login"))
print("Logged in successfully")

# Add extra wait to ensure page fully loads and overlays disappear
time.sleep(2)

# click the "training" dropdown menu using JavaScript to avoid interception
training_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="mainNav"]/div/div/div/ul[1]/li[1]/a')))
driver.execute_script("arguments[0].click();", training_dropdown)
print("Clicked training dropdown")

# click the "all modules" option
all_modules_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mainNav"]/div/div/div/ul[1]/li[1]/div/ul/li[11]/a')))
all_modules_option.click()
print("Clicked all modules option")


# This is part 2 - Collect and save all module links

# wait for the all modules page to load by waiting for the modules section to appear
module_links_section = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#modules > div > div")))
print("All modules page loaded")

# collect all module links in the section
module_links = module_links_section.find_elements(By.CSS_SELECTOR, "div > a")

print(f"Found {len(module_links)} module links.")

# Save the hrefs of all modules
module_hrefs = [link.get_attribute('href') for link in module_links]
print("Module Hrefs:", module_hrefs)

with open("module_links.txt", "w") as file:
    for href in module_hrefs:
        file.write(href + "\n")

print(f"\nFound {len(module_hrefs)} module links total.")

# Print all collected hrefs
print("Collected module links:")
for href in module_hrefs:
    print(href)

# This is part 3 - Open a module link in a new tab and start the quiz
# side note - adding a progress bar would be cool.
# for href in module_hrefs:
start_quiz(driver, module_hrefs[0])

# Keep browser open to inspect
input("\nPress Enter to close browser...")
driver.quit()
