import mysql.connector
import os
import json
from dotenv import load_dotenv

# Load DB credentials
env_path = os.path.join('admin', 'backend', '.env')
load_dotenv(env_path)

def check_editor():
    db_pass = os.getenv('DB_PASSWORD', 'OmarNour@Work161996')
    db_name = os.getenv('DB_NAME', 'nta_portal')
    db_user = os.getenv('DB_USER', 'root')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            port=db_port
        )
        cursor = conn.cursor(dictionary=True)
        
        email = "editor@nta.edu.eg"
        cursor.execute("SELECT id, email, role, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            print(f"User Found: {json.dumps(user, indent=2)}")
        else:
            print(f"User NOT found: {email}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    check_editor()
