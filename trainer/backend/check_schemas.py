from core.database import get_db_connection
import sys

db = get_db_connection()
cursor = db.cursor(dictionary=True)

print("--- assignment_submissions ---")
cursor.execute("DESCRIBE assignment_submissions")
for row in cursor.fetchall():
    print(row)

print("\n--- attendance_logs ---")
cursor.execute("DESCRIBE attendance_logs")
for row in cursor.fetchall():
    print(row)

db.close()
