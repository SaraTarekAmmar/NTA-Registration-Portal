import mysql.connector

DB_CONFIG = dict(
    host="localhost",
    port=3306,
    user="root",
    password="OmarNour@Work161996",
    database="nta_portal",
)

SQL = """
CREATE TABLE IF NOT EXISTS cv_matching_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    national_id VARCHAR(14) NOT NULL,
    match_score FLOAT,
    evidence TEXT,
    analysis_json JSON,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY (course_id, national_id)
);
"""

try:
    db = mysql.connector.connect(**DB_CONFIG)
    cur = db.cursor()
    cur.execute(SQL)
    db.commit()
    print("Table cv_matching_results created successfully")
    cur.close()
    db.close()
except Exception as e:
    print(f"Error: {e}")
