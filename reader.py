import selenium.webdriver as webdriver


def start_quiz(driver, module_url):
    driver.get(module_url)
    print(f"Opened module page: {module_url}")