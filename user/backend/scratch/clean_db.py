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

def clean_duplicates():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Clean identity_doc_types_master
    print("Cleaning identity_doc_types_master duplicates...")
    cursor.execute("""
        DELETE t1 FROM identity_doc_types_master t1
        INNER JOIN identity_doc_types_master t2 
        WHERE t1.id > t2.id AND t1.code = t2.code
    """)
    print(f"  Rows deleted: {cursor.rowcount}")
    
    # Clean military_status_master just in case
    print("Cleaning military_status_master duplicates...")
    # Since military_status_master doesn't have a 'code' column (checked earlier, it has id, name_en, name_ar)
    # we use name_en
    cursor.execute("""
        DELETE t1 FROM military_status_master t1
        INNER JOIN military_status_master t2 
        WHERE t1.id > t2.id AND t1.name_en = t2.name_en
    """)
    print(f"  Rows deleted: {cursor.rowcount}")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    clean_duplicates()
