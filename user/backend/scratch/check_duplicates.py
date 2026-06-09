import asyncio
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

tables = [
    "countries_master",
    "degree_levels_master",
    "grades_master",
    "ministries_master",
    "job_titles_master",
    "marital_status_master",
    "monthly_income_master",
    "interests_master",
    "languages_master"
]

def check_duplicates():
    conn = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=1, **db_config).get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        for t in tables:
            # Check duplicates by name_ar or name_en
            query = f"SELECT name_ar, COUNT(*) as cnt FROM {t} GROUP BY name_ar HAVING cnt > 1"
            cursor.execute(query)
            dups = cursor.fetchall()
            if dups:
                print(f"Table {t} has duplicate Arabic names:")
                for d in dups:
                    print(f"  - '{d['name_ar']}' appears {d['cnt']} times")
            else:
                print(f"Table {t} has no duplicate Arabic names.")
                
        # Audit universities_master
        cursor.execute("SELECT country_id, name_en, COUNT(*) as cnt FROM universities_master GROUP BY country_id, name_en HAVING cnt > 1")
        univ_dups = cursor.fetchall()
        if univ_dups:
            print("Table universities_master has duplicates:")
            for d in univ_dups:
                print(f"  - Country ID {d['country_id']}, Name: '{d['name_en']}' appears {d['cnt']} times")
        else:
            print("Table universities_master has no duplicates.")

        # Audit university_colleges
        cursor.execute("SELECT university_id, name_en, COUNT(*) as cnt FROM university_colleges GROUP BY university_id, name_en HAVING cnt > 1")
        coll_dups = cursor.fetchall()
        if coll_dups:
            print("Table university_colleges has duplicates:")
            for d in coll_dups:
                print(f"  - University ID {d['university_id']}, Name: '{d['name_en']}' appears {d['cnt']} times")
        else:
            print("Table university_colleges has no duplicates.")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_duplicates()
