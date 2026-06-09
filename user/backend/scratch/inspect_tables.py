import os
import sys
from dotenv import load_dotenv
from mysql.connector import pooling

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def inspect_tables():
    conn = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=1, **db_config).get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        print("--- GRADES MASTER ---")
        cursor.execute("SELECT * FROM grades_master")
        for row in cursor.fetchall():
            print(f"ID: {row.get('id')}, Code: {row.get('code')}, Name AR: '{row.get('name_ar')}', Type: {row.get('type')}")
        
        print("\n--- DEGREE LEVELS MASTER ---")
        cursor.execute("SELECT * FROM degree_levels_master")
        for row in cursor.fetchall():
            print(f"ID: {row.get('id')}, Code: {row.get('code')}, Name AR: '{row.get('name_ar')}', Type: {row.get('type')}")

        print("\n--- JOB TITLES ---")
        cursor.execute("SELECT * FROM job_titles_master")
        for row in cursor.fetchall():
            print(f"ID: {row.get('id')}, Name AR: '{row.get('name_ar')}', Sector: {row.get('sector')}")

        print("\n--- LANGUAGES ---")
        cursor.execute("SELECT * FROM languages_master")
        for row in cursor.fetchall():
            if row.get('name_ar') in ['العربية', 'الإنجليزية', 'الفرنسية']:
                print(f"ID: {row.get('id')}, Code: {row.get('code')}, Name AR: '{row.get('name_ar')}'")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    inspect_tables()
