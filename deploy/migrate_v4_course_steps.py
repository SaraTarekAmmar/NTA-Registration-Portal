import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend', '.env'))
from core.database import get_db_connection

def migrate():
    db = get_db_connection()
    c = db.cursor()
    
    print("Creating course_steps table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS course_steps (
        id INT AUTO_INCREMENT PRIMARY KEY,
        course_id INT NOT NULL,
        path_type ENUM('admission', 'registration') NOT NULL,
        step_key VARCHAR(100) NOT NULL,
        step_type VARCHAR(50) NOT NULL,
        title_ar VARCHAR(300) NOT NULL,
        step_order INT DEFAULT 0,
        is_required TINYINT(1) DEFAULT 1,
        config_json JSON,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_course_path (course_id, path_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    db.commit()
    print("Migration v4 (Course Steps) complete.")
    db.close()

if __name__ == "__main__":
    migrate()
