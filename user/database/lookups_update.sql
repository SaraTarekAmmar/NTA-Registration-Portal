-- NTA Portal - Lookup Tables Expansion
-- Transitioning hardcoded UI elements to Live Database Lookups

USE nta_portal;

-- 1. Military Status Master
CREATE TABLE IF NOT EXISTS `military_status_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(100) NOT NULL,
  `name_ar` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `military_status_master` (`name_en`, `name_ar`) VALUES
('Completed', 'أدى الخدمة'),
('Exempted', 'إعفاء'),
('Postponed', 'تأجيل'),
('Currently Serving', 'مجند حالياً');

-- 2. Identity Document Types Master
CREATE TABLE IF NOT EXISTS `identity_doc_types_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(100) NOT NULL,
  `name_ar` varchar(100) NOT NULL,
  `code` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `identity_doc_types_master` (`name_en`, `name_ar`, `code`) VALUES
('National ID', 'البطاقة الشخصية', 'national_id'),
('Passport', 'جواز السفر', 'passport');

-- 3. Degree Levels Master
CREATE TABLE IF NOT EXISTS `degree_levels_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(100) NOT NULL,
  `name_ar` varchar(100) NOT NULL,
  `type` enum('undergraduate', 'postgraduate') DEFAULT 'undergraduate',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `degree_levels_master` (`name_en`, `name_ar`, `type`) VALUES
('Higher Degree', 'مؤهل عالي', 'undergraduate'),
('Above Intermediate', 'مؤهل فوق المتوسط', 'undergraduate'),
('Intermediate', 'مؤهل متوسط', 'undergraduate'),
('Master', 'ماجستير', 'postgraduate'),
('PhD', 'دكتوراه', 'postgraduate');

-- 4. Grades/GPA Master
CREATE TABLE IF NOT EXISTS `grades_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(50) NOT NULL,
  `name_ar` varchar(50) NOT NULL,
  `min_percentage` decimal(5,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `grades_master` (`name_en`, `name_ar`, `min_percentage`) VALUES
('Excellent', 'امتياز', 85.00),
('Very Good', 'جيد جداً', 75.00),
('Good', 'جيد', 65.00),
('Pass', 'مقبول', 50.00),
('A', 'أ', 90.00),
('B', 'ب', 80.00),
('C', 'ج', 70.00),
('D', 'د', 60.00);

-- 5. Ministries Master
CREATE TABLE IF NOT EXISTS `ministries_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(255) NOT NULL,
  `name_ar` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `ministries_master` (`name_en`, `name_ar`) VALUES
('Ministry of Education', 'التربية والتعليم'),
('Ministry of Health', 'الصحة'),
('Ministry of Finance', 'المالية'),
('Ministry of Communications', 'الاتصالات'),
('Ministry of Social Solidarity', 'التضامن الاجتماعي'),
('Ministry of Justice', 'العدل'),
('Ministry of Interior', 'الداخلية'),
('Ministry of Defense', 'الدفاع'),
('Ministry of Foreign Affairs', 'الخارجية'),
('Other', 'أخرى');

-- 6. Job Titles Master
CREATE TABLE IF NOT EXISTS `job_titles_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(255) NOT NULL,
  `name_ar` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `job_titles_master` (`name_en`, `name_ar`) VALUES
('Administrative Employee', 'موظف إداري'),
('Engineer', 'مهندس'),
('Specialist', 'أخصائي'),
('Manager', 'مدير'),
('Consultant', 'مستشار'),
('Director', 'رئيس قطاع / مدير عام'),
('Researcher', 'باحث'),
('Legal Counsel', 'مستشار قانوني'),
('IT Professional', 'متخصص تكنولوجيا معلومات'),
('Accountant', 'محاسب'),
('Other', 'أخرى');
