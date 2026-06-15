"""
Migration: Add Coordinator role & related schema changes (non-destructive, idempotent).

1. Add 'coordinator' to users.role ENUM
2. Add cover_image column to courses (if missing)
3. Ensure session content columns on course_sessions (description, content, objectives, notes)
4. Ensure session_materials link table exists
5. Ensure course_materials table exists

Safe to run multiple times. Never drops data.
"""
import sys
import os
from pathlib import Path

# Allow running standalone from deploy/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "admin" / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "editor" / "backend"))

from dotenv import load_dotenv
load_dotenv(str(Path(__file__).resolve().parent.parent / "admin" / "backend" / ".env"))

from core.database import get_db_connection


def column_exists(cur, table, column):
    cur.execute(
        """SELECT COUNT(*) AS n FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s""",
        (table, column),
    )
    row = cur.fetchone()
    return (row["n"] if isinstance(row, dict) else row[0]) > 0


def table_exists(cur, table):
    cur.execute(
        """SELECT COUNT(*) AS n FROM information_schema.TABLES
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s""",
        (table,),
    )
    row = cur.fetchone()
    return (row["n"] if isinstance(row, dict) else row[0]) > 0


def enum_has_value(cur, table, column, value):
    cur.execute(
        """SELECT COLUMN_TYPE FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s""",
        (table, column),
    )
    row = cur.fetchone()
    if not row:
        return False
    col_type = row["COLUMN_TYPE"] if isinstance(row, dict) else row[0]
    return f"'{value}'" in col_type


def main():
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    try:
        print("[Phase 1] Database migration for coordinator role...")

        # ── 1. Add 'coordinator' to users.role ENUM ──
        if not enum_has_value(cur, "users", "role", "coordinator"):
            print("  + Adding 'coordinator' to users.role ENUM...")
            cur.execute(
                """ALTER TABLE users MODIFY COLUMN role
                   ENUM('trainee','admin','editor','superadmin','trainer','applicant','coordinator')
                   COLLATE utf8mb4_unicode_ci NOT NULL"""
            )
            print("  ✓ users.role ENUM updated")
        else:
            print("  = users.role already has 'coordinator'")

        # ── 2. Add cover_image to courses ──
        if not column_exists(cur, "courses", "cover_image"):
            cur.execute("ALTER TABLE courses ADD COLUMN cover_image VARCHAR(512) NULL")
            print("  + courses.cover_image added")
        else:
            print("  = courses.cover_image already present")

        # ── 3. Session content columns ──
        for col in ("description", "content", "objectives", "notes"):
            if not column_exists(cur, "course_sessions", col):
                cur.execute(f"ALTER TABLE course_sessions ADD COLUMN {col} TEXT NULL")
                print(f"  + course_sessions.{col} added")
            else:
                print(f"  = course_sessions.{col} already present")

        # ── 4. session_materials link table ──
        if not table_exists(cur, "session_materials"):
            cur.execute("""
                CREATE TABLE session_materials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    material_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_session_material (session_id, material_id),
                    KEY idx_session (session_id),
                    KEY idx_material (material_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("  + session_materials table created")
        else:
            print("  = session_materials table already present")

        # ── 5. course_materials table ──
        if not table_exists(cur, "course_materials"):
            cur.execute("""
                CREATE TABLE course_materials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    course_id INT NOT NULL,
                    file_name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(512) NOT NULL,
                    file_type VARCHAR(50) DEFAULT '',
                    file_size INT DEFAULT NULL,
                    category VARCHAR(50) DEFAULT 'supporting',
                    description TEXT NULL,
                    uploader_id INT DEFAULT NULL,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_course (course_id),
                    CONSTRAINT fk_cm_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            print("  + course_materials table created")
        else:
            print("  = course_materials table already present")

        # ── 6. Ensure chat_history.role ENUM includes coordinator ──
        if not enum_has_value(cur, "chat_history", "role", "coordinator"):
            cur.execute(
                """ALTER TABLE chat_history MODIFY COLUMN role
                   ENUM('trainee','admin','editor','coordinator')
                   COLLATE utf8mb4_unicode_ci NOT NULL"""
            )
            print("  + chat_history.role ENUM updated")
        else:
            print("  = chat_history.role already has 'coordinator'")

        db.commit()
        print("\n[SUCCESS] Migration complete.")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise
    finally:
        cur.close()
        db.close()


if __name__ == "__main__":
    main()
