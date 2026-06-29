"""
Migration: Add admission_manager role to users.role ENUM.

Safe to run multiple times. Never drops data.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "admin" / "backend"))

from dotenv import load_dotenv

load_dotenv(str(Path(__file__).resolve().parent.parent / "admin" / "backend" / ".env"))

import mysql.connector


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
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "nta_portal"),
        charset="utf8mb4",
    )
    cur = db.cursor(dictionary=True)
    try:
        print("[Phase 1] Database migration for admission manager role...")

        if not enum_has_value(cur, "users", "role", "admission_manager"):
            print("  + Adding 'admission_manager' to users.role ENUM...")
            cur.execute(
                """ALTER TABLE users MODIFY COLUMN role
                   ENUM('trainee','admin','editor','superadmin','trainer','applicant','coordinator','committee_member','admission_manager')
                   COLLATE utf8mb4_unicode_ci NOT NULL"""
            )
            print("  [ok] users.role ENUM updated")
        else:
            print("  = users.role already has 'admission_manager'")

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
