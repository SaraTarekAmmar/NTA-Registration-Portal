import sys
import os

# Ensure the backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas.trainee import TraineeRegistration
from pydantic import ValidationError

print("--- TESTING SECURITY VALIDATION ---\n")

def test_pydantic():
    print("1. Testing Bad Name Payload (Numbers in name)")
    bad_payload = {
        "fullName": "John Doe 123",
        "fullNameEn": "John Doe",
        "dob": "1995-05-15",
        "nationalId": "29505150123456",
        "gender": "male",
        "maritalStatus": "single",
        "email": "test@test.com",
        "phoneNumbers": ["+201012345678"],
        "emergencyName": "Jane Doe",
        "emergencyPhone": "+201012345679",
        "currentAddress": "123 Street",
        "permanentAddress": "123 Street",
        "technicalSkills": [],
        "soft_skills": [],
        "computer_skills": [],
        "academicHistory": [],
        "professional_history": [],
        "portfolioUrl": "",
        "learningObjectives": "",
        "references": [],
        "dietaryRestrictions": "",
        "accessibilityRequirements": "",
        "photoFront": "",
        "quizResults": {}
    }
    
    try:
        TraineeRegistration(**bad_payload)
        print("FAIL: Bad Name Payload passed validation!")
    except ValidationError as e:
        print("PASS: Bad Name Payload rejected.")
        print("Error details:", e.errors()[0]['msg'])

    print("\n2. Testing Bad Age Payload (Age 10)")
    bad_payload["fullName"] = "John Doe"
    bad_payload["dob"] = "2015-05-15"
    try:
        TraineeRegistration(**bad_payload)
        print("FAIL: Bad Age Payload passed validation!")
    except ValidationError as e:
        print("PASS: Bad Age Payload rejected.")
        print("Error details:", e.errors()[0]['msg'])
        
    print("\n3. Testing Bad Phone Payload (No country code)")
    bad_payload["dob"] = "1995-05-15"
    bad_payload["phoneNumbers"] = ["01012345678"]
    try:
        TraineeRegistration(**bad_payload)
        print("FAIL: Bad Phone Payload passed validation!")
    except ValidationError as e:
        print("PASS: Bad Phone Payload rejected.")
        print("Error details:", e.errors()[0]['msg'])

if __name__ == "__main__":
    test_pydantic()
    print("\n--- TESTS FINISHED ---")
