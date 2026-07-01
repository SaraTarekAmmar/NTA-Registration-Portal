import sys
from pathlib import Path
from core.database import get_db_connection
from core.logger_util import log_activity

# Integration with the new AI Hub
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(ROOT / "AI Services" / "Requirement Analyzer"))

try:
    from analyzer import RequirementAnalyzer
except ImportError:
    RequirementAnalyzer = None

def trigger_cv_match(trainee_id: int, course_id: int):
    """
    Triggers the AI Requirement Analysis for a specific trainee and course.
    """
    if not RequirementAnalyzer:
        print("Error: RequirementAnalyzer module not found in AI Services Hub")
        return False

    try:
        print(f"Triggering Enhanced AI Analysis for Trainee {trainee_id} on Course {course_id}...")
        analyzer = RequirementAnalyzer()
        result = analyzer.analyze_trainee(trainee_id, course_id)
        
        if result.get("success"):
            print(f"Analysis Complete: {result.get('radar_chart', {}).get('overall_match_percentage', 0)}%")
            return True
        else:
            print(f"Analysis Failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"Error triggering AI analysis: {e}")
        return False
