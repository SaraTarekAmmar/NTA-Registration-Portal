import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend', '.env'))
from core.database import get_db_connection

def migrate():
    db = get_db_connection()
    c = db.cursor()
    
    print("Creating interview_templates table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS interview_templates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        program_type ENUM('PLP', 'Youth', 'Custom') NOT NULL DEFAULT 'Custom',
        criteria_json JSON,
        is_active TINYINT(1) DEFAULT 1,
        created_by INT,
        updated_by INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    print("Creating committee_assignments table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS committee_assignments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        committee_id INT NOT NULL,
        application_id INT NOT NULL,
        course_id INT NOT NULL,
        step_id INT NOT NULL,
        committee_member_id INT NOT NULL,
        role ENUM('Member', 'Coordinator') NOT NULL DEFAULT 'Member',
        created_by INT,
        updated_by INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_committee_assignment (application_id, step_id, committee_member_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    print("Creating committee_scores table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS committee_scores (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        course_id INT NOT NULL,
        step_id INT NOT NULL,
        committee_id INT NOT NULL,
        committee_member_id INT NOT NULL,
        criteria_scores_json JSON,
        total_score DECIMAL(5,2),
        recommendation ENUM('Accepted', 'Waitlist', 'Unsuitable'),
        notes TEXT,
        status ENUM('Draft', 'Submitted') DEFAULT 'Draft',
        submitted_at DATETIME,
        created_by INT,
        updated_by INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_committee_score (application_id, step_id, committee_member_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    print("Creating committee_final_summaries table...")
    c.execute("""
    CREATE TABLE IF NOT EXISTS committee_final_summaries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        application_id INT NOT NULL,
        course_id INT NOT NULL,
        step_id INT NOT NULL,
        committee_id INT NOT NULL,
        coordinator_id INT NOT NULL,
        average_scores_json JSON,
        final_total_score DECIMAL(5,2),
        final_recommendation ENUM('Accepted', 'Waitlist', 'Unsuitable'),
        reasons TEXT,
        notes TEXT,
        status ENUM('Draft', 'Finalized') DEFAULT 'Draft',
        submitted_at DATETIME,
        created_by INT,
        updated_by INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_committee_summary (application_id, step_id, committee_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    # Insert initial templates (PLP and Youth)
    c.execute("SELECT COUNT(*) FROM interview_templates")
    if c.fetchone()[0] == 0:
        plp_criteria = [
            {"key": "appearance", "title_ar": "المظهر العام", "title_en": "Appearance", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "motivation_enthusiasm", "title_ar": "الحماس والرغبة في المشاركة", "title_en": "Willingness to participate and enthusiasm", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "self_confidence", "title_ar": "الثقة بالنفس", "title_en": "Self-confidence", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "initiative", "title_ar": "المبادرة", "title_en": "Initiation", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "communication_skills", "title_ar": "مهارات التواصل", "title_en": "Communication skills", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "personality", "title_ar": "تقييم الشخصية", "title_en": "Personality", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "ability_to_express", "title_ar": "القدرة على التعبير عن نفسه بوضوح", "title_en": "Ability to express himself clearly", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "problem_solving", "title_ar": "حل المشكلات", "title_en": "Problem-solving", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "analytical_skills", "title_ar": "المهارات التحليلية", "title_en": "Analytical skills", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "career_goals", "title_ar": "الطموحات العملية", "title_en": "Career goals", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "presentation_skills", "title_ar": "مهارات العرض", "title_en": "Presentation skills", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "leadership", "title_ar": "القيادة", "title_en": "Leadership", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "creativity", "title_ar": "الإبداع", "title_en": "Creativity", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "decision_making", "title_ar": "اتخاذ القرار", "title_en": "Decision making", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "flexibility_adaptability", "title_ar": "المرونة والقدرة على التكيف", "title_en": "Flexibility/adaptability", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True}
        ]
        youth_criteria = [
            {"key": "appearance", "title_ar": "المظهر العام", "title_en": "Appearance", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "conversing_interacting", "title_ar": "أسلوبه في الحديث والتواصل", "title_en": "Manner of conversing and interacting", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "motivation_enthusiasm", "title_ar": "الحماس والرغبة في المشاركة", "title_en": "Willingness to participate and enthusiasm", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "self_confidence", "title_ar": "الثقة بالنفس", "title_en": "Self-confidence", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "collaboration_teamwork", "title_ar": "التعاون والقدرة على العمل الجماعي", "title_en": "Collaboration and teamwork", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "respect_dialogue", "title_ar": "احترامه للآخرين وأسلوبه في الحوار", "title_en": "Respect for others and style of dialogue", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "ability_to_express", "title_ar": "قدرته على التعبير عن نفسه بوضوح", "title_en": "Ability to express himself clearly", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "responsiveness_guidance", "title_ar": "مرونته واستجابته للتوجيهات", "title_en": "Flexibility and responsiveness to guidance", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "general_behavior", "title_ar": "سلوكه العام - هدوءه أو اندفاعه", "title_en": "General behavior", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True},
            {"key": "hobbies_interests", "title_ar": "وجود هوايات أو اهتمامات خاصة", "title_en": "Hobbies or interests", "weight": 1, "scale_min": 1, "scale_max": 5, "required": True}
        ]
        
        c.execute("INSERT INTO interview_templates (name, program_type, criteria_json, created_by) VALUES (%s, %s, %s, %s)", 
                  ("البرنامج الرئاسي لتأهيل الشباب (15 معيار)", "PLP", json.dumps(plp_criteria, ensure_ascii=False), 1))
        c.execute("INSERT INTO interview_templates (name, program_type, criteria_json, created_by) VALUES (%s, %s, %s, %s)", 
                  ("برنامج النشء (10 معايير)", "Youth", json.dumps(youth_criteria, ensure_ascii=False), 1))

    db.commit()
    print("Migration v6 (Interview Features) complete.")
    db.close()

if __name__ == "__main__":
    migrate()
