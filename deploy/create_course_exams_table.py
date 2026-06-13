"""Create the course_exams table used by the editor exams feature.

The legacy `exams` table is a fixed 3-subject entrance-exam store
(subject ENUM('arabic','english','public_knowledge')) and cannot hold
course-linked editor exams. This table backs editor/backend/routers/exams.py.

Run once manually:  python deploy/create_course_exams_table.py
"""
import sys
from pathlib import Path

# Reuse the editor backend's env-based DB connection (no hardcoded secrets).
EDITOR_BACKEND = Path(__file__).resolve().parent.parent / "editor" / "backend"
sys.path.insert(0, str(EDITOR_BACKEND))

from core.database import get_db_connection

SQL = """
CREATE TABLE IF NOT EXISTS course_exams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(120) NOT NULL UNIQUE,
    course_id INT NOT NULL,
    title VARCHAR(255),
    title_ar VARCHAR(255),
    duration_minutes INT DEFAULT 60,
    pass_score INT DEFAULT 60,
    status VARCHAR(20) DEFAULT 'draft',
    content_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_course_exams_course (course_id)
);
"""

if __name__ == "__main__":
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute(SQL)
        db.commit()
        print("Table course_exams created (or already exists).")
    finally:
        cursor.close()
        db.close()
