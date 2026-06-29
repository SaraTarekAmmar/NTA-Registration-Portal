#!/usr/bin/env python3
"""
Run this once to create all front_* tables in nta_portal.
Usage: python init_front_db.py
"""
import os, sys
from pathlib import Path

# Load .env from backend/
env_path = Path(__file__).parent.parent / ".env"
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path)

import mysql.connector

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "nta_portal"),
    charset="utf8mb4"
)

sql_file = Path(__file__).parent / "create_tables.sql"
sql = sql_file.read_text(encoding="utf-8")

cursor = conn.cursor()
for statement in sql.split(";"):
    stmt = statement.strip()
    if stmt and not stmt.startswith("--"):
        try:
            cursor.execute(stmt)
            conn.commit()
        except mysql.connector.Error as e:
            print(f"[WARN] {e}")

cursor.close()
conn.close()
print("[OK] Front page tables created/verified.")
