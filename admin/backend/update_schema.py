import mysql.connector
from core.database import get_db_connection

def update_schema():
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("ALTER TABLE stage_reviews ADD COLUMN details JSON AFTER notes")
        db.commit()
        print("Schema updated successfully: added 'details' column to 'stage_reviews'")
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    update_schema()
