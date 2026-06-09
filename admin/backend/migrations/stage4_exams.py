import mysql.connector
import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'admin', 'backend'))

try:
    from core.database import get_db_connection
    db = get_db_connection()
    cursor = db.cursor()
    
    # 1. Create exams table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject ENUM('arabic', 'english', 'public_knowledge') NOT NULL,
            title VARCHAR(255) NOT NULL,
            content_json JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    # 2. Create trainee_exam_submissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trainee_exam_submissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            trainee_id INT NOT NULL,
            subject ENUM('arabic', 'english', 'public_knowledge') NOT NULL,
            answers_json JSON NOT NULL,
            score DECIMAL(5,2),
            processed_results JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    
    db.commit()
    print("Stage 4 Exam tables created successfully.")
    
    # 3. Seed exams from JSON files
    import json
    subjects = ['arabic', 'english', 'public_knowledge']
    for sub in subjects:
        file_path = f"data/standard_exams/{sub}.json"
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cursor.execute("SELECT id FROM exams WHERE subject = %s", (sub,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute(
                        "INSERT INTO exams (subject, title, content_json) VALUES (%s, %s, %s)",
                        (sub, data['title'], json.dumps(data, ensure_ascii=False))
                    )
                    print(f"Seeded {sub} exam.")
                else:
                    cursor.execute(
                        "UPDATE exams SET title = %s, content_json = %s WHERE subject = %s",
                        (data['title'], json.dumps(data, ensure_ascii=False), sub)
                    )
                    print(f"Updated {sub} exam.")
    
    db.commit()
    cursor.close()
    db.close()
except Exception as e:
    print(f"Error: {e}")
