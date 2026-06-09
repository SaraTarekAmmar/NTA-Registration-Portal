import json
from core.database import get_db_connection

def check_results():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT COUNT(*) as total FROM cv_matching_results")
        print(f"Total entries in cv_matching_results: {cursor.fetchone()['total']}")
        
        cursor.execute("SELECT national_id, course_id, match_score, CHAR_LENGTH(evidence) as flen, analysis_json FROM cv_matching_results ORDER BY id DESC LIMIT 10")
        results = cursor.fetchall()
        
        print("\nLatest 10 results:")
        print("-" * 50)
        for r in results:
            nid = r['national_id']
            score = r['match_score']
            flen = r['flen']
            has_json = "YES" if r['analysis_json'] else "NO"
            print(f"Trainee NID: {nid} | Course: {r['course_id']} | Score: {score} | Feedback Len: {flen} | JSON: {has_json}")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_results()
