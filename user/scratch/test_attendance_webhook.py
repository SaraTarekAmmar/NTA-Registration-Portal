import requests
import base64
import os
import sys
from pathlib import Path

# Set up project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT / "superadmin" / "backend"))

# Sample 1x1 transparent GIF base64 string
SAMPLE_B64 = (
    "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
)

def run_integration_test():
    webhook_url = "http://localhost:8003/api/attendance/webhook"
    admin_photo_url = "http://localhost:8002/api/admin/attendance/photo/29501301000013/1/ENTER"
    
    national_id = "29501301000013"
    session_id = 1  # Course 10
    
    payload = {
        "national_id": national_id,
        "session_id": session_id,
        "match_score": 0.985,
        "event_type": "ENTER",
        "image_b64": SAMPLE_B64
    }
    
    print("--------------------------------------------------")
    print("1. Sending Face Recognition check-in request to webhook...")
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")
        
        assert response.status_code == 200, "Webhook request failed!"
        res_data = response.json()
        assert res_data.get("status") == "success", "Failed status in response!"
        
        saved_relative_path = res_data.get("image_path")
        print(f"--> Saved relative path in DB: {saved_relative_path}")
        assert saved_relative_path is not None, "Saved image path is empty!"
        
        # 2. Verify file exists on disk
        abs_file_path = PROJECT_ROOT / saved_relative_path
        print(f"2. Verifying file existence on disk: {abs_file_path}")
        assert abs_file_path.exists(), f"Image file does not exist at {abs_file_path}"
        print("[SUCCESS] Image file created successfully on disk!")
        
        # 3. Retrieve the photo from Admin server
        print("--------------------------------------------------")
        print("3. Fetching photo from admin dashboard serving endpoint...")
        photo_response = requests.get(admin_photo_url, allow_redirects=False, timeout=5)
        print(f"Status Code: {photo_response.status_code}")
        
        assert photo_response.status_code == 200, "Failed to retrieve saved photo!"
        assert "image/" in photo_response.headers.get("content-type", ""), "Content-Type is not an image!"
        print(f"[SUCCESS] Admin successfully served the photo (Size: {len(photo_response.content)} bytes)")
        
        # 4. Clean up test data
        print("--------------------------------------------------")
        print("4. Cleaning up created file and database log...")
        if abs_file_path.exists():
            os.remove(abs_file_path)
            print("Removed saved image file.")
            
        from core.database import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM attendance_logs 
                WHERE national_id = %s AND session_id = %s AND event_type = %s
            """, (national_id, session_id, "ENTER"))
            conn.commit()
            print("Cleaned up database log entry.")
        except Exception as db_err:
            print(f"Database cleanup failed: {db_err}")
        finally:
            cursor.close()
            conn.close()
            
        print("--------------------------------------------------")
        print("=== ALL END-TO-END WEBHOOK IMAGE STORAGE TESTS PASSED SUCCESSFULLY! ===")
        print("--------------------------------------------------")
        
    except requests.exceptions.RequestException as req_err:
        print(f"[CRITICAL ERROR] Network connection failed: {req_err}")
        print("Make sure both Superadmin (port 8003) and Admin (port 8002) backends are running!")
        sys.exit(1)
    except AssertionError as assert_err:
        print(f"[CRITICAL ERROR] Assertion Failed: {assert_err}")
        sys.exit(1)

if __name__ == "__main__":
    run_integration_test()
