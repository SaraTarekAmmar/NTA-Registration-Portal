import mysql.connector
import json
import os
from dotenv import load_dotenv

# Load environment variables from admin/backend/.env (project root is one level above deploy/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)  # one level up from deploy/
env_path = os.path.join(project_root, 'admin', 'backend', '.env')
load_dotenv(env_path)

def seed_data():
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'nta_portal'),
            port=int(os.getenv('DB_PORT', 3306))
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            fake_data_dir = os.path.join(project_root, 'user', 'database', 'fake_data')
            
            # Get list of all json files in fake_data_dir
            files = [f for f in os.listdir(fake_data_dir) if f.endswith('.json')]
            files.sort()

            print(f"Found {len(files)} fake data profiles. Starting injection...")

            for filename in files:
                file_path = os.path.join(fake_data_dir, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 0. Check for existing user and cleanup
                user_data = data['user']
                cursor.execute("SELECT id FROM users WHERE national_id = %s OR email = %s", 
                               (user_data['national_id'], user_data['email']))
                existing_user = cursor.fetchone()
                
                if existing_user:
                    user_id = existing_user[0]
                    # Cleanup dependent tables (ON DELETE CASCADE might handle this, but being explicit is safer)
                    cursor.execute("DELETE FROM pipeline_state WHERE trainee_id = %s", (user_id,))
                    cursor.execute("DELETE FROM applications WHERE user_id = %s", (user_id,))
                    cursor.execute("DELETE FROM trainee_profiles WHERE user_id = %s", (user_id,))
                    cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))

                # Hardcoded pbkdf2-sha256 hash for "Password123"
                default_password_hash = "$pbkdf2-sha256$29000$SSlF6N1bS0npHWOsVUqJ8Q$uN9DZiiqay2D5SC.lrxavBeg..f2J2qzu/xFyrZTNCnY"
                
                # 1. Insert into users
                cursor.execute("""
                    INSERT INTO users (full_name_ar, full_name_en, email, national_id, role, dob, gender, marital_status, password_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_data['full_name_ar'], user_data['full_name_en'], user_data['email'],
                    user_data['national_id'], user_data['role'], user_data['dob'],
                    user_data['gender'], user_data['marital_status'], default_password_hash
                ))
                user_id = cursor.lastrowid

                # 2. Insert into trainee_profiles
                profile_data = data['profile']
                cursor.execute("""
                    INSERT INTO trainee_profiles (
                        user_id, phone_numbers, secondary_email, address, emergency_contacts,
                        technical_skills, soft_skills, computer_skills,
                        academic_history, professional_history, professional_summary,
                        awards_impact, community_extracurricular, registration_extra
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, json.dumps(profile_data['phone_numbers']), profile_data['secondary_email'],
                    profile_data['address'], json.dumps(profile_data['emergency_contacts']),
                    json.dumps(profile_data['technical_skills']), json.dumps(profile_data['soft_skills']),
                    json.dumps(profile_data['computer_skills']), json.dumps(profile_data['academic_history']),
                    json.dumps(profile_data['professional_history']), json.dumps(profile_data['professional_summary']),
                    json.dumps(profile_data['awards_impact']), json.dumps(profile_data['community_extracurricular']),
                    json.dumps(data.get('registration_extra', {}))
                ))

                # 3. Insert into applications
                app_data = data['application']
                cursor.execute("""
                    INSERT INTO applications (
                        user_id, course_id, status,
                        motivation_data, research_publication, references_data,
                        logistics, identity_photos, quiz_results, quiz_scores
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, app_data['course_id'], app_data['status'],
                    json.dumps(app_data['motivation_data']), json.dumps(app_data['research_publication']),
                    json.dumps(app_data['references_data']), json.dumps(app_data['logistics']),
                    json.dumps(app_data['identity_photos']), json.dumps(app_data['quiz_results']),
                    json.dumps(app_data['quiz_scores'])
                ))

                # 4. Insert into pipeline_state
                cursor.execute("""
                    INSERT INTO pipeline_state (trainee_id, current_stage_id, status)
                    VALUES (%s, %s, 'active')
                """, (user_id, data.get('stage', 1)))

                print(f" Injected: {user_data['full_name_ar']} ({filename})")

            connection.commit()
            print(f"\nSuccessfully injected {len(files)} profiles into 'nta_portal' database.")

    except mysql.connector.Error as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    seed_data()
