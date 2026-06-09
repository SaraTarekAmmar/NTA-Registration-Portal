import mysql.connector
import os
import json
import sys
from dotenv import load_dotenv
from passlib.context import CryptContext

# 1. Setup Password Hashing (Matching the system's auth.py)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

# 2. Setup Environment and Database Connection
def get_db_connection():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Try to find .env in common locations
    env_paths = [
        os.path.join(project_root, 'user', 'backend', '.env'),
        os.path.join(project_root, 'admin', 'backend', '.env'),
        os.path.join(script_dir, '.env')
    ]
    
    loaded = False
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path)
            loaded = True
            break
    
    if not loaded:
        print("[!] Warning: No .env file found. Using default environment variables.")

    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'nta_portal'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except mysql.connector.Error as err:
        print(f"[!] Database Connection Error: {err}")
        return None

def install_trainees():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    accounts_file = os.path.join(script_dir, "trainee_accounts.txt")
    
    if not os.path.exists(accounts_file):
        print(f"[!] Error: {accounts_file} not found.")
        return

    print("[*] Connecting to database...")
    db = get_db_connection()
    if not db:
        return
    
    # Use buffered=True to avoid "Unread result found" errors when changing data
    cursor = db.cursor(dictionary=True, buffered=True)
    
    try:
        with open(accounts_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print(f"[*] Processing {len(lines)} lines from trainee_accounts.txt...")
        
        success_count = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = [p.strip() for p in line.split('|')]
            if len(parts) < 5:
                print(f" [SKIP] Invalid format: {line}")
                continue
                
            name_ar, name_en, email, national_id, password = parts[:5]
            
            # 1. Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s OR national_id = %s", (email, national_id))
            existing_user = cursor.fetchone()
            
            password_hash = get_password_hash(password)
            
            if existing_user:
                user_id = existing_user['id']
                print(f" [*] Updating existing user: {email}")
                cursor.execute("""
                    UPDATE users 
                    SET full_name_ar = %s, full_name_en = %s, password_hash = %s 
                    WHERE id = %s
                """, (name_ar, name_en, password_hash, user_id))
            else:
                print(f" [+] Creating new user: {email}")
                cursor.execute("""
                    INSERT INTO users (full_name_ar, full_name_en, email, national_id, role, password_hash, dob, gender, marital_status)
                    VALUES (%s, %s, %s, %s, 'trainee', %s, '1995-01-01', 'male', 'single')
                """, (name_ar, name_en, email, national_id, password_hash))
                user_id = cursor.lastrowid

            # 2. Ensure trainee_profile exists
            cursor.execute("SELECT id FROM trainee_profiles WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO trainee_profiles (user_id, phone_numbers, emergency_contacts, 
                        technical_skills, soft_skills, computer_skills, 
                        academic_history, professional_history)
                    VALUES (%s, '[]', '{}', '[]', '[]', '[]', '[]', '[]')
                """, (user_id,))

            # 3. Ensure application exists
            cursor.execute("SELECT id FROM applications WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO applications (user_id, course_id, status, motivation_data, 
                        research_publication, references_data, logistics, 
                        identity_photos, quiz_results, quiz_scores)
                    VALUES (%s, 1, 'idle', '{}', '[]', '[]', '{}', '{}', '[]', '{}')
                """, (user_id,))

            # 4. Ensure pipeline state exists
            cursor.execute("SELECT id FROM pipeline_state WHERE trainee_id = %s", (user_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO pipeline_state (trainee_id, current_stage_id, status)
                    VALUES (%s, 1, 'active')
                """, (user_id,))

            success_count += 1
        
        db.commit()
        print(f"\n[SUCCESS] Successfully installed/updated {success_count} trainees.")
        print("[TIP] Trainees can now log in using their email or national ID.")

    except Exception as e:
        print(f"[!] Error during installation: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    install_trainees()
