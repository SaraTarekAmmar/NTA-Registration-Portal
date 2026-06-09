import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path("d:/Work/NTA/NTA-Regestration-Portal - Final/admin/backend")))

from core.database import get_db_connection

def main():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT match_score, evidence, analysis_json FROM cv_matching_results WHERE course_id=10 LIMIT 1')
    res = cursor.fetchone()
    if res:
        res['analysis_json'] = json.loads(res['analysis_json'])
        output_path = Path("d:/Work/NTA/NTA-Regestration-Portal - Final/AI Services/Requirement Analyzer/actual_test_output.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {output_path}")
    else:
        print("No results found in DB.")

if __name__ == "__main__":
    main()
