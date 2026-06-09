import os
import sys
from dotenv import load_dotenv
import mysql.connector

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def main():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        # Check if column already exists in trainee_standardized_tests
        cursor.execute("SHOW COLUMNS FROM trainee_standardized_tests LIKE 'verification_url'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE trainee_standardized_tests ADD COLUMN verification_url VARCHAR(512) DEFAULT NULL")
            print("Added verification_url column to trainee_standardized_tests.")
        else:
            print("verification_url column already exists in trainee_standardized_tests.")

        # Check if column already exists in trainer_standardized_tests
        cursor.execute("SHOW COLUMNS FROM trainer_standardized_tests LIKE 'verification_url'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE trainer_standardized_tests ADD COLUMN verification_url VARCHAR(512) DEFAULT NULL")
            print("Added verification_url column to trainer_standardized_tests.")
        else:
            print("verification_url column already exists in trainer_standardized_tests.")

        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error executing migration: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
