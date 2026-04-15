from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchWindowException, StaleElementReferenceException, TimeoutException, NoSuchElementException
import re
import logging
from scraper_paths import read_module_links


logger = logging.getLogger("s_tec_scraper")

def start_quiz(driver, module_url):
    wait = WebDriverWait(driver, 10)
    try:
        # open link in new tab
        driver.execute_script("window.open(arguments[0], '_blank');", module_url)
        driver.switch_to.window(driver.window_handles[-1])
        print(f"Opened module page: {module_url}")

        # wait for page to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))

        # every module starts with a video, we have to skip it to get to the quiz.

        # Try to start the video, but do not fail startup if the element is hidden/zero-sized.
        play_started = False
        play_selectors = [
            "#course-poster > div > div",
            "#course-poster [role='button']",
            "#course-poster",
            "video"
        ]
        for selector in play_selectors:
            try:
                candidates = driver.find_elements(By.CSS_SELECTOR, selector)
                if not candidates:
                    continue
                el = candidates[0]
                if selector != "video":
                    try:
                        if el.is_displayed() and el.size.get('width', 0) > 0 and el.size.get('height', 0) > 0:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            el.click()
                            play_started = True
                            break
                    except Exception:
                        pass
                    try:
                        driver.execute_script("arguments[0].click();", el)
                        play_started = True
                        break
                    except Exception:
                        continue
                else:
                    driver.execute_script(
                        "arguments[0].muted = true;"
                        "arguments[0].play && arguments[0].play().catch(() => {});",
                        el,
                    )
                    play_started = True
                    break
            except Exception:
                continue

        if play_started:
            print(f"Started video for module: {module_url}")
        else:
            print(f"Could not interact with video poster for module: {module_url}; continuing with skip attempts")

        # driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
        # driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)
        time.sleep(1)  # wait a moment for the video to start playing

        # player_play_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#w-vulcan-v2-106 > div > div > button"))) <- this is the play/pause button that shows up if you one the video in a different tab. 

        # find any slider with role='slider' and drag it to the end
        sliders = driver.find_elements(By.CSS_SELECTOR, "div[role='slider']")
        if sliders:
            slider = sliders[0]  # Use the first found slider
            
            # driver.execute_script(
            #     "arguments[0].setAttribute('aria-valuenow', arguments[0].getAttribute('aria-valuemax'));"
            #     "arguments[0].dispatchEvent(new Event('change'));",
            #     slider
            # )

            action = ActionChains(driver)
            # Get the slider width
            width = slider.size.get('width', 0)
            
            # # Drag the slider handle to halfway first
            # action.click_and_hold(slider).move_by_offset(width/2, 0).release().perform()
            # time.sleep(2)  # wait a moment to give the video time to render in a bit more
            # # then once it fully loads, try dragging again to ensure it reaches the end
            # action.click_and_hold(slider).move_by_offset((width/2)+1, 0).release().perform()
            
            # driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.SPACE)

            try:
                if slider.is_displayed() and width > 1:
                    # Preferred: perform a single drag-and-drop operation which handles press-move-release
                    action.drag_and_drop_by_offset(slider, width, 0).perform()
                else:
                    raise ValueError("Slider is not interactable")
            except Exception:
                try:
                    # Fallback: explicit move-to -> click-and-hold -> move -> release with short pauses
                    action.move_to_element(slider).click_and_hold().pause(0.1).move_by_offset(max(width - 1, 1), 0).pause(0.1).release().perform()
                except Exception:
                    # Last fallback: force slider value to max with JS
                    driver.execute_script(
                        "arguments[0].setAttribute('aria-valuenow', arguments[0].getAttribute('aria-valuemax') || '100');"
                        "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                        slider,
                    )
            
            time.sleep(2)  # wait a moment to give the video time to render in a bit more
        
            # ensure slider reached the end and release focus by clicking on the page
            try:
                driver.find_element(By.TAG_NAME, 'body').click()
            except Exception:
                # if body isn't clickable, use JS to blur active element
                driver.execute_script("document.activeElement && document.activeElement.blur();")
            


            try:
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_RIGHT)
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_RIGHT)
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ARROW_RIGHT)
            except Exception:
                pass

            print(f"Skipped video for module: {module_url}")
        else:
            print(f"No slider found to skip video for module: {module_url}")
        time.sleep(3)  # wait a moment for the quiz button to appear

        # click the button to start the quiz
        quiz_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#quiz > div.eov-chooser > a.button-primary.custom-btn.proceed-to-quiz")))
        quiz_btn.click()

    except NoSuchWindowException as e:
        print(f"Error starting quiz for module {module_url}: target window already closed: {e}")
        # try to recover: switch to first available window and load the module there
        handles = driver.window_handles
        if not handles:
            print("No browser windows available, aborting module.")
            return False
        try:
            driver.switch_to.window(handles[0])
            driver.get(module_url)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "body")))
        except Exception as e2:
            print(f"Recovery attempt failed for module {module_url}: {e2}")
            return False

    except Exception as e:
        print(f"Error starting quiz for module {module_url}: {e}")
        return False



    # # find how many quiz questions there are, then call do_question that many times
    # try:
    #     # try checking if the quiz is over instead
    #     step_indicator = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='question-form']/div[1]/div")))
    #     total_questions_text = step_indicator.text.strip()  # e.g. "Question 1 of 5"
    #     total_questions = int(total_questions_text.split(" of ")[1])
    #     print(f"Total questions in quiz: {total_questions}")
    #     for _ in range(total_questions):
    #         do_question(driver, wait, module_url)
    # except Exception as e:
    #     print(f"Error determining total questions for module {module_url}: {e}")
    
    # Alternatively, just attempt questions until we hit an error (quiz end)
    while True:
        try:
            more = do_question(driver, wait, module_url)
            if not more:
                print(f"Finished all questions for module: {module_url}")
                break
            else:
                time.sleep(2)  # brief pause between questions
                
        except Exception as e:
            print(f"Finished quiz or encountered error for module {module_url}: {e}")
            break
        # more = do_question(driver, wait, module_url)
    return


