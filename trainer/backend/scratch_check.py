from core.database import get_db_connection
import json
import sys

# Ensure UTF-8 output for Arabic text
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

db = get_db_connection()
cursor = db.cursor(dictionary=True)

print("--- trainee_profiles schema ---")
cursor.execute("DESCRIBE trainee_profiles")
for row in cursor.fetchall():
    print(row)

print("\n--- courses schema ---")
cursor.execute("DESCRIBE courses")
for row in cursor.fetchall():
    print(row)

print("\n--- Python Trainees ---")
# Using title instead of name based on previous errors and likely schema
cursor.execute("""
    SELECT u.id, u.full_name_ar 
    FROM users u 
    JOIN applications a ON u.id = a.user_id 
    JOIN courses c ON a.course_id = c.id 
    WHERE c.title LIKE '%Python%' AND u.role = 'trainee'
""")
trainees = cursor.fetchall()
for t in trainees:
    print(t)

db.close()
