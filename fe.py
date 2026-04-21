from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from getpass import getpass
import shutil
import threading
import time

LOGIN_URL = "https://student.mist.ac.bd/login"
EVALUATION_URL = "https://student.mist.ac.bd/semester-evaluation/faculty-evaluation"
RATING_OPTIONS = ["Very Good", "Good", "Average", "Poor", "Very Poor"]


def prompt_with_default(prompt_text, default_value):
    user_input = input(f"{prompt_text} [{default_value}]: ").strip()
    return user_input if user_input else default_value


def prompt_rating_choice():
    print("\nChoose a rating for all questions:")
    for idx, label in enumerate(RATING_OPTIONS, start=1):
        print(f"  {idx}. {label}")

    while True:
        raw = input("Enter rating number (default 1): ").strip()
        if not raw:
            return 0, RATING_OPTIONS[0]

        if raw.isdigit():
            selected = int(raw) - 1
            if 0 <= selected < len(RATING_OPTIONS):
                return selected, RATING_OPTIONS[selected]

        print("Invalid choice. Please enter a number between 1 and 5.")


def prompt_browser_choice():
    print("\nChoose browser:")
    print("  1. Edge")
    print("  2. Chrome")
    print("  3. Firefox")

    browser_map = {
        "1": "edge",
        "2": "chrome",
        "3": "firefox",
        "edge": "edge",
        "chrome": "chrome",
        "firefox": "firefox",
    }

    while True:
        raw = input("Enter 1/2/3 (default 1): ").strip().lower()
        if not raw:
            return "edge"

        if raw in browser_map:
            return browser_map[raw]

        print("Invalid browser choice. Please enter 1, 2, or 3.")


def find_local_driver(browser_name):
    candidates = {
        "edge": "msedgedriver",
        "chrome": "chromedriver",
        "firefox": "geckodriver",
    }
    executable = candidates.get(browser_name)
    if not executable:
        return None
    return shutil.which(executable)


def create_driver(browser_name, driver_path=None):
    browser_name = (browser_name or "edge").strip().lower()

    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.page_load_strategy = "eager"
        if driver_path:
            return webdriver.Chrome(service=ChromeService(driver_path), options=options)
        return webdriver.Chrome(options=options)

    if browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        options.page_load_strategy = "eager"
        if driver_path:
            driver = webdriver.Firefox(service=FirefoxService(driver_path), options=options)
        else:
            driver = webdriver.Firefox(options=options)
        driver.maximize_window()
        return driver

    options = webdriver.EdgeOptions()
    options.add_argument("--start-maximized")
    options.page_load_strategy = "eager"
    if driver_path:
        return webdriver.Edge(service=EdgeService(driver_path), options=options)
    return webdriver.Edge(options=options)


def _driver_progress_indicator(stop_event):
    frames = ["|", "/", "-", "\\"]
    idx = 0
    while not stop_event.is_set():
        frame = frames[idx % len(frames)]
        print(f"\rInitializing browser... {frame}", end="", flush=True)
        idx += 1
        time.sleep(0.2)


def initialize_driver(browser_name):
    browser_name = (browser_name or "edge").strip().lower()
    driver_path = find_local_driver(browser_name)

    if driver_path:
        print(f"Using local {browser_name.title()} WebDriver: {driver_path}")
    else:
        print(f"No local {browser_name.title()} WebDriver found.")
        print("Downloading WebDriver automatically (first run may take 20-60 seconds).")

    start = time.time()
    stop_event = threading.Event()
    spinner = threading.Thread(target=_driver_progress_indicator, args=(stop_event,), daemon=True)
    spinner.start()

    try:
        if driver_path:
            driver = create_driver(browser_name, driver_path=driver_path)
        else:
            if browser_name == "chrome":
                managed_driver_path = ChromeDriverManager().install()
            elif browser_name == "firefox":
                managed_driver_path = GeckoDriverManager().install()
            else:
                managed_driver_path = EdgeChromiumDriverManager().install()
            driver = create_driver(browser_name, driver_path=managed_driver_path)
    except Exception as managed_error:
        print(f"\nManaged driver setup failed: {managed_error}")
        print("Trying Selenium built-in driver manager...")
        driver = create_driver(browser_name)
    finally:
        stop_event.set()
        spinner.join(timeout=1)

    elapsed = time.time() - start
    print(f"\rInitializing browser... done in {elapsed:.1f}s{' ' * 12}")
    return driver


def login(driver, username, password):
    """Login to the student portal"""
    print("Navigating to login page...")
    driver.get(LOGIN_URL)
    
    try:
        # Wait for login form to load
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email"))
        )
        password_field = driver.find_element(By.NAME, "password")
        
        # Enter credentials
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        print("Login submitted, waiting for redirect...")
        time.sleep(3)
        
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False


