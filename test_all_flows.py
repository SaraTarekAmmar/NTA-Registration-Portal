import pytest
from playwright.sync_api import sync_playwright
import traceback
import os

# Port mapping based on AGENTS.md and run scripts
PORTALS = {
    "Admin": {
        "url": "http://localhost:8002/admin-login.html",
        "email": "admin@nta.edu.eg",
        "national_id": "29001011234567",
        "password": "NTA@Admin2026",
        "dashboard_token": "admin_token"
    },
    "Editor": {
        "url": "http://localhost:8004/editor-login.html",
        "email": "editor@nta.edu.eg",
        "national_id": "29505051234567",
        "password": "NTA@Editor2026",
        "dashboard_token": "editor_token"
    },
    "Coordinator": {
        "url": "http://localhost:8005/coordinator-login.html",
        "email": "coordinator@nta.edu.eg",
        "national_id": "29304041234567",
        "password": "NTA@Coord2026",
        "dashboard_token": "coordinator_token"
    },
    "Admission Center": {
        "url": "http://localhost:7776/index.html",
        "email": "admission@nta.edu.eg",
        "national_id": "29703031234567",
        "password": "NTA@Admission2026",
        "dashboard_token": "ntaTrainee" # sessionStorage
    },
    "Trainer": {
        "url": "http://localhost:8006/index.html",
        "email": "trainer@nta.edu.eg",
        "national_id": "28501011234567",
        "password": "NTA@Trainer2026",
        "dashboard_token": "ntaTrainer"
    },
    "Trainee": {
        "url": "http://localhost:7771/index.html",
        "email": "trainee@example.com",
        "national_id": "29808081234567",
        "password": "NTA@Trainee2026",
        "dashboard_token": "ntaTrainee"
    }
}

def test_all_portals():
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for name, config in PORTALS.items():
            print(f"\n--- Testing {name} Portal ---")
            page = browser.new_page()
            
            # Setup console and network tracking
            errors = []
            page.on("console", lambda msg: errors.append(f"Console {msg.type}: {msg.text}") if msg.type == "error" else None)
            page.on("response", lambda res: errors.append(f"Network Error: {res.url} - {res.status}") if res.status >= 400 else None)
            
            try:
                page.goto(config["url"], timeout=10000)
                
                # Try to login
                email_input = page.locator("input[type='email'], input[name='email'], #email, #adminEmail, #editorEmail, #coordinatorEmail").first
                if email_input.is_visible(timeout=5000):
                    email_input.fill(config["email"])
                    
                    nid_input = page.locator("input[name='nationalId'], #nationalId, #adminNationalId, #editorNationalId").first
                    if nid_input.is_visible():
                        nid_input.fill(config["national_id"])
                    
                    pwd_input = page.locator("input[type='password']").first
                    if pwd_input.is_visible():
                        pwd_input.fill(config["password"])
                        
                    # Click submit (finding button type submit or similar)
                    submit_btn = page.locator("button[type='submit'], .btn-primary, #loginBtn, .login-btn").first
                    if submit_btn.is_visible():
                        submit_btn.click()
                        page.wait_for_timeout(2000) # Wait for navigation/auth
                        
                        # Check local storage for token
                        token = page.evaluate(f"localStorage.getItem('{config['dashboard_token']}')")
                        if not token:
                            token = page.evaluate(f"sessionStorage.getItem('{config['dashboard_token']}')")
                            
                        if token:
                            print(f"[OK] {name} Login successful")
                        else:
                            print(f"[FAIL] {name} Login failed - No token found")
                            errors.append("Login failed - No token found in localStorage")
                    else:
                        print(f"[FAIL] {name} - Submit button not found")
                        errors.append("Submit button not found")
                else:
                    print(f"[FAIL] {name} - Email input not found on {config['url']}")
                    errors.append(f"Email input not found on login page")
                    
            except Exception as e:
                print(f"[ERROR] Exception during {name} test: {str(e)}")
                errors.append(f"Exception: {str(e)}")
            finally:
                if errors:
                    results.append({"portal": name, "status": "FAIL", "errors": errors})
                else:
                    results.append({"portal": name, "status": "PASS", "errors": []})
                    
                page.close()
                
        browser.close()
        
    print("\n\n=== SUMMARY ===")
    with open("bug_report.md", "w") as f:
        f.write("# Automated Bug Hunt Report\n\n")
        
        for r in results:
            print(f"{r['portal']}: {r['status']}")
            f.write(f"## {r['portal']} Portal ({r['status']})\n")
            if r['errors']:
                for err in r['errors']:
                    f.write(f"- {err}\n")
            else:
                f.write("- No obvious errors detected during login flow.\n")
            f.write("\n")

if __name__ == "__main__":
    test_all_portals()
