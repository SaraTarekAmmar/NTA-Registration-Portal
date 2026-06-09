from core.database import get_db_connection

def find_python_trainees():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.id, u.full_name_ar, c.title 
            FROM users u 
            JOIN applications a ON u.id = a.user_id 
            JOIN courses c ON a.course_id = c.id 
            WHERE c.title LIKE '%Python%' OR c.title LIKE '%بايثون%'
        """)
        results = cursor.fetchall()
        for r in results:
            # Print only ID to avoid encoding issues with Arabic names in console
            print(f"ID: {r['id']} | Course: {r['title']}")
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    find_python_trainees()
