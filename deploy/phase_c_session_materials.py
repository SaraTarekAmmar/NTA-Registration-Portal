"""
Phase C migration (non-destructive):
  - add content columns to course_sessions (description, content, objectives, notes)
  - create session_materials link table (UNIQUE session_id+material_id)
Idempotent: safe to run multiple times. Never drops or deletes data.
Run from editor/backend context for DB access, or standalone if path set.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "editor" / "backend"))
from core.database import get_db_connection  # noqa: E402


def column_exists(cur, table, column):
    cur.execute(
        """SELECT COUNT(*) FROM information_schema.COLUMNS
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME=%s""",
        (table, column),
    )
    return cur.fetchone()[0] > 0


def table_exists(cur, table):
    cur.execute(
        """SELECT COUNT(*) FROM information_schema.TABLES
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME=%s""",
        (table,),
    )
    return cur.fetchone()[0] > 0


def main():
    db = get_db_connection()
    cur = db.cursor()
    try:
        # 1. course_sessions content columns
        for col in ("description", "content", "objectives", "notes"):
            if not column_exists(cur, "course_sessions", col):
                cur.execute(f"ALTER TABLE course_sessions ADD COLUMN {col} TEXT NULL")
                print(f"  + course_sessions.{col} added")
            else:
                print(f"  = course_sessions.{col} already present")

        # 2. session_materials link table
        if not table_exists(cur, "session_materials"):
            cur.execute(
                """
                CREATE TABLE session_materials (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    material_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_session_material (session_id, material_id),
                    KEY idx_session (session_id),
                    KEY idx_material (material_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
            print("  + session_materials table created")
        else:
            print("  = session_materials table already present")

        db.commit()
        print("Phase C migration complete.")
    finally:
        cur.close()
        db.close()


if __name__ == "__main__":
    main()