def evaluate_faculty(driver, faculty_name, rating_index, rating_label, comments_text, recommendations_text):
    """Evaluate a single faculty member"""
    try:
        print(f"Evaluating: {faculty_name}")
        # Wait until at least 10 question number elements are present
        try:
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//div[contains(@class,'semesterEvaluation_question_number__') and starts-with(normalize-space(.), 'Q')]") ) >= 10
            )
        except TimeoutException:
            print("  Could not detect 10 questions on the page (timeout).")
            return False

        question_number_elems = driver.find_elements(By.XPATH, "//div[contains(@class,'semesterEvaluation_question_number__') and starts-with(normalize-space(.), 'Q')]")
        
        for idx, q_elem in enumerate(question_number_elems, start=1):
            label = q_elem.text.strip()
            try:
                # Navigate from the question number element up two levels then to the sibling answers container
                answer_container = q_elem.find_element(By.XPATH, "../../following-sibling::div")
                answer_options = answer_container.find_elements(By.XPATH, ".//div[contains(@class,'semesterEvaluation_answer_item__')]")
                if not answer_options:
                    print(f"  No answer options found for {label or 'Q'+str(idx)}")
                    continue

                chosen_index = min(rating_index, len(answer_options) - 1)
                selected_option = answer_options[chosen_index]

                # Skip click if already active
                classes = selected_option.get_attribute("class") or ""
                if 'semesterEvaluation_answer_item_active' in classes:
                    print(f"  {label} already '{rating_label}' (active)")
                else:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", selected_option)
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(selected_option))
                    driver.execute_script("arguments[0].click();", selected_option)
                    print(f"  Selected {label} -> {rating_label}")
                time.sleep(0.15)
            except Exception as e:
                print(f"  Error answering {label or 'Q'+str(idx)}: {e}")
                # Optional: capture a small debug snippet
                try:
                    snippet = selected_option.get_attribute('outerHTML')[:120]
                    print(f"    Debug snippet: {snippet}...")
                except:
                    pass
        
        # Click the submit button to open the modal
        submit_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
        )
        submit_button.click()
        print("  Opened comments modal")
        time.sleep(1)
        
        # Fill in the modal form
        try:
            # Wait for modal to appear
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "evaluate_form"))
            )
            
            # Fill overall comments
            comments_field = driver.find_element(By.NAME, "comments")
            comments_field.clear()
            comments_field.send_keys(comments_text)
            
            # Fill recommendations
            recommendations_field = driver.find_element(By.NAME, "recommendations")
            recommendations_field.clear()
            recommendations_field.send_keys(recommendations_text)
            
            print("  Filled comments and recommendations")
            time.sleep(0.5)
            
            # Submit the form
            modal_submit = driver.find_element(By.CSS_SELECTOR, "button[type='submit'][form='evaluate_form']")
            modal_submit.click()
            print(f"  ✓ Evaluation submitted for {faculty_name}")
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"  Error filling modal: {e}")
            return False
            
    except Exception as e:
        print(f"Error evaluating faculty: {e}")
        return False

def get_faculty_list(driver):
    """Get list of all faculty members to evaluate"""
    try:
        # Find all evaluate buttons
        evaluate_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Evaluate')]")
        
        faculty_list = []
        for button in evaluate_buttons:
            try:
                # Get faculty name from the same container
                parent = button.find_element(By.XPATH, "./ancestor::div[contains(@class, 'semesterEvaluation_faculty_item')]")
                name_element = parent.find_element(By.XPATH, ".//div[contains(@class, 'MuiBox-root')][2]")
                faculty_name = name_element.text.strip()
                faculty_list.append((faculty_name, button))
            except:
                continue
        
        return faculty_list
    except Exception as e:
        print(f"Error getting faculty list: {e}")
        return []

def main():
    print("Faculty Evaluation Automation")
    print("=" * 32)

    # Get user credentials
    username = input("Enter your username/ID: ").strip()
    password = getpass("Enter your password (hidden): ")
    browser_name = prompt_browser_choice()
    rating_index, rating_label = prompt_rating_choice()
    comments_text = prompt_with_default("Overall comments", "Good performance overall. N/A")
    recommendations_text = prompt_with_default("Recommendations", "Keep up the good work. N/A")

    print(f"\nBrowser mode: {browser_name.title()}")
    print("\nInitializing browser...")
    driver = initialize_driver(browser_name)
    
    try:
        # Login
        if not login(driver, username, password):
            print("Login failed. Exiting...")
            return
        
        # Navigate to evaluation page
        print("\nNavigating to faculty evaluation page...")
        driver.get(EVALUATION_URL)
        time.sleep(3)
        
        # Process evaluations
        total_evaluated = 0
        while True:
            print("\nChecking for faculty members to evaluate...")
            
            # Get current list of faculty to evaluate
            faculty_list = get_faculty_list(driver)
            
            if not faculty_list:
                print("\n✓ All faculty evaluations completed!")
                break
            
            print(f"Found {len(faculty_list)} faculty member(s) to evaluate")
            
            # Get the first faculty member
            faculty_name, evaluate_button = faculty_list[0]
            
            # Click evaluate button
            evaluate_button.click()
            time.sleep(2)
            
            # Evaluate this faculty member
            if evaluate_faculty(
                driver,
                faculty_name,
                rating_index,
                rating_label,
                comments_text,
                recommendations_text,
            ):
                total_evaluated += 1
                print(f"Progress: {total_evaluated} evaluation(s) completed")
            
            # Go back to the main evaluation page
            driver.get(EVALUATION_URL)
            time.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"COMPLETED: {total_evaluated} faculty evaluations finished!")
        print(f"{'='*50}")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nClosing browser...")
        driver.quit()

if __name__ == "__main__":
    main()