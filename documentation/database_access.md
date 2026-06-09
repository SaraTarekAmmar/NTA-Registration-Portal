# Database Access & Verification Guide

This guide explains how to connect to the NTA Registration Portal database to verify that API calls are correctly reading from and writing to the system.

## 1. Automated Environment Setup (Windows)
Before manual connection, you can initialize the entire database environment by running:
```batch
deploy\setup_tools.bat
```
This installs MySQL Server and Workbench. The system launcher (`RUN_SYSTEM.bat`) will then create the database and schema for you automatically.

## 2. Connection Parameters
Use the following credentials to connect via MySQL Workbench, HeidiSQL, or the command line:

- **Host**: `localhost`
- **Port**: `3306` (Default MySQL port)
- **User**: `root`
- **Password**: `nta_password_2024` (or your local root password)
- **Database**: `nta_portal`

## 2. Tools for Access
- **MySQL Workbench** (Recommended): Visual interface for running queries.
- **VS Code MySQL Extension**: Best for quick checks without leaving the IDE.
- **Command Line**:
  ```bash
  mysql -u root -p nta_portal
  ```

## 3. Key Verification Queries

### Verify Trainee Profile Updates
To check if the **Edit Profile** API successfully updated a trainee's data:
```sql
-- Check core user data
SELECT full_name_ar, full_name_en, email, national_id 
FROM users 
WHERE id = [TRAINEE_ID];

-- Check extended profile details
SELECT * FROM trainee_profiles WHERE user_id = [TRAINEE_ID];
```

### Verify Course Applications
To see if a trainee's application was correctly recorded:
```sql
SELECT a.id, u.full_name_ar, c.title, a.status, a.created_at
FROM applications a
JOIN users u ON a.user_id = u.id
JOIN courses c ON a.course_id = c.id
ORDER BY a.created_at DESC;
```

### Verify Pipeline Transitions
To confirm if an Admin's "Accept" click moved a candidate to the next stage:
```sql
SELECT t.full_name_ar, ps.current_stage_id, ps.status
FROM pipeline_state ps
JOIN users t ON ps.trainee_id = t.id
WHERE t.id = [TRAINEE_ID];
```

### Verify Electronic Sorting (AI Audit)
To check the detailed 4-phase AI audit results for a trainee:
```sql
-- Check overall judge and confidence
SELECT trainee_id, final_judge, confidence_score, ai_summary 
FROM admission_sorting_results 
WHERE trainee_id = [TRAINEE_ID];

-- Check specific phase statuses (Identity, Professional, Education)
SELECT identity_status, professional_status, education_status
FROM admission_sorting_results 
WHERE trainee_id = [TRAINEE_ID];

-- Check the automated audit log entry
SELECT * FROM stage_reviews 
WHERE trainee_id = [TRAINEE_ID] AND reviewer_name LIKE '%Admission AI%';
```

## 5. Verifying Document Uploads

To check if a trainee's CV and documents were stored correctly:
```sql
SELECT documents FROM trainee_profiles WHERE user_id = [TRAINEE_ID];
```

To check for supplemental registration metadata:
```sql
SELECT registration_extra FROM trainee_profiles WHERE user_id = [TRAINEE_ID];
```

To see candidates with specific accessibility needs:
```sql
SELECT u.full_name_ar, u.email 
FROM users u 
JOIN trainee_profiles tp ON u.id = tp.user_id 
WHERE JSON_EXTRACT(tp.registration_extra, '$.accessibility_needs') IS NOT NULL;
```

## 7. Checking Chat History

To audit what users are asking the LLM and the bot's replies:
```sql
SELECT u.full_name_ar, ch.role, ch.question, ch.reply, ch.created_at 
FROM chat_history ch
JOIN users u ON ch.user_id = u.id
ORDER BY ch.created_at DESC;
```

## 6. Mapping Skills
To list all skills in a specific subcategory (Skill Area):
```sql
SELECT * FROM skills_master WHERE subcategory_id = [ID];
```
To show the entire hierarchy for a category:
```sql
SELECT sc.name_en AS Category, ss.name_en AS Area, sm.name_en AS Skill
FROM skills_master sm
JOIN skill_subcategories ss ON sm.subcategory_id = ss.id
JOIN skill_categories sc ON ss.category_id = sc.id
WHERE sc.id = 1; -- 1: Technical, 2: Computer, etc.
```

### 7. Languages & Proficiency
To list all available languages:
```sql
SELECT * FROM languages_master;
```
To show proficiency levels:
```sql
SELECT * FROM language_proficiency_master;
```

## Troubleshooting
- **JSON Fields**: Extended profile data (skills, history, documents) is stored as JSON strings. Use `JSON_EXTRACT` or view the full column to see nested data.
- **Foreign Key Constraints**: Ensure you are deleting records in the correct order (Applications -> Pipeline State -> User) if you need to reset test data.
