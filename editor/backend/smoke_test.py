import urllib.request
import urllib.error
import sys
import os

def ping_url(url):
    print(f"Pinging {url}...", end="")
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            if status == 200:
                print(" OK (200)")
                return True
            else:
                print(f" FAIL (HTTP {status})")
                return False
    except urllib.error.URLError as e:
        print(f" FAIL ({e.reason})")
        return False
    except Exception as e:
        print(f" FAIL (Error: {e})")
        return False

def test_db_ping():
    print("Testing DB connection...", end="")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from core.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result and result[0] == 1:
            print(" OK (Successfully queried SELECT 1)")
            return True
        else:
            print(" FAIL (Unexpected query result)")
            return False
    except Exception as e:
        print(f" FAIL (Database error: {e})")
        return False

def run_smoke_test():
    print("==================================================")
    print("RUNNING NTA PORTAL SYSTEM SMOKE TESTS")
    print("==================================================")
    
    success = True
    
    # 1. Test Static Pages on Editor Server (Port 8004)
    pages = [
        "http://localhost:8004/editor-login.html",
        "http://localhost:8004/editor-admission-builder.html",
        "http://localhost:8004/editor-registration-builder.html",
        "http://localhost:8004/editor.css"
    ]
    
    for page in pages:
        if not ping_url(page):
            success = False
            
    # 2. Test Database Connection
    if not test_db_ping():
        success = False
        
    print("==================================================")
    if success:
        print("ALL SMOKE TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("SMOKE TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test()
