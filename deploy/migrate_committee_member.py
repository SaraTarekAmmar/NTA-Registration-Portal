"""
Migration: Add committee_member role & update schema (idempotent).
"""
import sys
import os
from pathlib import Path

# Add backend paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "admin" / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coordinator" / "backend"))

from dotenv import load_dotenv
load_dotenv(str(Path(__file__).resolve().parent.parent / "admin" / "backend" / ".env"))

from core.database import get_db_connection

def main():
    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    try:
        print("[*] Running migration: Add 'committee_member' to users.role ENUM...")
        
        # Read migration file
        migration_file = Path(__file__).resolve().parent.parent / "database" / "migrations" / "20260625_committee_member_role.sql"
        with open(migration_file, "r", encoding="utf-8") as f:
            sql = f.read()

        cur.execute(sql)
        db.commit()
        print("[SUCCESS] ENUM updated successfully!")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        sys.exit(1)
    finally:
        cur.close()
        db.close()

if __name__ == "__main__":
    main()
