import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'admin', 'backend', '.env'))
from core.database import get_db_connection

db = get_db_connection()
c = db.cursor(dictionary=True)

c.execute('SELECT step_key, step_order, is_locked FROM registration_step_settings ORDER BY step_order')
rows = c.fetchall()
print(f'Steps seeded: {len(rows)}')
for r in rows:
    print(f"  {r['step_order']}. {r['step_key']} locked={r['is_locked']}")

for tbl in ['course_materials', 'course_planning', 'admission_sections', 'applicant_submissions']:
    c.execute(f'SHOW TABLES LIKE "{tbl}"')
    exists = bool(c.fetchone())
    print(f'Table {tbl}: {"OK" if exists else "MISSING"}')

db.close()
print('Done.')
