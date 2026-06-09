import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path

# Absolute path to .env
base_dir = Path(__file__).parent
env_path = base_dir / "user" / "backend" / ".env"
load_dotenv(dotenv_path=env_path)

def migrate():
    try:
        print(f"Loading .env from: {env_path}")
        host = os.getenv('DB_HOST', '127.0.0.1')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        database = os.getenv('DB_NAME')
        port = int(os.getenv('DB_PORT', 3306))

        print(f"Connecting to {host}:{port} as {user}...")
        
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        cursor = conn.cursor()
        
        print("Checking for existing index...")
        cursor.execute("""
            SELECT COUNT(1) 
            FROM information_schema.statistics 
            WHERE table_schema = %s 
            AND table_name = 'applications' 
            AND index_name = 'idx_user_course'
        """, (database,))
        
        if cursor.fetchone()[0] == 0:
            print("Cleaning up pre-existing duplicates in applications table...")
            # Keep only the row with the lowest ID for each (user_id, course_id)
            cursor.execute("""
                DELETE a1 FROM applications a1
                INNER JOIN applications a2 
                WHERE a1.id > a2.id 
                AND a1.user_id = a2.user_id 
                AND a1.course_id = a2.course_id
            """)
            conn.commit()
            print(f"Removed {cursor.rowcount} duplicate rows.")

            print("Adding UNIQUE INDEX idx_user_course (user_id, course_id) to applications table...")
            cursor.execute("ALTER TABLE applications ADD UNIQUE INDEX idx_user_course (user_id, course_id)")
            conn.commit()
            print("Successfully added unique index.")
        else:
            print("Index already exists.")
            
        cursor.close()
        conn.close()
        print("Done.")
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
