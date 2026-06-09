import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.microsoft import EdgeChromiumDriverManager

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def get_current_step_from_dom(driver):
    try:
        active_step_el = driver.find_element(By.CSS_SELECTOR, ".reg-step.active")
        return int(active_step_el.get_attribute("data-step"))
    except Exception as e:
        print(f"Error getting active step from DOM: {e}")
        return None

def test_bypass_all_steps():
    print("Setting up Headless Edge browser...")
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200,900")
    options.set_capability('ms:loggingPrefs', {'browser': 'ALL'})

    service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    
    try:
        url = "http://127.0.0.1:7771/registration.html"
        print(f"Navigating to {url}...")
        driver.get(url)
        time.sleep(3)
        
        current_step = get_current_step_from_dom(driver)
        print(f"Initial Step: {current_step}")
        
        print("\nActivating Developer Validation Bypass...")
        toggle = driver.find_element(By.ID, "devBypassToggle")
        driver.execute_script("arguments[0].click();", toggle)
        time.sleep(1)
        print(f"Bypass Active Status: {toggle.is_selected()}")
        
        # Navigate through all steps
        for step in range(1, 10):
            print(f"\nCurrently on Step {step}. Clicking 'Next'...")
            btn_next = driver.find_element(By.ID, "btnNext")
            driver.execute_script("arguments[0].click();", btn_next)
            time.sleep(1)
            
            new_step = get_current_step_from_dom(driver)
            print(f"Transitioned to Step: {new_step}")
            if new_step != step + 1:
                print(f"Warning: Failed to reach expected step {step+1}. Blocked on step {new_step}.")
                break
                
        # Now we are on Step 10
        print("\nChecking if Submit button is visible on Step 10...")
        btn_submit = driver.find_element(By.ID, "btnSubmit")
        print(f"Submit button displayed: {btn_submit.is_displayed()}")
        
        print("\nClicking Submit button...")
        driver.execute_script("arguments[0].click();", btn_submit)
        time.sleep(3)
        
        print(f"Current page URL: {driver.current_url}")
        if "success" in driver.current_url or "profile" in driver.current_url:
            print("SUCCESS: Successfully submitted registration and redirected!")
        else:
            print(f"Submit result url: {driver.current_url}")
            
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_bypass_all_steps()
