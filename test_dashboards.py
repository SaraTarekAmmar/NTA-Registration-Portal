import asyncio
from playwright.async_api import async_playwright

PORTALS = {
    "Admin": {
        "url": "http://localhost:8002/admin-login.html",
        "email": "admin@nta.edu.eg",
        "national_id": "29001011234567",
        "password": "NTA@Admin2026",
        "pages": [
            "http://localhost:8002/admin-dashboard.html",
            "http://localhost:8002/admin-trainees.html",
            "http://localhost:8002/admin-courses.html",
            "http://localhost:8002/admin-reports.html"
        ]
    },
    "Editor": {
        "url": "http://localhost:8004/editor-login.html",
        "email": "editor@nta.edu.eg",
        "national_id": "29505051234567",
        "password": "NTA@Editor2026",
        "pages": [
            "http://localhost:8004/editor-dashboard.html",
            "http://localhost:8004/editor-courses.html"
        ]
    },
    "Coordinator": {
        "url": "http://localhost:8005/coordinator-login.html",
        "email": "coordinator@nta.edu.eg",
        "national_id": "29304041234567",
        "password": "NTA@Coord2026",
        "pages": [
            "http://localhost:8005/coordinator-dashboard.html",
            "http://localhost:8005/coordinator-attendance.html"
        ]
    },
    "Admission Center": {
        "url": "http://localhost:7776/index.html",
        "email": "admission@nta.edu.eg",
        "national_id": "29703031234567",
        "password": "NTA@Admission2026",
        "pages": [
            "http://localhost:7776/candidates.html",
            "http://localhost:7776/interviews.html"
        ]
    },
    "Trainer": {
        "url": "http://localhost:8006/index.html",
        "email": "trainer@nta.edu.eg",
        "national_id": "28501011234567",
        "password": "NTA@Trainer2026",
        "pages": [
            "http://localhost:8006/trainer-dashboard.html",
            "http://localhost:8006/trainer-courses.html",
            "http://localhost:8006/trainer-attendance.html"
        ]
    },
    "Trainee": {
        "url": "http://localhost:7771/index.html",
        "email": "trainee@example.com",
        "national_id": "29808081234567",
        "password": "NTA@Trainee2026",
        "pages": [
            "http://localhost:7771/dashboard.html",
            "http://localhost:7771/courses.html",
            "http://localhost:7771/profile.html"
        ]
    }
}

async def run_tests():
    bugs_found = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for name, config in PORTALS.items():
            print(f"\n--- Testing {name} Portal Pages ---")
            context = await browser.new_context()
            page = await context.new_page()
            
            # Listen for console errors
            page.on("console", lambda msg: bugs_found.append(f"[{name}] Console {msg.type}: {msg.text}") if msg.type in ['error', 'warning'] else None)
            
            # Listen for failed requests
            page.on("response", lambda response: bugs_found.append(f"[{name}] Network Error: {response.url} - {response.status}") if response.status >= 400 else None)
            
            try:
                # 1. Login
                await page.goto(config["url"])
                await page.wait_for_load_state("networkidle")
                
                # Fill login form
                if name == "Trainee":
                    await page.fill("input[type='email']", config["email"])
                    await page.fill("input[type='password']", config["password"])
                else:
                    try:
                        await page.fill("input[name='nationalId']", config["national_id"])
                    except:
                        pass
                    await page.fill("input[type='email']", config["email"])
                    await page.fill("input[type='password']", config["password"])
                
                await page.click("button[type='submit']")
                await page.wait_for_timeout(2000) # Wait for login to complete and token to be saved
                
                # 2. Visit Pages
                for test_url in config.get("pages", []):
                    print(f"  Visiting {test_url}...")
                    await page.goto(test_url)
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(1000) # Give JS a moment to render and fetch APIs
                    
            except Exception as e:
                print(f"[ERROR] Exception testing {name}: {str(e)}")
                bugs_found.append(f"[{name}] Exception: {str(e)}")
            finally:
                await context.close()

        await browser.close()
        
    print("\n=== BUG REPORT ===")
    if not bugs_found:
        print("No obvious bugs found in automated scan.")
    else:
        for bug in bugs_found:
            print(bug)
            
    with open("bug_report_details.md", "w", encoding="utf-8") as f:
        f.write("# Automated Deep Bug Hunt Report\n\n")
        if not bugs_found:
            f.write("No obvious bugs found in automated scan.\n")
        else:
            for bug in bugs_found:
                f.write(f"- {bug}\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
