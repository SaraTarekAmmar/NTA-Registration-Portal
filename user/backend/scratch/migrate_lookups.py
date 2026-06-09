import json
import os
import mysql.connector
import sys
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "nta_portal")
}

# Paths to the JSON files (relative to the workspace root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Scratch is inside user/backend/scratch -> go up 4 levels to reach workspace root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MINISTRIES_JSON_PATH = os.path.join(BASE_DIR, "ministries_lookup_updated.json")
EGYPT_JSON_PATH = os.path.join(BASE_DIR, "Egypt V2.json")
UK_JSON_PATH = os.path.join(BASE_DIR, "United Kingdom V2.json")

def load_robust_json(filepath):
    """Loads a JSON file robustly, even if it contains concatenated lists/objects."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        pos = 0
        combined = []
        while pos < len(content):
            # Skip whitespace
            while pos < len(content) and content[pos].isspace():
                pos += 1
            if pos >= len(content):
                break
            try:
                obj, next_pos = decoder.raw_decode(content, pos)
                if isinstance(obj, list):
                    combined.extend(obj)
                else:
                    combined.append(obj)
                pos = next_pos
            except Exception as e:
                print(f"[ERROR] raw_decode failed at position {pos}: {e}")
                # Fallback: attempt a quick string replace for concatenated arrays
                # e.g., "]\n[" -> ","
                cleaned = content.replace("]\n[", ",").replace("]\r\n[", ",")
                return json.loads(cleaned)
        return combined

def run_migration():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    try:
        print("[*] Starting Lookup Data Migration...")
        print(f"[*] Workspace Root: {BASE_DIR}")
        
        # 1. Create New Tables if they don't exist
        print("[*] Creating Tables...")
        
        # ministry_authorities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `ministry_authorities` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `ministry_id` INT NOT NULL,
                `name` VARCHAR(255) NOT NULL,
                FOREIGN KEY (`ministry_id`) REFERENCES `ministries_master` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # university_colleges
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `university_colleges` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `university_id` INT NOT NULL,
                `name_en` VARCHAR(255) NOT NULL,
                `name_ar` VARCHAR(255) DEFAULT NULL,
                FOREIGN KEY (`university_id`) REFERENCES `universities_master` (`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
        
        # 2. Ingest Ministries and Authorities
        if os.path.exists(MINISTRIES_JSON_PATH):
            print(f"[*] Processing Ministries from {MINISTRIES_JSON_PATH}...")
            ministries_data = load_robust_json(MINISTRIES_JSON_PATH)
                
            # Clear existing ministry authorities and ministries
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("DELETE FROM ministry_authorities")
            cursor.execute("DELETE FROM ministries_master")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            ministry_count = 0
            authority_count = 0
            
            for m in ministries_data:
                name_en = m.get('name_en')
                name_ar = m.get('name_ar')
                authorities = m.get('authorities', [])
                
                cursor.execute(
                    "INSERT INTO ministries_master (name_en, name_ar) VALUES (%s, %s)",
                    (name_en, name_ar)
                )
                ministry_id = cursor.lastrowid
                ministry_count += 1
                
                if authorities:
                    auth_vals = [(ministry_id, auth) for auth in authorities]
                    cursor.executemany(
                        "INSERT INTO ministry_authorities (ministry_id, name) VALUES (%s, %s)",
                        auth_vals
                    )
                    authority_count += len(authorities)
                    
            print(f"    [OK] Ingested {ministry_count} ministries and {authority_count} authorities.")
        else:
            print(f"    [WARNING] Ministries file not found at {MINISTRIES_JSON_PATH}")

        # 3. Get Country IDs for Egypt and United Kingdom
        cursor.execute("SELECT id, name_en FROM countries_master WHERE name_en IN ('Egypt', 'United Kingdom')")
        country_map = {row['name_en']: row['id'] for row in cursor.fetchall()}
        
        egypt_id = country_map.get('Egypt')
        uk_id = country_map.get('United Kingdom')
        
        if not egypt_id or not uk_id:
            raise Exception("Egypt or United Kingdom not found in countries_master table.")
            
        print(f"[*] Country IDs found - Egypt: {egypt_id}, United Kingdom: {uk_id}")
        
        # Clear existing universities and colleges for Egypt and UK
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute(
            "DELETE FROM universities_master WHERE country_id IN (%s, %s)",
            (egypt_id, uk_id)
        )
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 4. Ingest Egypt Universities and Colleges
        if os.path.exists(EGYPT_JSON_PATH):
            print(f"[*] Processing Egypt Universities from {EGYPT_JSON_PATH}...")
            egypt_data = load_robust_json(EGYPT_JSON_PATH)
                
            egy_univ_count = 0
            egy_coll_count = 0
            
            for u in egypt_data:
                name_en = u.get('name')
                name_ar = u.get('name_ar')
                colleges = u.get('colleges', [])
                
                cursor.execute(
                    "INSERT INTO universities_master (country_id, name_en, name_ar) VALUES (%s, %s, %s)",
                    (egypt_id, name_en, name_ar)
                )
                univ_id = cursor.lastrowid
                egy_univ_count += 1
                
                if colleges:
                    coll_vals = []
                    for coll in colleges:
                        if isinstance(coll, dict):
                            coll_vals.append((univ_id, coll.get('name_en'), coll.get('name_ar')))
                        else:
                            coll_vals.append((univ_id, coll, None))
                    cursor.executemany(
                        "INSERT INTO university_colleges (university_id, name_en, name_ar) VALUES (%s, %s, %s)",
                        coll_vals
                    )
                    egy_coll_count += len(coll_vals)
                    
            print(f"    [OK] Ingested {egy_univ_count} Egypt universities and {egy_coll_count} colleges.")
        else:
            print(f"    [WARNING] Egypt V2 file not found at {EGYPT_JSON_PATH}")
            
        # 5. Ingest UK Universities and Colleges
        if os.path.exists(UK_JSON_PATH):
            print(f"[*] Processing United Kingdom Universities from {UK_JSON_PATH}...")
            uk_data = load_robust_json(UK_JSON_PATH)
                
            uk_univ_count = 0
            uk_coll_count = 0
            
            for u in uk_data:
                name_en = u.get('name')
                name_ar = u.get('name_ar')
                colleges = u.get('colleges', [])
                
                cursor.execute(
                    "INSERT INTO universities_master (country_id, name_en, name_ar) VALUES (%s, %s, %s)",
                    (uk_id, name_en, name_ar)
                )
                univ_id = cursor.lastrowid
                uk_univ_count += 1
                
                if colleges:
                    coll_vals = []
                    for coll in colleges:
                        if isinstance(coll, dict):
                            coll_vals.append((univ_id, coll.get('name_en'), coll.get('name_ar')))
                        else:
                            coll_vals.append((univ_id, coll, None))
                    cursor.executemany(
                        "INSERT INTO university_colleges (university_id, name_en, name_ar) VALUES (%s, %s, %s)",
                        coll_vals
                    )
                    uk_coll_count += len(coll_vals)
                    
            print(f"    [OK] Ingested {uk_univ_count} UK universities and {uk_coll_count} colleges.")
        else:
            print(f"    [WARNING] UK V2 file not found at {UK_JSON_PATH}")

        conn.commit()
        print("\n[SUCCESS] Migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
