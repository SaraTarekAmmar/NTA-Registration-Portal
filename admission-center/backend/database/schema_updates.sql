-- Schema updates for missing registration fields

-- Contact Details (Step 2)
ALTER TABLE `trainee_profiles` ADD COLUMN `country_of_stay` VARCHAR(100) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `government_or_state` VARCHAR(100) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `city` VARCHAR(100) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `current_address` TEXT DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `permanent_address` TEXT DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `emergency_name` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `emergency_phone` VARCHAR(50) DEFAULT NULL;

-- Demographics (Step 1)
ALTER TABLE `trainee_profiles` ADD COLUMN `military_status` VARCHAR(50) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `military_reason` TEXT DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `monthly_average_income` VARCHAR(50) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `number_of_nationalities` INT DEFAULT 1;
ALTER TABLE `trainee_profiles` ADD COLUMN `identity_doc_type` VARCHAR(50) DEFAULT NULL;

-- Political & Legal (Step 7)
ALTER TABLE `trainee_profiles` ADD COLUMN `has_political_participation` VARCHAR(10) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `political_party_name` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `political_role` VARCHAR(255) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `political_work_details` TEXT DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `has_prior_criminal_convictions` VARCHAR(10) DEFAULT NULL;
ALTER TABLE `trainee_profiles` ADD COLUMN `prior_conviction_description` TEXT DEFAULT NULL;