def extract_correct_answer(html_content):
    # Regular expression to find the correctAnswerText variable
    match = re.search(r'correctAnswerText\s*=\s*"([^"]+)";', html_content)
    if match:
        return match.group(1)  # Return the value(not the key/id of the element) of correctAnswerText
    return None


def wait_for_next_question(driver, previous_answer_text, timeout=3):
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_answer_text = extract_correct_answer(driver.page_source)
        if current_answer_text != previous_answer_text:
            return True
        time.sleep(0.2)

    return False

def do_question(driver, wait, module_url):
    try:
        # now we are in the quiz, we need to find the correct answer from the page source
        html_content = driver.page_source
        correct_answer_text = extract_correct_answer(html_content)
        logger.info("Module %s correct answer: %s", module_url, correct_answer_text)

        if correct_answer_text is None:
            handles = driver.window_handles
            current = driver.current_window_handle
            # If there's another window (module tab), close the current module tab and switch back to the main window
            if len(handles) > 1 and current != handles[0]:
                try:
                    driver.close()
                except Exception:
                    pass
                try:
                    driver.switch_to.window(handles[0])
                except Exception:
                    pass
            else:
                # Ensure we're focused on the main window
                try:
                    driver.switch_to.window(handles[0])
                except Exception:
                    pass
            return False  # Explicitly signal quiz finished

        # Try once, then refresh the choice list once if the DOM shifts under us.
        target = (correct_answer_text or "").strip().lower()
        clicked = False
        clicked_choice_text = None
        max_attempts = 2
        for attempt in range(max_attempts):
            choices = driver.find_elements(By.CSS_SELECTOR, "ol.choices li")
            if not choices:
                time.sleep(0.2)
                continue

            for li in choices:
                try:
                    li_text = li.text.strip().lower()
                except StaleElementReferenceException:
                    # stale - restart outer attempt
                    li_text = ""
                    break

                if target and target in li_text:
                    # Try clicking with resilience to stale references
                    match_clicked = False
                    try:
                        span = li.find_element(By.CSS_SELECTOR, "label > span")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", span)
                        driver.execute_script("arguments[0].click();", span)
                        clicked_choice_text = li.text.strip()
                        match_clicked = True
                    except (StaleElementReferenceException, NoSuchElementException):
                        # Re-find the specific li and retry a JS click sequence
                        try:
                            # re-find the list items fresh and find the matching one by text
                            fresh = driver.find_elements(By.CSS_SELECTOR, "ol.choices li")
                            for f in fresh:
                                try:
                                    if target in f.text.strip().lower():
                                        try:
                                            label = f.find_element(By.CSS_SELECTOR, "label")
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
                                            driver.execute_script("arguments[0].click();", label)
                                        except Exception:
                                            try:
                                                input_el = f.find_element(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
                                                driver.execute_script("arguments[0].click();", input_el)
                                            except Exception as e:
                                                logger.warning("Final fallback click failed for %s: %s", correct_answer_text, e)
                                        clicked_choice_text = f.text.strip()
                                        match_clicked = True
                                        break
                                except StaleElementReferenceException:
                                    continue
                        except Exception as e:
                            logger.warning("Error during fallback click for %s: %s", correct_answer_text, e)
                    except Exception:
                        # generic fallback attempt on current element
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", li)
                            driver.execute_script("arguments[0].click();", li)
                            clicked_choice_text = li.text.strip()
                            match_clicked = True
                        except Exception as e:
                            logger.warning("Failed to click matching choice element for %s: %s", correct_answer_text, e)
                    clicked = match_clicked
                    if clicked_choice_text and match_clicked:
                        logger.info("Selected answer for %s: %s", module_url, clicked_choice_text)
                    break

            if clicked:
                break
            else:
                time.sleep(0.2)  # short pause then retry to account for DOM refresh

        if not clicked:
            logger.warning("No matching choice found for answer %s in %s", correct_answer_text, module_url)

        # submit the answer with retries to avoid stale element problems
        submit_clicked = False
        for _ in range(2):
            try:
                submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#fakesubmit")))
                submit_btn.click()
                submit_clicked = True
                break
            except (StaleElementReferenceException, TimeoutException):
                time.sleep(0.2)
            except Exception as e:
                logger.warning("Unexpected error clicking submit for %s: %s", module_url, e)
                break

        if not submit_clicked:
            logger.warning("Failed to click submit button for %s (may already be processed)", module_url)

        if clicked_choice_text:
            logger.info("Answered quiz question for %s with %s", module_url, clicked_choice_text)
        else:
            logger.info("Answered quiz question for module: %s", module_url)

        wait_for_next_question(driver, correct_answer_text, timeout=2)

        return True  # Indicate there may be more questions

    except Exception as e:
        logger.exception("Error during quiz for module %s: %s", module_url, e)
        # Let caller handle the termination; return False to move to next module
        return False
# def do_question(driver, wait, module_url):
#     try:
#         # wait for quiz start button to appear and click it
#         # quiz_start_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#quiz > div.eov-chooser > a.button-primary.custom-btn.proceed-to-quiz")))
#         # quiz_start_btn.click()
#         # print(f"Started quiz for module: {module_url}")

#         # now we are in the quiz, we need to find the correct answer from the page source
#         html_content = driver.page_source
#         correct_answer_text = extract_correct_answer(html_content)
#         print(f"Correct answer text: {correct_answer_text}")

#         if correct_answer_text is None:
#             handles = driver.window_handles
#             current = driver.current_window_handle
#             # If there's another window (module tab), close the current module tab and switch back to the main window
#             if len(handles) > 1 and current != handles[0]:
#                 try:
#                     driver.close()
#                 except Exception:
#                     pass
#                 try:
#                     driver.switch_to.window(handles[0])
#                 except Exception:
#                     pass
#             else:
#                 # Ensure we're focused on the main window
#                 try:
#                     driver.switch_to.window(handles[0])
#                 except Exception:
#                     pass
#             return False  # Explicitly signal quiz finished

#         # Find the choices (<ol class="choices"> li items) and click the matching one.
#         # Some pages require clicking the inner <span> inside the label, so prefer that.
#         try:
#             choices = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ol.choices li")))
#         except Exception:
#             choices = driver.find_elements(By.CSS_SELECTOR, "ol.choices li")

#         target = (correct_answer_text or "").strip().lower()
#         clicked = False

#         for li in choices:
#             try:
#                 li_text = li.text.strip().lower()
#             except Exception:
#                 li_text = ""

#             if target and target in li_text:
#                 # Prefer clicking the inner <span> (works in the site HTML you provided)
#                 try:
#                     span = li.find_element(By.CSS_SELECTOR, "label > span")
#                     driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", span)
#                     driver.execute_script("arguments[0].click();", span)
#                     print(f"Clicked span for correct answer: {correct_answer_text}")
#                 except Exception:
#                     # Fallbacks: label, then li, then input
#                     try:
#                         label = li.find_element(By.CSS_SELECTOR, "label")
#                         driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
#                         driver.execute_script("arguments[0].click();", label)
#                         print(f"Clicked label for correct answer: {correct_answer_text}")
#                     except Exception:
#                         try:
#                             driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", li)
#                             driver.execute_script("arguments[0].click();", li)
#                             print(f"Clicked li for correct answer: {correct_answer_text}")
#                         except Exception:
#                             try:
#                                 input_el = li.find_element(By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']")
#                                 driver.execute_script("arguments[0].click();", input_el)
#                                 print(f"Clicked input for correct answer: {correct_answer_text}")
#                             except Exception as e:
#                                 print(f"Failed to click matching choice element: {e}")
#                 clicked = True
#                 break

#         if not clicked:
#             print(f"No matching choice found for: {correct_answer_text}")

#         # for choice in choices:
#         #     try:
#         #         label = choice.find_element(By.TAG_NAME, "label")
#         #         label_text = label.text.strip()
#         #         if correct_answer_text and correct_answer_text.strip() in label_text:
#         #             try:
#         #                 # Prefer normal click on the label (toggles the radio)
#         #                 label.click()
#         #             except Exception:
#         #                 # Fallback to JS click on the input if normal click fails
#         #                 input_el = choice.find_element(By.CSS_SELECTOR, "input[type='radio']")
#         #                 driver.execute_script("arguments[0].click();", input_el)
#         #             print(f"Clicked the correct answer: {label_text}")
#         #             break
#         #     except Exception as e:
#         #         print(f"Failed to process choice element: {e}")

#         # submit the answer
#         submit_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#fakesubmit")))
#         submit_btn.click()

#         print(f"Answered quiz question for module: {module_url}")

#         time.sleep(7)  # wait a moment as the quiz processes the answer

#         return True  # Indicate there may be more questions

#     except Exception as e:
#         print(f"Error during quiz for module {module_url}: {e}")

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
    module_urls = read_module_links()

    start_quiz(driver, module_urls[0])  # Start quiz for the first module link

    input("\nPress Enter to close browser...")
    driver.quit()

if __name__ == "__main__":
    main()



 