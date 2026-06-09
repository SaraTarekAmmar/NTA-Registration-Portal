"""
Verify editor password against the stored hash, and if it doesn't match,
re-hash and update it in the database.
"""
import mysql.connector
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

env_path = os.path.join('admin', 'backend', '.env')
load_dotenv(env_path)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

EDITOR_EMAIL = "editor@nta.edu.eg"
EDITOR_PASSWORD = "NTA@Editor2026"

def fix_editor():
    db_pass = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'nta_portal')
    db_user = os.getenv('DB_USER', 'root')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))

    try:
        conn = mysql.connector.connect(
            host=db_host, user=db_user, password=db_pass,
            database=db_name, port=db_port
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, role, password_hash FROM users WHERE email = %s", (EDITOR_EMAIL,))
        user = cursor.fetchone()

        if not user:
            print(f"ERROR: User '{EDITOR_EMAIL}' not found in database.")
            return

        print(f"User: {user['email']} | Role: {user['role']}")
        stored_hash = user['password_hash']

        # Verify current password
        is_valid = pwd_context.verify(EDITOR_PASSWORD, stored_hash) if stored_hash else False
        print(f"Password '{EDITOR_PASSWORD}' matches stored hash: {is_valid}")

        if not is_valid:
            print(">> Password mismatch! Re-hashing and updating...")
            new_hash = pwd_context.hash(EDITOR_PASSWORD)
            cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, EDITOR_EMAIL))
            conn.commit()
            print(f">> Password updated successfully for {EDITOR_EMAIL}.")
        else:
            print(">> Password is correct. Login should work.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database Error: {e}")

if __name__ == "__main__":
    fix_editor()
