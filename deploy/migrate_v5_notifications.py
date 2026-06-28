import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "admin", "backend"))
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "admin", "backend", ".env"))
from core.database import get_db_connection


def migrate():
    db = get_db_connection()
    c = db.cursor()

    print("Creating notifications table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        title_ar VARCHAR(300) NOT NULL,
        message_ar TEXT NOT NULL,
        notification_type ENUM('status_change', 'email_sent', 'document_required', 'stage_update', 'system') NOT NULL DEFAULT 'system',
        related_application_id INT NULL,
        related_stage VARCHAR(100) NULL,
        is_read TINYINT(1) DEFAULT 0,
        read_at DATETIME NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_notifications (user_id, is_read, created_at DESC),
        INDEX idx_application (related_application_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (related_application_id) REFERENCES applications(id) ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    print("Creating applicant_status table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS applicant_status (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        current_stage VARCHAR(100) NOT NULL DEFAULT 'electronic_screening',
        overall_status ENUM('pending', 'in_progress', 'accepted', 'rejected', 'waitlisted') NOT NULL DEFAULT 'pending',
        status_notes TEXT NULL,
        last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_application_status (application_id),
        FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    db.commit()
    print("Migration v5 (Notifications & Applicant Status) complete.")
    db.close()


if __name__ == "__main__":
    migrate()
