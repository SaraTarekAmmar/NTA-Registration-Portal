import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Ensure stdout handles UTF-8
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def check_id_docs():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM identity_doc_types_master")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_id_docs()
