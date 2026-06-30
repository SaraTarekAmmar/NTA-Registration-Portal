from playwright.sync_api import sync_playwright
import pytest
import os

def test_theme_switching():
    # Start playwright and test theme switching on superadmin portal
    # To run this, the superadmin server needs to be running.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # We construct a local URL based on a mock static HTML load, 
        # but in practice, you'd navigate to "http://localhost:8003/"
        # Since the server might not be running in this test environment, 
        # we will use the local file URI if possible, or expect a real server.
        
        local_path = f"file:///{os.path.abspath('superadmin/frontend/index.html').replace(os.sep, '/')}"
        page.goto(local_path)
        
        # Test if theme is applied (light mode or dark mode by default)
        html_classes = page.locator("html").get_attribute("class") or ""
        is_light_mode_default = "light-mode" in html_classes
        
        # Find the theme toggle button and click it
        # The toggle button usually has id "themeToggle" or "ntaThemeFab"
        toggle = page.locator("#themeToggle, #ntaThemeFab").first
        if toggle.is_visible():
            toggle.click()
            
            # Wait for JS to update theme
            page.wait_for_timeout(500)
            
            # Verify the theme changed
            new_classes = page.locator("html").get_attribute("class") or ""
            is_light_mode_new = "light-mode" in new_classes
            
            assert is_light_mode_default != is_light_mode_new
            
        browser.close()
