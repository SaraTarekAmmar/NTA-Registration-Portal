import mysql.connector
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
import sys

# Setup password hashing (using pbkdf2_sha256 for pure-python compatibility on Windows)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def set_admin_password():
    # Load DB credentials
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, 'backend', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    db_pass = os.getenv('DB_PASSWORD', 'OmarNour@Work161996')
    db_name = os.getenv('DB_NAME', 'nta_portal')
    db_user = os.getenv('DB_USER', 'root')
    db_host = os.getenv('DB_HOST', 'localhost')

    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name
        )
        cursor = conn.cursor()

        print("--- NTA Super Admin Password Utility ---")
        email = input("Enter Admin/Editor Email: ").strip()
        password = input("Enter New Password: ").strip()

        if not email or not password:
            print("Error: Email and Password are required.")
            return

        hashed = get_password_hash(password)

        query = "UPDATE users SET password_hash = %s WHERE email = %s AND role IN ('admin', 'editor')"
        cursor.execute(query, (hashed, email))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"Successfully updated password for {email}.")
        else:
            print(f"Error: No admin/editor found with email {email}.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    set_admin_password()
