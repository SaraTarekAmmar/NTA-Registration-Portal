import json
import random
from core.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor(dictionary=True)

cursor.execute('SELECT id, analysis_json FROM cv_matching_results WHERE course_id = 10')
rows = cursor.fetchall()

base_texts = [
    "أظهر المتدرب كفاءة ممتازة وفهم عميق للتقنيات الأساسية مع إمكانيات واعدة للتطور.",
    "مستوى المتدرب متوسط ويحتاج إلى التركيز أكثر على المهارات التحليلية والرياضية.",
    "أداء استثنائي وتطابق عالي جداً مع متطلبات الدورة، مع توصية بمهام متقدمة.",
    "المتدرب يمتلك الأساسيات ولكنه يحتاج للمزيد من التطبيق العملي لتجاوز مرحلة المبتدئ."
]

for idx, r in enumerate(rows):
    score = random.randint(55, 95)
    text = random.choice(base_texts)
    
    # Parse existing JSON and modify scores slightly
    try:
        data = json.loads(r['analysis_json'])
        for m in data.get('requirement_matches', []):
            m['score'] = random.randint(40, 100)
        data['overall_match_percentage'] = score
        new_json = json.dumps(data, ensure_ascii=False)
    except:
        new_json = r['analysis_json']
        
    cursor.execute('''
        UPDATE cv_matching_results 
        SET match_score = %s, evidence = %s, analysis_json = %s
        WHERE id = %s
    ''', (score, text, new_json, r['id']))

conn.commit()
conn.close()
print("Randomized data for course 10 to demonstrate dynamic UI.")
