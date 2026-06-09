import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def check_lookup_tables():
    tables_to_check = [
        "interests_master", "languages_master", "countries_master",
        "universities_master", "states_master", "skill_categories",
        "skill_subcategories", "skills_master", "military_status_master",
        "identity_doc_types_master", "degree_levels_master", "grades_master",
        "ministries_master", "job_titles_master", "marital_status_master",
        "monthly_income_master"
    ]
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SHOW TABLES")
    existing_tables = [t[0] for t in cursor.fetchall()]
    
    print("Checking lookup tables:")
    for table in tables_to_check:
        status = "EXISTS" if table in existing_tables else "MISSING"
        print(f"  {table}: {status}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_lookup_tables()
