"""
install_trainers.py
-------------------
Reads trainer_accounts.txt and upserts each trainer into the `users` table
with role='trainer'.

Format in trainer_accounts.txt (pipe-separated):
  Full Name (AR) | Full Name (EN) | Email | National ID | Password

Usage:
  python deploy/install_trainers.py
"""

import mysql.connector
import os
import sys
from dotenv import load_dotenv
from passlib.context import CryptContext

# Password hashing — must match the system's auth.py
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_db_connection():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Load credentials from credentials.txt first, then fall back to .env files
    creds_file = os.path.join(script_dir, "credentials.txt")
    env_paths = [
        creds_file,
        os.path.join(project_root, "admin", "backend", ".env"),
        os.path.join(project_root, "superadmin", "backend", ".env"),
        os.path.join(project_root, "user", "backend", ".env"),
    ]

    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path)
            print(f"[*] Loaded credentials from: {path}")
            break
    else:
        print("[!] Warning: No credentials file found. Using environment defaults.")

    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 3306)),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "nta_portal"),
        )
        return connection
    except mysql.connector.Error as err:
        print(f"[!] Database Connection Error: {err}")
        sys.exit(1)


def install_trainers():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    accounts_file = os.path.join(script_dir, "trainer_accounts.txt")

    if not os.path.exists(accounts_file):
        print(f"[!] Error: {accounts_file} not found.")
        sys.exit(1)

    print("[*] Connecting to database...")
    db = get_db_connection()
    cursor = db.cursor(dictionary=True, buffered=True)

    upsert_query = """
        INSERT INTO users
            (full_name_ar, full_name_en, email, national_id, role,
             dob, gender, marital_status, password_hash)
        VALUES
            (%s, %s, %s, %s, 'trainer', %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            full_name_ar   = VALUES(full_name_ar),
            full_name_en   = VALUES(full_name_en),
            password_hash  = VALUES(password_hash)
    """

    try:
        with open(accounts_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        print(f"[*] Processing {len(lines)} lines from trainer_accounts.txt ...")

        success_count = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                print(f"  [SKIP] Invalid format (need 5 fields): {line}")
                continue

            name_ar, name_en, email, national_id, password = parts[:5]
            # Optional extra fields: dob, gender, marital_status
            dob            = parts[5] if len(parts) > 5 else "1985-01-01"
            gender         = parts[6] if len(parts) > 6 else "male"
            marital_status = parts[7] if len(parts) > 7 else "single"

            password_hash = get_password_hash(password)

            # Check existence for a meaningful log message
            cursor.execute(
                "SELECT id FROM users WHERE email = %s OR national_id = %s",
                (email, national_id),
            )
            existing = cursor.fetchone()
            action = "Updating" if existing else "Creating"
            print(f"  [{'+' if not existing else '*'}] {action} trainer: {email}")

            cursor.execute(
                upsert_query,
                (name_ar, name_en, email, national_id,
                 dob, gender, marital_status, password_hash),
            )
            success_count += 1

        db.commit()
        print(f"\n[SUCCESS] Installed/updated {success_count} trainer(s).")
        print("[TIP] Trainers can now log in using their email.")

    except Exception as e:
        print(f"[!] Error during installation: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        db.close()


if __name__ == "__main__":
    install_trainers()
