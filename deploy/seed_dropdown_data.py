import json
import os
import mysql.connector
from dotenv import load_dotenv

# Load directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(BASE_DIR, 'DropDown Data')

# Load .env from admin/backend/.env (preferred source for DB config)
ADMIN_ENV_PATH = os.path.join(BASE_DIR, 'admin', 'backend', '.env')
USER_ENV_PATH = os.path.join(BASE_DIR, 'user', 'backend', '.env')

if os.path.exists(ADMIN_ENV_PATH):
    load_dotenv(ADMIN_ENV_PATH)
elif os.path.exists(USER_ENV_PATH):
    load_dotenv(USER_ENV_PATH)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def seed_interests():
    print("[*] Seeding Interests...")
    path = os.path.join(DATA_DIR, 'Intersts.Json')
    if not os.path.exists(path):
        print(f"    [SKIP] {path} not found.")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        interests = data.get('interests', [])
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM interests_master")
    
    query = "INSERT INTO interests_master (name_en, name_ar) VALUES (%s, %s)"
    vals = [(i['name_en'], i['name_ar']) for i in interests]
    
    cursor.executemany(query, vals)
    db.commit()
    print(f"    [OK] Inserted {len(vals)} interests.")
    db.close()

def seed_languages():
    print("[*] Seeding Languages...")
    path = os.path.join(DATA_DIR, 'Languages.json')
    if not os.path.exists(path):
        print(f"    [SKIP] {path} not found.")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        languages = json.load(f)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM languages_master")
    
    query = "INSERT INTO languages_master (name_en, name_ar) VALUES (%s, %s)"
    vals = [(l['name_en'], l['name_ar']) for l in languages]
    
    cursor.executemany(query, vals)
    db.commit()
    print(f"    [OK] Inserted {len(vals)} languages.")
    db.close()

def seed_countries_and_universities():
    print("[*] Seeding Countries and Universities...")
    path = os.path.join(DATA_DIR, 'All Universities.json')
    if not os.path.exists(path):
        print(f"    [SKIP] {path} not found.")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        countries_data = json.load(f)
    
    db = get_db()
    cursor = db.cursor()
    
    # Clear existing
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DELETE FROM universities_master")
    cursor.execute("DELETE FROM countries_master")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    for country in countries_data:
        name_en = country.get('country')
        name_ar = country.get('country_ar')
        
        cursor.execute("INSERT INTO countries_master (name_en, name_ar) VALUES (%s, %s)", (name_en, name_ar))
        country_id = cursor.lastrowid
        
        universities = country.get('universities', [])
        if universities:
            u_vals = [(country_id, u.get('name'), u.get('name_ar')) for u in universities]
            cursor.executemany("INSERT INTO universities_master (country_id, name_en, name_ar) VALUES (%s, %s, %s)", u_vals)
    
    db.commit()
    print(f"    [OK] Seeded {len(countries_data)} countries and their universities.")
    db.close()

def seed_states():
    print("[*] Seeding States (Combined Countries/States)...")
    path = os.path.join(DATA_DIR, 'combined_countries_states.json')
    if not os.path.exists(path):
        print(f"    [SKIP] {path} not found.")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        states_data = json.load(f)
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("DELETE FROM states_master")
    
    # Build country map
    cursor.execute("SELECT id, name_en FROM countries_master")
    country_map = {name: cid for cid, name in cursor.fetchall()}
    
    # Built-in Arabic mapping for Egypt Governorates
    egypt_ar_map = {
        "Cairo": "القاهرة", "Alexandria": "الإسكندرية", "Giza": "الجيزة", "Dakahlia": "الدقهلية",
        "Red Sea": "البحر الأحمر", "Beheira": "البحيرة", "Fayoum": "الفيوم", "Gharbia": "الغربية",
        "Ismailia": "الإسماعيلية", "Monufia": "المنوفية", "Minya": "المنيا", "Qalyubia": "القليوبية",
        "New Valley": "الوادي الجديد", "Sharqia": "الشرقية", "Suez": "السويس", "Aswan": "أسوان",
        "Assiut": "أسيوط", "Beni Suef": "بني سويف", "Damietta": "دمياط", "Kafr El Sheikh": "كفر الشيخ",
        "Matrouh": "مطروح", "Port Said": "بورسعيد", "Qena": "قنا", "South Sinai": "جنوب سيناء",
        "North Sinai": "شمال سيناء", "Sohag": "سوهاج", "Luxor": "الأقصر"
    }

    count = 0
    for entry in states_data:
        c_name = entry.get('name')
        c_id = country_map.get(c_name)
        
        if c_id:
            states = entry.get('states', [])
            if states:
                s_vals = []
                for s in states:
                    s_name = s.get('name')
                    s_ar = s.get('name_ar')
                    if not s_ar and c_name == "Egypt":
                        s_ar = egypt_ar_map.get(s_name)
                    s_vals.append((c_id, s_name, s_ar, s.get('code')))
                
                cursor.executemany("INSERT INTO states_master (country_id, name_en, name_ar, code) VALUES (%s, %s, %s, %s)", s_vals)
                count += len(s_vals)
            
    db.commit()
    print(f"    [OK] Seeded {count} states.")
    db.close()

def seed_skills():
    print("[*] Seeding Skills Hierarchy...")
    path = os.path.join(DATA_DIR, 'skills_data.json')
    if not os.path.exists(path):
        print(f"    [SKIP] {path} not found.")
        return
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        hierarchy = data.get('skill_hierarchy', [])
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("DELETE FROM skills_master")
    cursor.execute("DELETE FROM skill_subcategories")
    cursor.execute("DELETE FROM skill_categories")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    for cat in hierarchy:
        cursor.execute("INSERT INTO skill_categories (id, name_en, name_ar) VALUES (%s, %s, %s)", 
                       (cat.get('id'), cat.get('name_en'), cat.get('name_ar')))
        
        for sub in cat.get('subcategories', []):
            cursor.execute("INSERT INTO skill_subcategories (id, category_id, name_en, name_ar) VALUES (%s, %s, %s, %s)",
                           (sub.get('id'), cat.get('id'), sub.get('name_en'), sub.get('name_ar')))
            
            skills = sub.get('skills', [])
            if skills:
                sk_vals = [(sk.get('id'), sub.get('id'), sk.get('name_en'), sk.get('name_ar')) for sk in skills]
                cursor.executemany("INSERT INTO skills_master (id, subcategory_id, name_en, name_ar) VALUES (%s, %s, %s, %s)", sk_vals)
                
    db.commit()
    print(f"    [OK] Seeded skill hierarchy.")
    db.close()

if __name__ == "__main__":
    try:
        seed_interests()
        seed_languages()
        seed_countries_and_universities()
        seed_states()
        seed_skills()
        print("\n[SUCCESS] Dropdown data seeding completed.")
    except Exception as e:
        print(f"\n[ERROR] Seeding failed: {e}")
