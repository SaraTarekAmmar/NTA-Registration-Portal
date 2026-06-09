import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Use the same logic as our apps to find the .env
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, 'admin', 'backend', '.env')
load_dotenv(env_path)

def test_encoding():
    print("[*] Starting Encoding Diagnostic Test...")
    
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "nta_portal"),
        "charset": "utf8mb4"
    }

    test_string = "أهلاً بك - اختبار نظام الترميز UTF-8"
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        print(f"[*] Inserting test string: '{test_string}'")
        # We'll use a temporary update to the first user for testing
        cursor.execute("UPDATE users SET full_name_ar = %s WHERE id = 1", (test_string,))
        conn.commit()

        print("[*] Retrieving string back from database...")
        cursor.execute("SELECT full_name_ar FROM users WHERE id = 1")
        result = cursor.fetchone()[0]

        print(f"[*] Retrieved: '{result}'")

        if result == test_string:
            print("\n[SUCCESS] Encoding is working perfectly! No mojibake detected.")
        else:
            print("\n[FAILURE] Encoding mismatch!")
            print(f"    Expected: {test_string}")
            print(f"    Got:      {result}")
            sys.exit(1)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_encoding()
