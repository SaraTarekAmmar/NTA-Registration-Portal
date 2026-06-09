import os
import json
import mysql.connector
from dotenv import load_dotenv

def seed_exams():
    # 1. Load .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, 'admin', 'backend', '.env')
    
    if not os.path.exists(env_path):
        print(f"[ERROR] .env file not found at {env_path}")
        return
        
    load_dotenv(env_path)
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "nta_portal")
    
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            charset='utf8mb4'
        )
        cursor = conn.cursor(dictionary=True)
        
        print(f"[*] Seeding Stage 4 Exams into '{db_name}'...")
        
        subjects = ['arabic', 'english', 'public_knowledge']
        data_dir = os.path.join(project_root, 'data', 'standard_exams')
        
        if not os.path.exists(data_dir):
            print(f"[ERROR] Data directory not found: {data_dir}")
            return

        for sub in subjects:
            file_path = os.path.join(data_dir, f"{sub}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Check if exists
                    cursor.execute("SELECT id FROM exams WHERE subject = %s", (sub,))
                    existing = cursor.fetchone()
                    
                    if not existing:
                        cursor.execute(
                            "INSERT INTO exams (subject, title, content_json) VALUES (%s, %s, %s)",
                            (sub, data['title'], json.dumps(data, ensure_ascii=False))
                        )
                        print(f"    [+] Seeded: {sub}")
                    else:
                        cursor.execute(
                            "UPDATE exams SET title = %s, content_json = %s WHERE subject = %s",
                            (data['title'], json.dumps(data, ensure_ascii=False), sub)
                        )
                        print(f"    [~] Updated: {sub}")
            else:
                print(f"    [!] Skipping: {file_path} not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("[SUCCESS] Exam seeding completed.")
        
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL Error: {err}")

if __name__ == "__main__":
    seed_exams()
