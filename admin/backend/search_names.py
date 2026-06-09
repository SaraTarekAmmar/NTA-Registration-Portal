from core.database import get_db_connection
import json

db = get_db_connection()
cursor = db.cursor(dictionary=True)

# Mohamed Ahmed Ali
cursor.execute("SELECT id FROM users WHERE full_name_ar LIKE %s", ('%م%ح%م%د%أ%ح%م%د%ع%ل%ي%',))
rows = cursor.fetchall()
print(f"Match 1 count: {len(rows)}")
for row in rows:
    print(f"Match 1 ID: {row['id']}")

# Ahmed Mohamed Ali
cursor.execute("SELECT id FROM users WHERE full_name_ar LIKE %s", ('%أ%ح%م%د%م%ح%م%د%ع%ل%ي%',))
rows = cursor.fetchall()
print(f"Match 2 count: {len(rows)}")
for row in rows:
    print(f"Match 2 ID: {row['id']}")
db.close()
