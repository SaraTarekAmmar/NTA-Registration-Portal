import os
import mysql.connector
from dotenv import load_dotenv

def init_data_folders(project_root):
    print("[*] Initializing 'data' folder structure...")
    data_path = os.path.join(project_root, 'data')
    subfolders = [
        'trainees',
        'trainers',
        'courses/images',
        'courses/materials',
        'admins/photos',
        'admission',
        'general',
        'temp',
        'standard_exams',
        'log/admin',
        'log/superadmin'
    ]
    for sub in subfolders:
        full_path = os.path.join(data_path, sub)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"    Created: {sub}")
    print("[SUCCESS] Data folders initialized.")

def init_database():
    # 1. Load project root and .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, 'admin', 'backend', '.env')
    schema_path = os.path.join(project_root, 'admin', 'database', 'schema.sql')
    
    if not os.path.exists(env_path):
        print(f"[ERROR] .env file not found at {env_path}")
        return False
        
    load_dotenv(env_path)
    
    # 2. Extract DB credentials
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "nta_portal")
    
    print(f"[*] Connecting to MySQL at {db_host} as {db_user}...")
    
    try:
        # Connect without database first to create it
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 3. Create Database
        print(f"[*] Ensuring database '{db_name}' exists...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {db_name}")
        
        # 4. Read and Execute Schema
        if os.path.exists(schema_path):
            print(f"[*] Executing schema from {schema_path}...")
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                
            # For better reliability, we execute statements one by one
            # Use multi=True if possible or split carefully
            try:
                for result in cursor.execute(schema_sql, multi=True):
                    pass
                conn.commit()
                print("[SUCCESS] Database schema initialized.")
            except Exception as e:
                # Fallback to simple split if multi=True fails for some reason
                statements = schema_sql.split(';')
                for statement in statements:
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except mysql.connector.Error as err:
                            if "already exists" in str(err).lower():
                                continue
                            print(f"    [Warning] Statement failed: {err}")
                conn.commit()
                print("[SUCCESS] Database schema initialized (via fallback split).")
        else:
            print(f"[ERROR] Schema file not found at {schema_path}")
            return False
            
        cursor.close()
        conn.close()

        # 5. Initialize Data Folders
        init_data_folders(project_root)
        
        return True
        
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL Connection failed: {err}")
        print("        Please ensure MySQL is running and credentials in .env are correct.")
        return False

if __name__ == "__main__":
    if init_database():
        print("\n[INFO] You can now run seed_fake_data.py to populate the portal.")
        print("[INFO] POST-SETUP MIGRATION: run deploy/fix_stage_reviews_fk.py to change the")
        print("       stage_reviews.trainee_id FK from ON DELETE CASCADE to ON DELETE SET NULL.")
        print("       This preserves audit trail rows when rejected trainees are deleted.")
    else:
        exit(1)
