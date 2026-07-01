from core.database import get_db_connection

steps = [
    (1, "names", "Personal Information"),
    (2, "demographics", "Personal Information"),
    (3, "socio_economic", "Personal Information"),
    (4, "location_contact", "Contact Details"),
    (5, "digital_comm", "Contact Details"),
    (6, "identity_docs", "Identity & Military"),
    (7, "nationalities", "Identity & Military"),
    (8, "military", "Identity & Military"),
    (9, "emergency", "Emergency Contacts"),
    (10, "main_education", "Educational Background"),
    (11, "postgraduate", "Educational Background"),
    (12, "standardized_tests", "Educational Background"),
    (13, "employment_core", "Employment History"),
    (14, "role_scale", "Employment History"),
    (15, "leadership_scale", "Employment History"),
    (16, "languages", "Skills & Languages"),
    (17, "skills_matrix", "Skills & Languages"),
    (18, "interests", "Skills & Languages"),
    (19, "social_hub", "Activities & Social"),
    (20, "prizes_awards", "Activities & Social"),
    (21, "conferences", "Activities & Social"),
    (22, "extracurriculars", "Activities & Social"),
    (23, "voluntary_work", "Activities & Social"),
    (24, "political_work", "Activities & Social"),
    (25, "political_candidacy", "Activities & Social"),
    (26, "creative_assets", "Activities & Social"),
    (27, "core_motivation", "Motivation & Goals"),
    (28, "funding_scholarship", "Motivation & Goals"),
    (29, "legal_status", "Legal & References"),
    (30, "references", "Legal & References"),
    (31, "career_docs", "Legal & References"),
    (32, "accommodation", "Logistics & Needs"),
    (33, "agreements", "Logistics & Needs"),
    (34, "psychometric_a", "Cognitive Assessment"),
    (35, "psychometric_b", "Cognitive Assessment"),
    (36, "psychometric_c", "Cognitive Assessment"),
    (37, "psychometric_d", "Cognitive Assessment"),
    (38, "psychometric_e", "Cognitive Assessment"),
    (39, "visual_id", "Final Verification"),
    (40, "social_urls", "Final Verification"),
]

import os
os.environ['DB_USER'] = 'root'
os.environ['DB_PASSWORD'] = 'OmarNour@Work161996'
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_NAME'] = 'nta_portal'
conn = get_db_connection()
cur = conn.cursor()

try:
    # First, let's clear existing non-admission steps or maybe just insert them with logic
    cur.execute("DELETE FROM steps_pool WHERE type = 'registration'")
    
    for step_num, file_suffix, phase_name in steps:
        name = file_suffix
        route = f"components/step_{step_num}_{file_suffix}.html"
        
        cur.execute("""
            INSERT INTO steps_pool (id, name, type, frontend_component_route, validation_rule_schema)
            VALUES (%s, %s, 'registration', %s, '{}')
            ON DUPLICATE KEY UPDATE name=VALUES(name), frontend_component_route=VALUES(frontend_component_route)
        """, (step_num, name, route))
        
    conn.commit()
    print("Successfully seeded 40 registration steps into steps_pool table.")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    cur.close()
    conn.close()
