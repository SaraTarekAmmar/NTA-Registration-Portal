import mysql.connector

conn = mysql.connector.connect(
    host="localhost", user="root", password="sara@16112000", database="nta_portal"
)
cursor = conn.cursor(dictionary=True)
cursor.execute(
    "SELECT id, email, role, national_id, is_active, full_name_ar FROM users WHERE role IN ('admin', 'editor') OR email IN ('admin@example.com', 'editor')"
)
for row in cursor.fetchall():
    print(row)
cursor.close()
conn.close()
