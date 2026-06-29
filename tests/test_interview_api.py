import mysql.connector
import requests
import json

COORDINATOR_BASE = "http://localhost:8005"
ADMISSION_BASE = "http://localhost:7776"
ADMIN_BASE = "http://localhost:8002"

def get_db():
    return mysql.connector.connect(
        host="localhost", user="root", password="sara@16112000", database="nta_portal"
    )

def test_e2e_interview_flow():
    print("\n--- Starting E2E Interview Flow Integration Test ---")
    
    # 1. Login as Coordinator
    print("\n[Step 1] Logging in as Coordinator...")
    login_resp = requests.post(f"{COORDINATOR_BASE}/api/coordinator/auth/login", json={
        "email": "coordinator@nta.edu.eg",
        "nationalId": "29304041234567",
        "password": "NTA@Coord2026"
    })
    assert login_resp.status_code == 200, f"Coordinator login failed: {login_resp.text}"
    coord_token = login_resp.json()["access_token"]
    coord_headers = {"Authorization": f"Bearer {coord_token}", "Content-Type": "application/json"}
    print("Coordinator logged in successfully.")

    # 2. Get list of committee members
    print("\n[Step 2] Fetching committee members...")
    members_resp = requests.get(f"{COORDINATOR_BASE}/api/coordinator/interviews/committee-members", headers=coord_headers)
    assert members_resp.status_code == 200, f"Fetch committee members failed: {members_resp.text}"
    members = members_resp.json()
    print(f"Found {len(members)} committee members.")
    member1_id = None
    for m in members:
        if m["email"] == "member1@nta.edu.eg":
            member1_id = m["id"]
            break
    assert member1_id is not None, "member1@nta.edu.eg not found in committee members list"
    print(f"Member 1 ID: {member1_id}")

    # 3. Get queue, find a trainee in Stage 5 or 6
    print("\n[Step 3] Fetching interview queue as coordinator...")
    queue_resp = requests.get(f"{COORDINATOR_BASE}/api/coordinator/interviews/queue", headers=coord_headers)
    assert queue_resp.status_code == 200, f"Fetch queue failed: {queue_resp.text}"
    queue = queue_resp.json()
    print(f"Queue length: {len(queue)}")
    
    trainee = None
    for item in queue:
        if item["stage_id"] in (5, 6):
            trainee = item
            break
    
    if not trainee:
        print("No trainee in Stage 5 or 6. Forcing a trainee to Stage 5 for test purposes...")
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE role = 'trainee' LIMIT 1")
        test_user = cursor.fetchone()
        assert test_user is not None, "No trainee exists in users table to perform the test."
        trainee_id = test_user["id"]
        
        # Insert/Update pipeline state to stage 5
        cursor.execute("""
            INSERT INTO pipeline_state (trainee_id, current_stage_id, status)
            VALUES (%s, 5, 'active')
            ON DUPLICATE KEY UPDATE current_stage_id = 5, status = 'active'
        """, (trainee_id,))
        
        # Ensure they have an active application
        cursor.execute("""
            SELECT id FROM courses LIMIT 1
        """)
        c_row = cursor.fetchone()
        c_id = c_row["id"] if c_row else 1
        
        cursor.execute("""
            INSERT INTO applications (user_id, course_id, status, applied_at)
            VALUES (%s, %s, 'approved', NOW())
        """, (trainee_id, c_id))
        db.commit()
        cursor.close()
        db.close()
        
        # Refetch queue
        queue_resp = requests.get(f"{COORDINATOR_BASE}/api/coordinator/interviews/queue", headers=coord_headers)
        queue = queue_resp.json()
        for item in queue:
            if item["id"] == trainee_id:
                trainee = item
                break
                
    assert trainee is not None, "Failed to get/setup a trainee in Stage 5 or 6"
    print(f"Selected Trainee for test: ID={trainee['id']}, Stage={trainee['stage_id']}")

    # 4. Clean up any existing assignments for this trainee/stage
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM interview_assignments WHERE trainee_id = %s AND stage_id = %s", (trainee["id"], trainee["stage_id"]))
    cursor.execute("DELETE FROM admission_interview_scores WHERE trainee_id = %s AND stage_id = %s", (trainee["id"], trainee["stage_id"]))
    db.commit()
    cursor.close()
    db.close()

    # 5. Try submitting review before assignment (Should fail for committee member, pass for admin/coordinator)
    # Let's login as Committee Member on Admission Center
    print("\n[Step 5] Logging in as Committee Member to Admission Center...")
    login_member_resp = requests.post(f"{ADMISSION_BASE}/api/auth/login", json={
        "email": "member1@nta.edu.eg",
        "nationalId": "29402021234567",
        "password": "NTA@Member2026",
        "role": "admission_manager" # request payload matches login request model
    })
    assert login_member_resp.status_code == 200, f"Member login failed: {login_member_resp.text}"
    member_token = login_member_resp.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}", "Content-Type": "application/json"}
    
    # Try submitting review - should get 403 Forbidden because of missing assignment
    print("Submitting stage review as member1 WITHOUT assignment (should fail with 403)...")
    review_payload = {
        "trainee_id": trainee["id"],
        "stage_id": trainee["stage_id"],
        "reviewer_id": member1_id,
        "reviewer_name": "عضو اللجنة الأول",
        "attachment_path": "",
        "result": "Active",
        "notes": "Excellent candidate",
        "details": {
            "comm_skills": "4",
            "confidence": "5",
            "appearance": "4"
        }
    }
    review_resp = requests.post(f"{ADMISSION_BASE}/api/admission/stage-review", json=review_payload, headers=member_headers)
    assert review_resp.status_code == 403, f"Expected 403, got {review_resp.status_code}: {review_resp.text}"
    print("Success: Submission blocked correctly with 403.")

    # 6. Assign trainee to member1
    print("\n[Step 6] Assigning trainee to Member 1...")
    assign_resp = requests.post(f"{COORDINATOR_BASE}/api/coordinator/interviews/assign", json={
        "trainee_id": trainee["id"],
        "stage_id": trainee["stage_id"],
        "reviewer_id": member1_id,
        "course_id": trainee.get("course_id")
    }, headers=coord_headers)
    assert assign_resp.status_code == 200, f"Assignment failed: {assign_resp.text}"
    print("Trainee successfully assigned to Member 1.")

    # 7. Check queue as committee member
    print("\n[Step 7] Fetching queue as Committee Member...")
    member_queue_resp = requests.get(f"{COORDINATOR_BASE}/api/coordinator/interviews/queue", headers={
        "Authorization": f"Bearer {member_token}", "Content-Type": "application/json"
    })
    assert member_queue_resp.status_code == 200, f"Fetch queue as member failed: {member_queue_resp.text}"
    member_queue = member_queue_resp.json()
    print(f"Committee member sees {len(member_queue)} assigned candidates.")
    # Verify that the trainee we assigned is visible
    has_trainee = any(item["id"] == trainee["id"] for item in member_queue)
    assert has_trainee, "Assigned trainee is not visible to the committee member"
    print("Assigned trainee verified in committee member's queue.")

    # 8. Submit stage review (should succeed)
    print("\n[Step 8] Submitting stage review as Committee Member...")
    review_resp = requests.post(f"{ADMISSION_BASE}/api/admission/stage-review", json=review_payload, headers=member_headers)
    assert review_resp.status_code == 200, f"Submission failed: {review_resp.text}"
    print("Review submitted successfully.")

    # 9. Verify scores in the database
    print("\n[Step 9] Verifying scores in database...")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admission_interview_scores WHERE trainee_id = %s AND stage_id = %s AND reviewer_id = %s", (trainee["id"], trainee["stage_id"], member1_id))
    score_row = cursor.fetchone()
    assert score_row is not None, "No score row found in database!"
    
    print(f"Calculated Score in DB: {score_row['total_score']} / {score_row['total_max']}")
    assert score_row["total_score"] == 13, f"Expected total score 13, got {score_row['total_score']}"
    assert score_row["total_max"] == 15, f"Expected total max 15, got {score_row['total_max']}"
    
    # Check that assignment is completed
    cursor.execute("SELECT status FROM interview_assignments WHERE trainee_id = %s AND stage_id = %s AND reviewer_id = %s", (trainee["id"], trainee["stage_id"], member1_id))
    assign_row = cursor.fetchone()
    assert assign_row is not None
    assert assign_row["status"] == "completed", f"Assignment status should be 'completed', got {assign_row['status']}"
    print("Assignment status updated to 'completed' successfully.")
    
    cursor.close()
    db.close()

    print("\n--- E2E Interview Flow Integration Test Passed Successfully! ---")

if __name__ == "__main__":
    test_e2e_interview_flow()
