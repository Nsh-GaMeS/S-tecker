from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.action_chains import ActionChains

def start_quiz(driver, module_url):
    try:
        # open link in new tab
        driver.execute_script("window.open('" + module_url + "', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])

        # wait for page to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        # every module starts with a video, we have to skip it to get to the quiz.
        
        #first click the play button to start the video
        play_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#course-poster > div > div")))
        play_button.click()

        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
        time.sleep(1)  # wait a moment for the video to start playing

        # player_play_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#w-vulcan-v2-106 > div > div > button"))) <- this is the play/pause button that shows up if you one the video in a different tab. 

        # find any slider with role='slider' and drag it to the end
        sliders = driver.find_elements(By.CSS_SELECTOR, "div[role='slider']")
        if sliders:
            slider = sliders[0]  # Use the first found slider
            
            driver.execute_script(
                "arguments[0].setAttribute('aria-valuenow', arguments[0].getAttribute('aria-valuemax'));"
                "arguments[0].dispatchEvent(new Event('change'));",
                slider
            )

            # action = ActionChains(driver)
            # # Get the slider width
            # width = slider.size['width']  # Move further to ensure it reaches the end
            # # Drag the slider handle to the far right
            # action.click_and_hold(slider).move_by_offset(width * 2, 0).release().perform()
            
            print(f"Skipped video for module: {module_url}")
        else:
            print(f"No slider found to skip video for module: {module_url}")
    except Exception as e:
        print(f"Error starting quiz for module {module_url}: {e}")


def main():
    
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

    driver = webdriver.Chrome(options=chrome_options)

    # Example usage
    with open("module_links.txt", "r") as file:
        module_urls = [line.strip() for line in file.readlines()]

    start_quiz(driver, module_urls[0])  # Start quiz for the first module link

    input("\nPress Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    main()



 