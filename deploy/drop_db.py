import os
import mysql.connector
from dotenv import load_dotenv

def drop_database():
    # Load .env
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    env_path = os.path.join(project_root, 'admin', 'backend', '.env')
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASSWORD", "OmarNour@Work161996")
    db_name = os.getenv("DB_NAME", "nta_portal")
    
    try:
        print(f"[*] Connecting to MySQL at {db_host} as {db_user}...")
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass
        )
        cursor = conn.cursor()
        
        print(f"[*] Dropping database '{db_name}' if it exists...")
        cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
        
        conn.commit()
        print("[SUCCESS] Database has been completely removed!")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"[ERROR] Failed to drop database: {err}")

if __name__ == "__main__":
    drop_database()
