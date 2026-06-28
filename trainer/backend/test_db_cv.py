from core.database import get_db_connection
conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

print("CV Results:")
cursor.execute('SELECT id, course_id, national_id, match_score FROM cv_matching_results ORDER BY id DESC LIMIT 10')
rows = cursor.fetchall()
for r in rows: print(r)

print("\nUsers App:")
cursor.execute("SELECT u.id as u_id, u.national_id, a.course_id FROM users u JOIN applications a ON u.id = a.user_id WHERE a.status='approved' LIMIT 5")
rows = cursor.fetchall()
for r in rows: print(r)

conn.close()
