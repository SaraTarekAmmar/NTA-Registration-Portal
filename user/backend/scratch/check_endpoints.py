import requests

BASE_URL = "http://localhost:7771" 

def check_endpoints():
    endpoints = [
        "/api/lookups/countries",
        "/api/lookups/interests",
        "/api/lookups/languages",
        "/api/lookups/military-status",
        "/api/lookups/identity-doc-types",
        "/api/lookups/degree-levels",
        "/api/lookups/grades",
        "/api/lookups/ministries",
        "/api/lookups/job-titles",
        "/api/lookups/marital-status",
        "/api/lookups/monthly-income"
    ]
    
    # Try 8001 first (from main.py)
    port = 8001
    print(f"Checking endpoints on port {port}...")
    for ep in endpoints:
        try:
            url = f"http://localhost:{port}{ep}"
            resp = requests.get(url)
            print(f"  {ep}: {resp.status_code}")
            if resp.status_code != 200:
                print(f"    ERROR: {resp.text}")
        except Exception as e:
            print(f"  {ep}: FAILED ({e})")

if __name__ == "__main__":
    check_endpoints()
