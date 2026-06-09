"""
Updates the Editor user's national_id to a proper 14-digit value.
"""
import mysql.connector
import os
from dotenv import load_dotenv

env_path = os.path.join('admin', 'backend', '.env')
load_dotenv(env_path)

def fix_editor_national_id():
    db_pass = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'nta_portal')
    db_user = os.getenv('DB_USER', 'root')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))

    EDITOR_EMAIL = "editor@nta.edu.eg"
    # The schema.sql has 29505051234567 (14 chars) as the editor national_id
    NEW_NATIONAL_ID = "29505051234567"

    try:
        conn = mysql.connector.connect(
            host=db_host, user=db_user, password=db_pass,
            database=db_name, port=db_port
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, email, national_id FROM users WHERE email = %s", (EDITOR_EMAIL,))
        user = cursor.fetchone()
        print(f"Current national_id: {user['national_id']} (len={len(user['national_id']) if user['national_id'] else 0})")
        
        cursor.execute("UPDATE users SET national_id = %s WHERE email = %s", (NEW_NATIONAL_ID, EDITOR_EMAIL))
        conn.commit()
        print(f"Updated national_id to: {NEW_NATIONAL_ID} (len={len(NEW_NATIONAL_ID)})")
        print("Editor national_id is now 14 characters - login should work!")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    fix_editor_national_id()
