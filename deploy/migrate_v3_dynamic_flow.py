import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend', '.env'))
from core.database import get_db_connection

db = get_db_connection()
c = db.cursor()

# ── Tables ────────────────────────────────────────────────────────

c.execute("""
CREATE TABLE IF NOT EXISTS flow_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_type VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active TINYINT(1) DEFAULT 1,
    created_by INT,
    updated_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_course_type (course_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""")

c.execute("""
CREATE TABLE IF NOT EXISTS flow_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    flow_template_id INT NOT NULL,
    step_key VARCHAR(100) NOT NULL,
    step_type VARCHAR(50) NOT NULL DEFAULT 'personal_info',
    title_ar VARCHAR(300) NOT NULL,
    description_ar TEXT,
    step_order INT DEFAULT 0,
    is_required TINYINT(1) DEFAULT 1,
    is_active TINYINT(1) DEFAULT 1,
    visibility_rules JSON,
    unlock_rules JSON,
    config_json JSON,
    created_by INT,
    updated_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_template_order (flow_template_id, step_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""")

c.execute("""
CREATE TABLE IF NOT EXISTS applicant_step_overrides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    step_id INT NOT NULL,
    is_visible TINYINT(1) DEFAULT NULL,
    is_locked TINYINT(1) DEFAULT NULL,
    is_required TINYINT(1) DEFAULT NULL,
    custom_config JSON,
    reason TEXT,
    created_by INT,
    updated_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_applicant_step (applicant_id, step_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""")

c.execute("""
CREATE TABLE IF NOT EXISTS applicant_step_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    applicant_id INT NOT NULL,
    step_id INT NOT NULL,
    status ENUM('pending','in_progress','submitted','approved','rejected','skipped') DEFAULT 'pending',
    completed_at DATETIME,
    locked_reason VARCHAR(500),
    submitted_data JSON,
    reviewed_by INT,
    reviewed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_applicant_step_status (applicant_id, step_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
""")

db.commit()
print("Tables created OK")

# ── Seed default templates ────────────────────────────────────────

STEP_TYPES = {
    "step_1":  ("personal_info",      "المعلومات الشخصية"),
    "step_2":  ("document_upload",    "بيانات الهوية"),
    "step_3":  ("personal_info",      "المعلومات العائلية"),
    "step_4":  ("personal_info",      "المؤهل التعليمي"),
    "step_5":  ("personal_info",      "المهارات والخبرات"),
    "step_6":  ("personal_info",      "بيانات العمل"),
    "step_7":  ("personal_info",      "الحالة الصحية"),
    "step_8":  ("personal_info",      "الخدمة العسكرية"),
    "step_9":  ("personal_info",      "بيانات الطوارئ"),
    "step_10": ("final_confirmation", "المراجعة والتأكيد"),
}

def unlock_after(prev_key):
    return json.dumps({"requires_step_key": prev_key, "requires_status": "submitted"})

# Default adult flow (all 10 steps)
DEFAULT_STEPS = [
    ("step_1",  1, None,                  None),
    ("step_2",  2, None,                  unlock_after("step_1")),
    ("step_3",  3, None,                  unlock_after("step_2")),
    ("step_4",  4, None,                  unlock_after("step_3")),
    ("step_5",  5, None,                  unlock_after("step_4")),
    ("step_6",  6, None,                  unlock_after("step_5")),
    ("step_7",  7, None,                  unlock_after("step_6")),
    ("step_8",  8, None,                  unlock_after("step_7")),
    ("step_9",  9, None,                  unlock_after("step_8")),
    ("step_10",10, None,                  unlock_after("step_9")),
]

# Youth flow: simplified registration — personal data, contact, education, final confirmation
# Skips work experience, legal/political, logistics, and cognitive test unless admin adds them
YOUTH_STEPS = [
    ("step_1",  1, None, None),
    ("step_2",  2, None, unlock_after("step_1")),
    ("step_3",  3, None, unlock_after("step_2")),
    ("step_10", 4, None, unlock_after("step_3")),
]

# Financial/Political: full flow, steps 7 & 8 age-gated (18+)
FULL_WITH_AGE_STEPS = [
    ("step_1",  1, None,                  None),
    ("step_2",  2, None,                  unlock_after("step_1")),
    ("step_3",  3, None,                  unlock_after("step_2")),
    ("step_4",  4, None,                  unlock_after("step_3")),
    ("step_5",  5, None,                  unlock_after("step_4")),
    ("step_6",  6, None,                  unlock_after("step_5")),
    ("step_7",  7, json.dumps({"age_min": 18}), unlock_after("step_6")),
    ("step_8",  8, json.dumps({"age_min": 18}), unlock_after("step_7")),
    ("step_9",  9, None,                  unlock_after("step_8")),
    ("step_10",10, None,                  unlock_after("step_9")),
]

# Workshop / Bootcamp: lighter flow (skip military, health for short programs)
WORKSHOP_STEPS = [
    ("step_1",  1, None,                  None),
    ("step_2",  2, None,                  unlock_after("step_1")),
    ("step_4",  3, None,                  unlock_after("step_2")),
    ("step_5",  4, None,                  unlock_after("step_4")),
    ("step_9",  5, None,                  unlock_after("step_5")),
    ("step_10", 6, None,                  unlock_after("step_9")),
]

TEMPLATES = [
    ("default",    "التدفق الافتراضي",        DEFAULT_STEPS),
    ("youth",      "دورة الشباب",             YOUTH_STEPS),
    ("financial",  "الدورة المالية",          FULL_WITH_AGE_STEPS),
    ("political",  "الدورة السياسية",         FULL_WITH_AGE_STEPS),
    ("technical",  "الدورة التقنية",          DEFAULT_STEPS),
    ("workshop",   "ورشة عمل",               WORKSHOP_STEPS),
    ("bootcamp",   "معسكر تدريبي",           WORKSHOP_STEPS),
    ("online",     "دورة اونلاين",            WORKSHOP_STEPS),
]

for course_type, name, step_list in TEMPLATES:
    c.execute("SELECT id FROM flow_templates WHERE course_type=%s", (course_type,))
    if c.fetchone():
        print(f"Template {course_type}: already exists, skip")
        continue

    c.execute(
        "INSERT INTO flow_templates (course_type, name, is_active) VALUES (%s, %s, 1)",
        (course_type, name)
    )
    tmpl_id = c.lastrowid

    for step_key, order, vis_rules, unlock_rules in step_list:
        step_type, title_ar = STEP_TYPES[step_key]
        c.execute("""
            INSERT INTO flow_steps
              (flow_template_id, step_key, step_type, title_ar, step_order,
               is_required, is_active, visibility_rules, unlock_rules)
            VALUES (%s,%s,%s,%s,%s,1,1,%s,%s)
        """, (tmpl_id, step_key, step_type, title_ar, order, vis_rules, unlock_rules))

    db.commit()
    print(f"Created template '{course_type}' with {len(step_list)} steps")

db.close()
print("Migration v3 complete.")
