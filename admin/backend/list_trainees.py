from core.database import get_db_connection
import json

db = get_db_connection()
cursor = db.cursor(dictionary=True)
cursor.execute("SELECT id, full_name_ar FROM users WHERE role = 'trainee'")
rows = cursor.fetchall()
for row in rows:
    print(f"{row['id']}: {repr(row['full_name_ar'])}")
db.close()
