import mysql.connector
import os
from dotenv import load_dotenv

def clear_test_user():
    # Load env from project root/admin/backend/.env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, 'admin', 'backend', '.env')
    load_dotenv(env_path)

    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'nta_portal')
        )
        cursor = connection.cursor()

        # Find user ID for trainee@example.com / 29808081234567
        cursor.execute("SELECT id FROM users WHERE email = 'trainee@example.com' OR national_id = '29808081234567'")
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            print(f"[*] Found Test User ID: {user_id}")
            
            # Delete applications
            cursor.execute("DELETE FROM applications WHERE user_id = %s", (user_id,))
            print(f"[SUCCESS] Deleted all applications for User {user_id}")
            
            # Reset pipeline status to 1 (Initial)
            cursor.execute("UPDATE pipeline_state SET current_stage_id = 1, status = 'active' WHERE trainee_id = %s", (user_id,))
            print(f"[*] Reset pipeline state for User {user_id}")

            connection.commit()
        else:
            print("[ERROR] Test user not found in database.")

    except Exception as e:
        print(f"[ERROR] {str(e)}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    clear_test_user()
