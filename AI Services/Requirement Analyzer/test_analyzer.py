import os
import json
from analyzer import RequirementAnalyzer

def run_test():
    print("=== NTA AI Requirement Analyzer Test ===")
    
    # Configuration
    trainee_id = 65
    course_id = 10
    
    analyzer = RequirementAnalyzer()
    
    print(f"Target: Trainee {trainee_id}, Course {course_id}")
    print("Running multi-step analysis (this may take a minute)...")
    
    result = analyzer.analyze_trainee(trainee_id, course_id)
    
    if result.get("success"):
        print("\n[SUCCESS] AI Analysis completed successfully!")
        print("-" * 40)
        print("RADAR CHART DATA:")
        print(json.dumps(result["radar_chart"], indent=2, ensure_ascii=False))
        print("-" * 40)
        print("AI SUMMARY (Arabic):")
        print(result["summary"])
        print("-" * 40)
    else:
        print(f"\n[FAILED] Error: {result.get('error')}")
        print("-" * 40)
        print(f"DEBUG - Raw AI Output: {result.get('raw')}")
        print("-" * 40)

if __name__ == "__main__":
    run_test()
