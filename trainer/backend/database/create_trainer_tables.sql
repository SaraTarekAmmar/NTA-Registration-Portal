-- 1. Create trainer_profiles Table
CREATE TABLE IF NOT EXISTS `trainer_profiles` (
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

-- 2. Create trainer_education Table
CREATE TABLE IF NOT EXISTS `trainer_education` (
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

-- 3. Create trainer_experience Table
CREATE TABLE IF NOT EXISTS `trainer_experience` (
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

-- 4. Create trainer_skills Table
CREATE TABLE IF NOT EXISTS `trainer_skills` (
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

-- 5. Create trainer_languages Table
CREATE TABLE IF NOT EXISTS `trainer_languages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `language_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `proficiency` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_languages_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Create trainer_awards Table
CREATE TABLE IF NOT EXISTS `trainer_awards` (
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

-- 7. Create trainer_community Table
CREATE TABLE IF NOT EXISTS `trainer_community` (
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

-- 8. Create trainer_references Table
CREATE TABLE IF NOT EXISTS `trainer_references` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `relationship` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contact_info` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_references_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Create trainer_social_media Table
CREATE TABLE IF NOT EXISTS `trainer_social_media` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `platform_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `profile_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_social_media_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Create trainer_standardized_tests Table
CREATE TABLE IF NOT EXISTS `trainer_standardized_tests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `trainer_id` int NOT NULL,
  `test_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `score` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `date_taken` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `trainer_id` (`trainer_id`),
  CONSTRAINT `trainer_standardized_tests_ibfk_1` FOREIGN KEY (`trainer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
