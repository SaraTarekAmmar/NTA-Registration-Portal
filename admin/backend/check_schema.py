import mysql.connector
from core.database import get_db_connection

def check_schema():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("DESCRIBE stage_reviews")
    for row in cursor.fetchall():
        print(row)
    cursor.close()
    db.close()

if __name__ == "__main__":
    check_schema()
