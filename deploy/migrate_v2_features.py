"""
Migration: v2 features
Run once: python deploy/migrate_v2_features.py
"""
import os
import mysql.connector
from dotenv import load_dotenv

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
env_path = os.path.join(project_root, "admin", "backend", ".env")
load_dotenv(env_path)

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "nta_portal"),
    charset="utf8mb4",
)
cursor = conn.cursor()

STATEMENTS = [
    # ── Feature 1: Registration Step Lock/Unlock ──
    """
    CREATE TABLE IF NOT EXISTS `registration_step_settings` (
      `id` int NOT NULL AUTO_INCREMENT,
      `step_key` varchar(20) NOT NULL,
      `title_ar` varchar(255) NOT NULL,
      `step_order` int NOT NULL,
      `is_locked` tinyint(1) NOT NULL DEFAULT 0,
      `updated_by` int DEFAULT NULL,
      `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `step_key` (`step_key`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # ── Feature 2: Course Materials ──
    """
    CREATE TABLE IF NOT EXISTS `course_materials` (
      `id` int NOT NULL AUTO_INCREMENT,
      `course_id` int NOT NULL,
      `file_name` varchar(255) NOT NULL,
      `file_path` varchar(512) NOT NULL,
      `file_type` varchar(50) DEFAULT NULL,
      `file_size` bigint DEFAULT NULL,
      `category` enum('technical','financial','political','supporting') NOT NULL DEFAULT 'supporting',
      `uploader_id` int NOT NULL,
      `status` enum('active','archived') NOT NULL DEFAULT 'active',
      `description` text DEFAULT NULL,
      `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      KEY `course_id` (`course_id`),
      KEY `uploader_id` (`uploader_id`),
      CONSTRAINT `course_materials_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
      CONSTRAINT `course_materials_ibfk_2` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # ── Feature 3: Course Planning ──
    """
    CREATE TABLE IF NOT EXISTS `course_planning` (
      `id` int NOT NULL AUTO_INCREMENT,
      `course_id` int NOT NULL,
      `domain` enum('technical','financial','political','other') DEFAULT 'other',
      `tags` json DEFAULT NULL,
      `level` varchar(100) DEFAULT NULL,
      `start_date` date DEFAULT NULL,
      `end_date` date DEFAULT NULL,
      `schedule_json` json DEFAULT NULL,
      `instructor` varchar(255) DEFAULT NULL,
      `capacity` int DEFAULT NULL,
      `prerequisites` text DEFAULT NULL,
      `syllabus` text DEFAULT NULL,
      `outcomes` text DEFAULT NULL,
      `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
      `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`),
      UNIQUE KEY `course_id` (`course_id`),
      CONSTRAINT `course_planning_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # ── Feature 5: Dynamic Admissions Builder ──
    """
    CREATE TABLE IF NOT EXISTS `admission_sections` (
      `id` int NOT NULL AUTO_INCREMENT,
      `title_ar` varchar(255) NOT NULL,
      `section_type` enum('quiz','documents','essay','interview','info') NOT NULL DEFAULT 'info',
      `config_json` json DEFAULT NULL,
      `sort_order` int NOT NULL DEFAULT 0,
      `is_active` tinyint(1) NOT NULL DEFAULT 1,
      `created_by` int DEFAULT NULL,
      `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
      `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      PRIMARY KEY (`id`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    """
    CREATE TABLE IF NOT EXISTS `applicant_submissions` (
      `id` int NOT NULL AUTO_INCREMENT,
      `user_id` int NOT NULL,
      `section_id` int NOT NULL,
      `answers_json` json DEFAULT NULL,
      `uploaded_files` json DEFAULT NULL,
      `score` decimal(5,2) DEFAULT NULL,
      `status` enum('pending','submitted','reviewed','passed','failed') NOT NULL DEFAULT 'pending',
      `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
      `reviewed_at` timestamp NULL DEFAULT NULL,
      `reviewer_id` int DEFAULT NULL,
      PRIMARY KEY (`id`),
      UNIQUE KEY `unique_submission` (`user_id`,`section_id`),
      KEY `section_id` (`section_id`),
      CONSTRAINT `applicant_submissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
      CONSTRAINT `applicant_submissions_ibfk_2` FOREIGN KEY (`section_id`) REFERENCES `admission_sections` (`id`) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]

DEFAULT_STEPS = [
    ("step_1",  "المعلومات الشخصية",        1),
    ("step_2",  "بيانات الهوية",            2),
    ("step_3",  "المعلومات العائلية",        3),
    ("step_4",  "المؤهل التعليمي",          4),
    ("step_5",  "المهارات والكفاءات",        5),
    ("step_6",  "الخبرة المهنية",            6),
    ("step_7",  "اللغات",                   7),
    ("step_8",  "المستندات والمرفقات",       8),
    ("step_9",  "التحفيز والأهداف",          9),
    ("step_10", "المراجعة والتأكيد",         10),
]

for sql in STATEMENTS:
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"[OK] Executed statement")
    except mysql.connector.Error as e:
        if "already exists" in str(e).lower():
            print(f"[SKIP] Already exists")
        else:
            print(f"[ERROR] {e}")

for key, title, order in DEFAULT_STEPS:
    try:
        cursor.execute(
            "INSERT IGNORE INTO registration_step_settings (step_key, title_ar, step_order) VALUES (%s, %s, %s)",
            (key, title, order),
        )
    except mysql.connector.Error as e:
        print(f"[ERROR] seed step {key}: {e}")

conn.commit()
print("[DONE] All migration steps complete.")
cursor.close()
conn.close()
