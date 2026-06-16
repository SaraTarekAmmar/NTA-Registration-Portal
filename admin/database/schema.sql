-- NTA Portal - Actual Database Schema Export
-- Generated at: Thu 04/30/2026 04:31 AM

CREATE DATABASE IF NOT EXISTS nta_portal;
USE nta_portal;

-- Table structure for activity_logs
CREATE TABLE `activity_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `category` enum('PASSIVE','AUTH','ACTION','ADMIN','SYSTEM') NOT NULL,
  `event_type` varchar(100) NOT NULL,
  `user_id` int DEFAULT NULL,
  `national_id` varchar(14) DEFAULT NULL,
  `role` varchar(50) DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `request_path` varchar(255) DEFAULT NULL,
  `status_code` int DEFAULT NULL,
  `details` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `timestamp` (`timestamp`),
  KEY `category` (`category`),
  KEY `user_id` (`user_id`),
  KEY `national_id` (`national_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table structure for admission_sorting_results (Replaces legacy ID OCR)
CREATE TABLE `admission_sorting_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int NOT NULL,
  `course_id` int NOT NULL,
  `identity_status` varchar(50) DEFAULT 'Flagged',
  `identity_details` json DEFAULT NULL,
  `professional_status` varchar(50) DEFAULT 'Partial',
  `professional_details` json DEFAULT NULL,
  `education_status` varchar(50) DEFAULT 'Inconsistent',
  `education_details` json DEFAULT NULL,
  `final_judge` varchar(50) DEFAULT 'Rejected',
  `confidence_score` int DEFAULT '0',
  `ai_summary` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `admission_sorting_results_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `admission_sorting_results_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for admission_stage_4_exams
-- Stores a permanent snapshot of Stage 4 standardized exam scores for each applicant.
-- Scores are sourced from trainee_exam_submissions (written by the exam portal)
-- and mirrored here when an admin submits the Stage 4 review.
CREATE TABLE `admission_stage_4_exams` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int DEFAULT NULL,
  `arabic_score` decimal(5,2) DEFAULT NULL,
  `english_score` decimal(5,2) DEFAULT NULL,
  `public_knowledge_score` decimal(5,2) DEFAULT NULL,
  `overall_score` decimal(5,2) DEFAULT NULL,
  `admin_notes` text COLLATE utf8mb4_unicode_ci,
  `reviewed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `admission_stage_4_exams_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for answers
CREATE TABLE `answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `answer_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_correct` tinyint(1) NOT NULL DEFAULT '0',
  `fraction` decimal(5,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `answers_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for applications
CREATE TABLE `applications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `course_id` int NOT NULL,
  `status` enum('idle','waiting','approved') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'idle',
  `applied_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `motivation_data` json DEFAULT NULL,
  `research_publication` json DEFAULT NULL,
  `references_data` json DEFAULT NULL,
  `logistics` json DEFAULT NULL,
  `identity_photos` json DEFAULT NULL,
  `quiz_results` json DEFAULT NULL,
  `quiz_scores` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`course_id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `applications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `applications_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for attendance_logs
CREATE TABLE `attendance_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_id` int NOT NULL,
  `match_score` decimal(5,2) NOT NULL,
  `event_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'ENTER',
  `image_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `recorded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `national_id` (`national_id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `attendance_logs_ibfk_1` FOREIGN KEY (`national_id`) REFERENCES `users` (`national_id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_logs_ibfk_2` FOREIGN KEY (`session_id`) REFERENCES `course_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for attendance_permissions
CREATE TABLE `attendance_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `course_id` int NOT NULL,
  `type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `date` date NOT NULL,
  `reason` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('pending','accepted','rejected') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `attendance_permissions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `attendance_permissions_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for chat_history
CREATE TABLE `chat_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `role` enum('trainee','admin','editor') COLLATE utf8mb4_unicode_ci NOT NULL,
  `question` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `reply` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `chat_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for countries_master
CREATE TABLE `countries_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `code` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=200 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for course_cohorts
CREATE TABLE `course_cohorts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `cohort_data` json NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `course_cohorts_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for course_sessions
CREATE TABLE `course_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `session_date` timestamp NULL DEFAULT NULL,
  `topic` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `materials` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `course_sessions_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for course_trainers
CREATE TABLE `course_trainers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `trainer_national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`,`trainer_national_id`),
  KEY `trainer_national_id` (`trainer_national_id`),
  CONSTRAINT `course_trainers_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `course_trainers_ibfk_2` FOREIGN KEY (`trainer_national_id`) REFERENCES `users` (`national_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for courses
CREATE TABLE `courses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `image_url` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `duration_weeks` int NOT NULL,
  `total_sessions` int NOT NULL,
  `skill_level` enum('Beginner','Intermediate','Advanced') COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('Upcoming','Ongoing','Completed') COLLATE utf8mb4_unicode_ci NOT NULL,
  `has_active_quiz` tinyint(1) DEFAULT '0',
  `quiz_json` json DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for grades
CREATE TABLE `grades` (
  `id` int NOT NULL AUTO_INCREMENT,
  `national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  `course_id` int NOT NULL,
  `quiz_id` int DEFAULT NULL,
  `final_grade` decimal(5,2) NOT NULL,
  `raw_grade` decimal(5,2) NOT NULL,
  `max_grade` decimal(5,2) NOT NULL,
  `percentage` decimal(5,2) GENERATED ALWAYS AS (((`raw_grade` / `max_grade`) * 100)) STORED,
  PRIMARY KEY (`id`),
  KEY `national_id` (`national_id`),
  KEY `course_id` (`course_id`),
  KEY `quiz_id` (`quiz_id`),
  CONSTRAINT `grades_ibfk_1` FOREIGN KEY (`national_id`) REFERENCES `users` (`national_id`) ON DELETE CASCADE,
  CONSTRAINT `grades_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `grades_ibfk_3` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for interests_master
CREATE TABLE `interests_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=135 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for language_proficiency_master
CREATE TABLE `language_proficiency_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `level_en` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level_ar` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for languages_master
CREATE TABLE `languages_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=187 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for pipeline_state
CREATE TABLE `pipeline_state` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int NOT NULL,
  `current_stage_id` int NOT NULL DEFAULT '1',
  `status` enum('active','rejected','completed') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'active',
  `rejection_note` text COLLATE utf8mb4_unicode_ci,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `pipeline_state_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=69 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for private_course_assignments
CREATE TABLE `private_course_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  `assigned_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `private_course_assignments_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for questions
CREATE TABLE `questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `question_text` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `question_type` enum('mcq','truefalse','essay','shortanswer') COLLATE utf8mb4_unicode_ci NOT NULL,
  `max_mark` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `quiz_id` (`quiz_id`),
  CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for quiz_attempts
CREATE TABLE `quiz_attempts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `course_id` int NOT NULL,
  `score` decimal(5,2) NOT NULL,
  `details_json` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `quiz_attempts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `quiz_attempts_ibfk_2` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for quizzes
CREATE TABLE `quizzes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `time_open` timestamp NULL DEFAULT NULL,
  `time_close` timestamp NULL DEFAULT NULL,
  `max_grade` decimal(5,2) NOT NULL DEFAULT '100.00',
  `attempts_allowed` int NOT NULL DEFAULT '1',
  `session_id` int DEFAULT NULL,
  `availability_duration_hours` int DEFAULT '24',
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  KEY `fk_quiz_session` (`session_id`),
  CONSTRAINT `fk_quiz_session` FOREIGN KEY (`session_id`) REFERENCES `course_sessions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `quizzes_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for quiz_access_overrides
CREATE TABLE `quiz_access_overrides` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int NOT NULL,
  `trainee_id` int NOT NULL,
  `override_deadline` timestamp NOT NULL,
  `reason` varchar(255) DEFAULT NULL,
  `granted_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_override` (`quiz_id`, `trainee_id`),
  KEY `quiz_id` (`quiz_id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `fk_override_quiz` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_override_trainee` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for skill_categories
CREATE TABLE `skill_categories` (
  `id` int NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description_en` text COLLATE utf8mb4_unicode_ci,
  `description_ar` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for skill_subcategories
CREATE TABLE `skill_subcategories` (
  `id` int NOT NULL,
  `category_id` int NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description_en` text COLLATE utf8mb4_unicode_ci,
  `description_ar` text COLLATE utf8mb4_unicode_ci,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `skill_subcategories_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `skill_categories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for skills_master
CREATE TABLE `skills_master` (
  `id` int NOT NULL,
  `subcategory_id` int NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `subcategory_id` (`subcategory_id`),
  CONSTRAINT `skills_master_ibfk_1` FOREIGN KEY (`subcategory_id`) REFERENCES `skill_subcategories` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for stage_reviews
CREATE TABLE `stage_reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int DEFAULT NULL,
  `stage_id` int NOT NULL,
  `reviewer_id` int NOT NULL,
  `result` enum('Active','Rejected') COLLATE utf8mb4_unicode_ci NOT NULL,
  `reviewer_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `review_date` date NOT NULL,
  `notes` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `attachment_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
  `details` json DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  KEY `reviewer_id` (`reviewer_id`),
  CONSTRAINT `stage_reviews_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `stage_reviews_ibfk_2` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for states_master
CREATE TABLE `states_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `country_id` int NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `country_id` (`country_id`),
  CONSTRAINT `states_master_ibfk_1` FOREIGN KEY (`country_id`) REFERENCES `countries_master` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4760 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Table structure for trainee_profiles
CREATE TABLE `trainee_profiles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `professional_summary` json DEFAULT NULL,
  `registration_extra` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `trainee_profiles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=70 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for trainee_experience (Normalized from JSON)
CREATE TABLE `trainee_experience` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int NOT NULL,
  `organization` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `responsibilities` text COLLATE utf8mb4_unicode_ci,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `trainee_experience_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for trainee_skills (Normalized from JSON)
CREATE TABLE `trainee_skills` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int NOT NULL,
  `skill_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `proficiency` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `trainee_skills_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for trainee_education (Normalized from JSON)
CREATE TABLE `trainee_education` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int NOT NULL,
  `institution` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `major` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `degree` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `grad_year` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `trainee_education_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for trainee_documents (Normalized from JSON)
CREATE TABLE `trainee_documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainee_id` int NOT NULL,
  `doc_type` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `uploaded_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `trainee_documents_ibfk_1` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for universities_master
CREATE TABLE `universities_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `country_id` int NOT NULL,
  `name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_ar` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `country_id` (`country_id`),
  CONSTRAINT `universities_master_ibfk_1` FOREIGN KEY (`country_id`) REFERENCES `countries_master` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10892 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for user_answers
CREATE TABLE `user_answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `attempt_id` int NOT NULL,
  `question_id` int NOT NULL,
  `national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  `response` text COLLATE utf8mb4_unicode_ci,
  `is_correct` tinyint(1) DEFAULT NULL,
  `mark` decimal(5,2) DEFAULT NULL,
  `max_mark` decimal(5,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `attempt_id` (`attempt_id`),
  KEY `question_id` (`question_id`),
  KEY `national_id` (`national_id`),
  CONSTRAINT `user_answers_ibfk_1` FOREIGN KEY (`attempt_id`) REFERENCES `quiz_attempts` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_answers_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_answers_ibfk_3` FOREIGN KEY (`national_id`) REFERENCES `users` (`national_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for users
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `full_name_ar` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `full_name_en` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` enum('trainee','admin','editor','superadmin','trainer') COLLATE utf8mb4_unicode_ci NOT NULL,
  `dob` date NOT NULL,
  `gender` enum('male','female') COLLATE utf8mb4_unicode_ci NOT NULL,
  `marital_status` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  UNIQUE KEY `national_id` (`national_id`)
) ENGINE=InnoDB AUTO_INCREMENT=91 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- Table structure for assignment_submissions
CREATE TABLE `assignment_submissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `assignment_id` int NOT NULL,
  `trainee_id` int NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `grade` decimal(5,2) DEFAULT NULL,
  `feedback` text,
  `status` enum('pending','graded') DEFAULT 'pending',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_submission` (`assignment_id`,`trainee_id`),
  KEY `assignment_id` (`assignment_id`),
  KEY `trainee_id` (`trainee_id`),
  CONSTRAINT `assignment_submissions_ibfk_1` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `assignment_submissions_ibfk_2` FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for assignments
CREATE TABLE `assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `file_path` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deadline` datetime NOT NULL,
  `max_grade` decimal(5,2) DEFAULT '10.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `assignments_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for cv_matching_results
CREATE TABLE `cv_matching_results` (
  `id` int NOT NULL AUTO_INCREMENT,
  `course_id` int NOT NULL,
  `national_id` varchar(14) COLLATE utf8mb4_unicode_ci NOT NULL,
  `match_score` float DEFAULT NULL,
  `evidence` text COLLATE utf8mb4_unicode_ci,
  `analysis_json` json DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `course_id` (`course_id`,`national_id`),
  KEY `national_id` (`national_id`),
  CONSTRAINT `cv_matching_results_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `cv_matching_results_ibfk_2` FOREIGN KEY (`national_id`) REFERENCES `users` (`national_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for exams
CREATE TABLE `exams` (
    `id` int NOT NULL AUTO_INCREMENT,
    `subject` enum('arabic', 'english', 'public_knowledge') NOT NULL,
    `title` varchar(255) NOT NULL,
    `content_json` json NOT NULL,
    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table structure for trainee_exam_submissions
CREATE TABLE `trainee_exam_submissions` (
    `id` int NOT NULL AUTO_INCREMENT,
    `trainee_id` int NOT NULL,
    `subject` enum('arabic', 'english', 'public_knowledge') NOT NULL,
    `answers_json` json NOT NULL,
    `score` decimal(5,2),
    `processed_results` json,
    `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`trainee_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


DROP TABLE IF EXISTS `trainer_profiles`;
CREATE TABLE `trainer_profiles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `phone_numbers` json NOT NULL,
  `secondary_email` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` text COLLATE utf8mb4_unicode_ci,
  `emergency_contacts` json DEFAULT NULL,
  `technical_skills` json DEFAULT NULL,
  `soft_skills` json DEFAULT NULL,
  `computer_skills` json DEFAULT NULL,
  `academic_history` json DEFAULT NULL,
  `professional_history` json DEFAULT NULL,
  `professional_summary` json DEFAULT NULL,
  `awards_impact` json DEFAULT NULL,
  `community_extracurricular` json DEFAULT NULL,
  `documents` json DEFAULT NULL,
  `registration_extra` json DEFAULT NULL,
  `photo_front_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nationality` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `military_status` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `military_reason` text COLLATE utf8mb4_unicode_ci,
  `native_language` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `english_proficiency` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `permanent_address` text COLLATE utf8mb4_unicode_ci,
  `portfolio_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `learning_objectives` text COLLATE utf8mb4_unicode_ci,
  `dietary_restrictions` text COLLATE utf8mb4_unicode_ci,
  `accessibility_requirements` text COLLATE utf8mb4_unicode_ci,
  `other_skills_free_text` text COLLATE utf8mb4_unicode_ci,
  `interests_description` text COLLATE utf8mb4_unicode_ci,
  `uses_social_media` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `data_accuracy_confirmed` tinyint(1) DEFAULT '0',
  `professional_summary_text` text COLLATE utf8mb4_unicode_ci,
  `years_experience` int DEFAULT NULL,
  `id_scan_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cv_resume_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `organizational_chart_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `criminal_record_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `employer_noc_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `scholarship_essay_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `graduation_certificate_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_card_front_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_card_back_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_card_side_right_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `id_card_side_left_path` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `has_political_participation` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `political_party_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `political_role` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `political_work_details` text COLLATE utf8mb4_unicode_ci,
  `has_political_candidacy` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `candidacy_position_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `candidacy_result` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `candidacy_experience` text COLLATE utf8mb4_unicode_ci,
  `has_criminal_convictions` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `conviction_description` text COLLATE utf8mb4_unicode_ci,
  `country_of_stay` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `government_or_state` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `current_address` text COLLATE utf8mb4_unicode_ci,
  `emergency_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `emergency_phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `monthly_average_income` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `number_of_nationalities` int DEFAULT '1',
  `identity_doc_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `has_prior_criminal_convictions` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `prior_conviction_description` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `trainer_profiles_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_education`;
CREATE TABLE `trainer_education` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `institution` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `major` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `degree` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gpa` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `grad_year` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ranking` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_education_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_experience`;
CREATE TABLE `trainer_experience` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `organization` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `responsibilities` text COLLATE utf8mb4_unicode_ci,
  `reason_for_leaving` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_experience_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_skills`;
CREATE TABLE `trainer_skills` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `skill_id` int DEFAULT NULL,
  `category_id` int DEFAULT NULL,
  `skill_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `proficiency` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_skills_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_languages`;
CREATE TABLE `trainer_languages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `language_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `proficiency` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_languages_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_awards`;
CREATE TABLE `trainer_awards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `award_title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `issuing_body` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `achievement` text COLLATE utf8mb4_unicode_ci,
  `date_received` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_awards_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_community`;
CREATE TABLE `trainer_community` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `skill_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `organization` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date` date DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_community_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_references`;
CREATE TABLE `trainer_references` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `relationship` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_info` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_references_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_social_media`;
CREATE TABLE `trainer_social_media` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `platform_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `profile_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_social_media_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS `trainer_standardized_tests`;
CREATE TABLE `trainer_standardized_tests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `test_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_taken` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_standardized_tests_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


