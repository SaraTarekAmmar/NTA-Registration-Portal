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

def get_country_ids():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, name_en FROM countries_master WHERE name_en IN ('Egypt', 'United Kingdom')")
    for row in cursor.fetchall():
        print(f"Name: {row['name_en']}, ID: {row['id']}")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    get_country_ids()
