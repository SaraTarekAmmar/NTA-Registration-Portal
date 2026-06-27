# -*- coding: utf-8 -*-
import sys
import os

# Ensure the backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schemas.trainee import TraineeRegistration
from pydantic import ValidationError

print("--- TESTING REMEDIATED VALIDATIONS ---")

def get_base_payload():
    return {
        "fullName": "محمد أحمد علي",
        "fullNameEn": "Mohamed Ahmed Ali",
        "dob": "1995-05-15",
        "nationalId": "29505150123456",
        "gender": "male",
        "maritalStatus": "single",
        "email": "primary@example.com",
        "secondaryEmail": "secondary@example.com",
        "phoneNumbers": ["+201012345678"],
        "emergencyName": "Jane Doe",
        "emergencyPhone": "+201012345679",
        "currentAddress": "123 Street",
        "permanentAddress": "123 Street",
        "countryOfStay": "Egypt",
        "governmentOrState": "Cairo",
        "city": "Cairo",
        "nationality": "Egyptian",
        "nativeLanguage": "Arabic",
        "englishProficiency": "excellent",
        "militaryStatus": "exempted",
        "monthlyAverageIncome": "5000",
        "numberOfNationalities": 1,
        "learningObjectives": "To learn and grow",
        "quizResults": {},
        "dataAccuracyTermsConfirmed": True
    }

def run_tests():
    # Test 1: Valid payload passes
    payload = get_base_payload()
    try:
        TraineeRegistration(**payload)
        print("[PASS] Test 1: Valid payload successfully passed validation.")
    except ValidationError as e:
        print("[FAIL] Test 1: Valid payload rejected. Errors:", e.errors())

    # Test 2: Gender-NID match logic
    payload = get_base_payload()
    payload["gender"] = "female" # Male nationalId (ends in odd 12th digit '5' in 29505150123456)
    try:
        TraineeRegistration(**payload)
        print("[FAIL] Test 2: Mismatched gender and National ID passed validation!")
    except ValidationError as e:
        print("[PASS] Test 2: Mismatched gender and National ID correctly rejected.")

    # Test 3: Age-maritalStatus restriction
    payload = get_base_payload()
    payload["dob"] = "2010-05-15" # Age 16 (under 18)
    payload["maritalStatus"] = "married"
    try:
        TraineeRegistration(**payload)
        print("[FAIL] Test 3: Underage married status passed validation!")
    except ValidationError as e:
        print("[PASS] Test 3: Underage married status correctly rejected.")

    # Test 4: Primary/Secondary email duplication
    payload = get_base_payload()
    payload["secondaryEmail"] = "PRIMARY@example.com"
    try:
        TraineeRegistration(**payload)
        print("[FAIL] Test 4: Duplicated primary/secondary email passed validation!")
    except ValidationError as e:
        print("[PASS] Test 4: Duplicated primary/secondary email correctly rejected.")

if __name__ == "__main__":
    run_tests()
    print("--- TESTING FINISHED ---")
