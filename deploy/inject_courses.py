import mysql.connector
import os
import json
import re
from dotenv import load_dotenv

# Setup Environment and Database Connection
def get_db_connection():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Try to find .env in common locations
    env_paths = [
        os.path.join(project_root, 'admin', 'backend', '.env'),
        os.path.join(project_root, 'user', 'backend', '.env'),
        os.path.join(script_dir, '.env')
    ]
    
    loaded = False
    for path in env_paths:
        if os.path.exists(path):
            load_dotenv(path)
            loaded = True
            break
    
    if not loaded:
        print("[!] Warning: No .env file found. Using default environment variables.")

    try:
        # Get credentials with fallbacks
        db_host = os.getenv('DB_HOST', 'localhost')
        db_user = os.getenv('DB_USER', 'root')
        db_pass = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'nta_portal')
        db_port = int(os.getenv('DB_PORT', 3306))

        print(f"[*] Connecting to {db_name} on {db_host}...")
        connection = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_pass,
            database=db_name,
            port=db_port,
            charset='utf8mb4'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"[!] Database Connection Error: {err}")
        print("[TIP] Make sure your .env file is correct and MySQL is running.")
        return None

def inject_courses():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_courses_dir = os.path.join(project_root, 'data', 'courses')

    if not os.path.exists(data_courses_dir):
        print(f"[!] Error: {data_courses_dir} not found.")
        return

    db = get_db_connection()
    if not db:
        return
    
    cursor = db.cursor(dictionary=True, buffered=True)
    
    try:
        course_folders = [f for f in os.listdir(data_courses_dir) if os.path.isdir(os.path.join(data_courses_dir, f)) and f != 'images']
        
        print(f"[*] Found {len(course_folders)} course folders.")

        for folder in course_folders:
            folder_path = os.path.join(data_courses_dir, folder)
            print(f"\n[*] Processing folder: {folder}")

            # 1. Parse course.txt
            course_txt_path = os.path.join(folder_path, 'course.txt')
            title = folder.replace('_', ' ')
            description = ""
            if os.path.exists(course_txt_path):
                with open(course_txt_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        title_line = lines[0].strip()
                        if title_line.startswith("Course Title:"):
                            title = title_line.replace("Course Title:", "").strip()
                        else:
                            title = title_line
                        description = "".join(lines[1:]).strip()

            # 2. Extract duration from folder name (e.g., Python_for_Data_Science_10)
            duration_match = re.search(r'_(\d+)$', folder)
            duration_weeks = int(duration_match.group(1)) if duration_match else 10

            # 3. Count material files
            material_files = [f for f in os.listdir(folder_path) if f.startswith('course_material_') and f.endswith('.txt')]
            total_sessions = len(material_files) if material_files else 12 # Default

            # 4. Insert/Update Course
            cursor.execute("SELECT id FROM courses WHERE title = %s", (title,))
            existing_course = cursor.fetchone()

            if existing_course:
                course_id = existing_course['id']
                print(f" [*] Updating existing course: {title} (ID: {course_id})")
                cursor.execute("""
                    UPDATE courses 
                    SET description = %s, duration_weeks = %s, total_sessions = %s, skill_level = 'Intermediate', status = 'Ongoing'
                    WHERE id = %s
                """, (description, duration_weeks, total_sessions, course_id))
            else:
                print(f" [+] Creating new course: {title}")
                cursor.execute("""
                    INSERT INTO courses (title, description, image_url, duration_weeks, total_sessions, skill_level, status, is_public)
                    VALUES (%s, %s, %s, %s, %s, 'Intermediate', 'Ongoing', 1)
                """, (title, description, f"/data/courses/images/default_{folder}.png", duration_weeks, total_sessions))
                course_id = cursor.lastrowid

            # 5. Process Sessions/Materials
            if material_files:
                # Sort materials to ensure correct order
                material_files.sort()
                for mat_file in material_files:
                    mat_path = os.path.join(folder_path, mat_file)
                    with open(mat_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        first_line = content.split('\n')[0].strip()
                        topic = first_line if first_line else "General Session"
                        
                    # Check if session exists for this course and topic
                    cursor.execute("SELECT id FROM course_sessions WHERE course_id = %s AND topic = %s", (course_id, topic))
                    existing_session = cursor.fetchone()
                    
                    materials_json = json.dumps([{"type": "text", "content": content, "filename": mat_file}])
                    
                    if existing_session:
                        print(f"   [*] Updating session: {topic}")
                        cursor.execute("""
                            UPDATE course_sessions SET materials = %s WHERE id = %s
                        """, (materials_json, existing_session['id']))
                    else:
                        print(f"   [+] Adding session: {topic}")
                        cursor.execute("""
                            INSERT INTO course_sessions (course_id, topic, materials)
                            VALUES (%s, %s, %s)
                        """, (course_id, topic, materials_json))

            # 6. Process Trainees
            trainees_json_path = os.path.join(folder_path, 'trainees.json')
            if os.path.exists(trainees_json_path):
                with open(trainees_json_path, 'r', encoding='utf-8') as f:
                    trainees = json.load(f)
                
                print(f" [*] Processing {len(trainees)} trainees...")
                for trainee in trainees:
                    # Try to find user by name or ID
                    name_en = trainee.get('name_en')
                    name_ar = trainee.get('name_ar')
                    
                    cursor.execute("SELECT id FROM users WHERE full_name_en = %s OR full_name_ar = %s", (name_en, name_ar))
                    user = cursor.fetchone()
                    
                    if user:
                        user_id = user['id']
                        # Link to course via applications
                        cursor.execute("SELECT id FROM applications WHERE user_id = %s AND course_id = %s", (user_id, course_id))
                        if not cursor.fetchone():
                            print(f"   [+] Enrolling trainee: {name_en}")
                            cursor.execute("""
                                INSERT INTO applications (user_id, course_id, status, motivation_data, research_publication, references_data, logistics, identity_photos, quiz_results, quiz_scores)
                                VALUES (%s, %s, 'approved', '{}', '[]', '[]', '{}', '{}', '[]', '{}')
                            """, (user_id, course_id))
                    else:
                        print(f"   [!] Trainee not found in users table: {name_en}")

            # 7. Process Trainers
            trainers_json_path = os.path.join(folder_path, 'trainers.json')
            if os.path.exists(trainers_json_path):
                with open(trainers_json_path, 'r', encoding='utf-8') as f:
                    trainers = json.load(f)
                
                for trainer in trainers:
                    # Link via course_trainers
                    # Assuming trainer is identified by national_id in the JSON
                    national_id = trainer.get('national_id')
                    if national_id:
                        cursor.execute("SELECT id FROM course_trainers WHERE course_id = %s AND trainer_national_id = %s", (course_id, national_id))
                        if not cursor.fetchone():
                            cursor.execute("INSERT INTO course_trainers (course_id, trainer_national_id) VALUES (%s, %s)", (course_id, national_id))

            # 8. Process Assignments
            assignments_dir = os.path.join(folder_path, 'assignments')
            if os.path.exists(assignments_dir):
                assignment_files = [f for f in os.listdir(assignments_dir) if f.endswith('.txt') or f.endswith('.pdf') or f.endswith('.docx')]
                print(f" [*] Processing {len(assignment_files)} assignments...")
                
                from datetime import datetime, timedelta
                default_deadline = datetime.now() + timedelta(days=7)
                
                for assign_file in assignment_files:
                    assign_path = os.path.join(assignments_dir, assign_file)
                    title = assign_file.replace('_', ' ').replace('.txt', '').replace('.pdf', '').replace('.docx', '').title()
                    
                    description = ""
                    if assign_file.endswith('.txt'):
                        try:
                            with open(assign_path, 'r', encoding='utf-8') as f:
                                description = f.read()
                        except:
                            description = f"Assignment instructions in {assign_file}"
                    else:
                        description = f"Please refer to the attached file: {assign_file}"

                    # Check if assignment exists
                    cursor.execute("SELECT id FROM assignments WHERE course_id = %s AND title = %s", (course_id, title))
                    existing_assign = cursor.fetchone()
                    
                    if existing_assign:
                        print(f"   [*] Updating assignment: {title}")
                        cursor.execute("""
                            UPDATE assignments 
                            SET description = %s, file_path = %s
                            WHERE id = %s
                        """, (description, f"/data/courses/{folder}/assignments/{assign_file}", existing_assign['id']))
                    else:
                        print(f"   [+] Adding assignment: {title}")
                        cursor.execute("""
                            INSERT INTO assignments (course_id, title, description, file_path, deadline, max_grade)
                            VALUES (%s, %s, %s, %s, %s, 10.00)
                        """, (course_id, title, description, f"/data/courses/{folder}/assignments/{assign_file}", default_deadline))

        db.commit()
        print("\n[SUCCESS] Course injection completed.")

    except Exception as e:
        print(f"[!] Error during injection: {e}")
        db.rollback()
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    inject_courses()
