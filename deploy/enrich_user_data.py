import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "user" / "backend"))

from core.database import get_db_connection

def enrich_trainee():
    email = "trainee@example.com"
    db = get_db_connection()
    try:
        # Create a dictionary cursor
        cursor = db.cursor(dictionary=True)
        # Find user
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        # VERY IMPORTANT: Consume all results if any, then close cursor to avoid "Unread result found"
        while cursor.nextset():
            pass
        cursor.close()

        if not user:
            print("User not found! Inserting default trainee user...")
            cursor.execute("""
                INSERT INTO users (full_name_ar, full_name_en, email, national_id, role, dob, gender, marital_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, ('أحمد محمد علي', 'Ahmed Mohamed Ali', email, '29808081234567', 'trainee', '1998-08-08', 'male', 'single'))
            user_id = cursor.lastrowid
        else:
            user_id = user['id']
        print(f"Enriching user ID: {user_id}")

        # Start a new cursor for updates
        cursor = db.cursor()
        
        # 1. Update Users Table
        cursor.execute("""
            UPDATE users SET full_name_ar = 'محمد أحمد علي', full_name_en = 'Mohamed Ahmed Ali'
            WHERE id = %s
        """, (user_id,))

        # 2. Data for Trainee Profiles
        phone_numbers = ["+201012345678", "+201287654321"]
        em_contacts = {"name": "أحمد منصور", "phone": "+201112223334"}
        
        academic = [
            {
                "institution": "Cairo University",
                "major": "Computer Science",
                "degree": "Bachelor",
                "gpa": "3.8/4.0",
                "gradYear": "2018",
                "ranking": "Top 5%"
            },
            {
                "institution": "AUC",
                "major": "Data Science",
                "degree": "Master",
                "gpa": "A",
                "gradYear": "2021",
                "ranking": "Excellent"
            }
        ]
        
        professional = [
            {
                "organization": "NTA Solutions",
                "startDate": "2021-06-01",
                "endDate": "2024-01-01",
                "responsibilities": "Leading the backend development team, architecting microservices.",
                "reasonForLeaving": "Career growth"
            },
            {
                "organization": "Global Tech",
                "startDate": "2018-07-01",
                "endDate": "2021-05-30",
                "responsibilities": "Developing front-end interfaces and maintaining legacy code.",
                "reasonForLeaving": "Found better opportunity"
            }
        ]
        
        # Skills (IDs from skills_master)
        tech_skills = [{"category": 1, "name": 1}, {"category": 1, "name": 2}]
        soft_skills = [{"category": 3, "name": 10}]
        comp_skills = [{"category": 2, "name": 5}]
        
        extra = {
            "permanentAddress": "123 Nile St, Zamalek, Cairo",
            "portfolioUrl": "https://portfolio.me/trainee",
            "learningObjectives": "Mastering advanced AI algorithms and leadership skills.",
            "dietaryRestrictions": "None",
            "accessibilityRequirements": "None",
            "references": [
                {"name": "Dr. Ahmed Mansour", "relationship": "Professor", "contact": "ahmed@edu.eg"},
                {"name": "Eng. Sara Ali", "relationship": "Manager", "contact": "+20123456789"}
            ]
        }
        
        docs = {
            "cvResume": "uploads/cvs/test_cv.pdf",
            "idScan": "uploads/ids/test_id.pdf"
        }
        
        # Check if profile exists
        cursor.execute("SELECT id FROM trainee_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        # Consume any unread results from this check
        while cursor.nextset():
            pass

        if profile:
            print("Updating existing profile...")
            query = """
                UPDATE trainee_profiles 
                SET phone_numbers = %s,
                    secondary_email = 'mohamed.ali@example.com',
                    address = '6th of October City, Giza',
                    emergency_contacts = %s,
                    technical_skills = %s,
                    soft_skills = %s,
                    computer_skills = %s,
                    academic_history = %s,
                    professional_history = %s,
                    registration_extra = %s,
                    documents = %s
                WHERE user_id = %s
            """
            cursor.execute(query, (
                json.dumps(phone_numbers),
                json.dumps(em_contacts),
                json.dumps(tech_skills),
                json.dumps(soft_skills),
                json.dumps(comp_skills),
                json.dumps(academic),
                json.dumps(professional),
                json.dumps(extra),
                json.dumps(docs),
                user_id
            ))
        else:
            print("Creating new profile...")
            query = """
                INSERT INTO trainee_profiles 
                (user_id, phone_numbers, secondary_email, address, emergency_contacts, 
                 technical_skills, soft_skills, computer_skills, academic_history, 
                 professional_history, registration_extra, documents)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                user_id,
                json.dumps(phone_numbers),
                'mohamed.ali@example.com',
                '6th of October City, Giza',
                json.dumps(em_contacts),
                json.dumps(tech_skills),
                json.dumps(soft_skills),
                json.dumps(comp_skills),
                json.dumps(academic),
                json.dumps(professional),
                json.dumps(extra),
                json.dumps(docs)
            ))
            
        db.commit()
        print(f"Successfully enriched profile for {email}!")
        cursor.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    enrich_trainee()
