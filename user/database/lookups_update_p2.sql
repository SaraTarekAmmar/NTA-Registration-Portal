-- NTA Portal - Lookup Tables Expansion Part 2
USE nta_portal;

-- 7. Marital Status Master
CREATE TABLE IF NOT EXISTS `marital_status_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(100) NOT NULL,
  `name_ar` varchar(100) NOT NULL,
  `code` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `marital_status_master` (`name_en`, `name_ar`, `code`) VALUES
('Single', 'أعزب / عزباء', 'single'),
('Married', 'متزوج / متزوجة', 'married'),
('Divorced', 'مطلق / مطلقة', 'divorced'),
('Widowed', 'أرمل / أرملة', 'widowed');

-- 8. Monthly Income Master
CREATE TABLE IF NOT EXISTS `monthly_income_master` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name_en` varchar(100) NOT NULL,
  `name_ar` varchar(100) NOT NULL,
  `code` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `monthly_income_master` (`name_en`, `name_ar`, `code`) VALUES
('Below 5,000', 'أقل من 5,000', 'below_5000'),
('5,000 - 10,000', '5,000 - 10,000', '5000_10000'),
('10,000 - 20,000', '10,000 - 20,000', '10000_20000'),
('20,000 - 50,000', '20,000 - 50,000', '20000_50000'),
('Above 50,000', 'أكثر من 50,000', 'above_50000');
