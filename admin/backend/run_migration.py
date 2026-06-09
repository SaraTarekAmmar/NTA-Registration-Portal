"""
One-time migration: add 5 new nullable columns to the courses table
to support the new 3-step course wizard UI.
Safe to re-run — checks information_schema before each ALTER.
"""
import sys
import mysql.connector

DB_CONFIG = dict(
    host="localhost",
    port=3306,
    user="root",
    password="OmarNour@Work161996",
    database="nta_portal",
)

# (column_name, ALTER TABLE statement to run if column is missing)
COLUMNS = [
    ("title_ar",        "ALTER TABLE courses ADD COLUMN title_ar VARCHAR(255) NULL AFTER title"),
    ("short_name",      "ALTER TABLE courses ADD COLUMN short_name VARCHAR(100) NULL AFTER title_ar"),
    ("classification",  "ALTER TABLE courses ADD COLUMN classification VARCHAR(100) NULL AFTER short_name"),
    ("stages_json",     "ALTER TABLE courses ADD COLUMN stages_json JSON NULL AFTER classification"),
    ("batch_data_json", "ALTER TABLE courses ADD COLUMN batch_data_json JSON NULL AFTER stages_json"),
]

EXISTS_QUERY = """
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'courses' AND COLUMN_NAME = %s
"""

try:
    db = mysql.connector.connect(**DB_CONFIG)
    cur = db.cursor()

    for col_name, stmt in COLUMNS:
        cur.execute(EXISTS_QUERY, ("nta_portal", col_name))
        (exists,) = cur.fetchone()
        if exists:
            print(f"  SKIP (already exists): {col_name}")
        else:
            cur.execute(stmt)
            db.commit()
            print(f"  ADDED: {col_name}")

    cur.execute("DESCRIBE courses")
    cols = [row[0] for row in cur.fetchall()]
    print("\nFinal columns in `courses` table:")
    for c in cols:
        print(f"  - {c}")

    cur.close()
    db.close()
    print("\n[OK] Migration complete.")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

