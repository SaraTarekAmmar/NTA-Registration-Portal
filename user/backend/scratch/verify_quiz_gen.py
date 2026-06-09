import os
import sys
from pathlib import Path

# Add project roots to sys.path
ROOT = Path("d:/Work/NTA/NTA-Regestration-Portal - Final")
sys.path.insert(0, str(ROOT / "superadmin" / "backend"))
sys.path.insert(0, str(ROOT / "user" / "backend"))

def test_mock_generation():
    print("[*] Testing generate_mock_questions function from superadmin ai_proxy...")
    try:
        from routers.ai_proxy import generate_mock_questions
        res = generate_mock_questions(
            topic="التنمية البشرية وتطوير الذات",
            q_type="mixed",
            count=5,
            difficulty="medium"
        )
        print("  [+] Mock Questions Generated Successfully!")
        print(f"  [+] Output keys: {list(res.keys())}")
        print(f"  [+] Number of questions: {len(res['questions'])}")
        for idx, q in enumerate(res['questions']):
            print(f"    {idx+1}. [{q['type']}] {q['question'].encode('utf-8')}")
    except Exception as e:
        print(f"  [-] Failed mock generation test: {e}")
        import traceback
        traceback.print_exc()

def test_path_resolution():
    print("\n[*] Testing file resolution logic...")
    filename = "DUMMY_COURSE_GUIDE_V2.pdf"
    
    # Simulate the resolution paths logic from the router
    possible_paths = [
        ROOT / filename.lstrip('/'),
        ROOT / "uploads" / filename.lstrip('/'),
        ROOT / "data" / "uploads" / filename.lstrip('/'),
        ROOT / "user" / "uploads" / "files" / filename.lstrip('/')
    ]
    
    found_path = None
    for p in possible_paths:
        if p.exists() and p.is_file():
            found_path = p
            break
            
    if not found_path:
        courses_dir = ROOT / "data" / "courses"
        if courses_dir.exists():
            for r, d, files in os.walk(courses_dir):
                if filename in files:
                    found_path = Path(r) / filename
                    break
                    
    if found_path:
        print(f"  [+] Successfully resolved '{filename}' to: {found_path}")
    else:
        print(f"  [-] Failed to resolve '{filename}' using backend logic.")

if __name__ == "__main__":
    test_mock_generation()
    test_path_resolution()
