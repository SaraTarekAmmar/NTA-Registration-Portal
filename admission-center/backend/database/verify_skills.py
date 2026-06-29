import mysql.connector
import os
from dotenv import load_dotenv

# Robust path handling
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

# Try project root .env locations
env_path = os.path.join(PROJECT_ROOT, 'admin', 'backend', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(PROJECT_ROOT, 'user', 'backend', '.env')

load_dotenv(env_path)

def verify():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'OmarNour@Work161996'),
        database=os.getenv('DB_NAME', 'nta_portal')
    )
    cursor = conn.cursor()

    print("Verifying Skill Data...")

    queries = {
        "Categories Count": "SELECT COUNT(*) FROM skill_categories",
        "Subcategories Count": "SELECT COUNT(*) FROM skill_subcategories",
        "Skills Count": "SELECT COUNT(*) FROM skills_master",
        "Sample Linked Record": """
            SELECT c.name_ar, s.name_ar, sm.name_ar 
            FROM skills_master sm
            JOIN skill_subcategories s ON sm.subcategory_id = s.id
            JOIN skill_categories c ON s.category_id = c.id
            LIMIT 5
        """
    }

    for name, query in queries.items():
        cursor.execute(query)
        res = cursor.fetchall()
        print(f"{name}: {res}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify()
