-- NTA Portal - Lookup Tables Expansion Part 3 (Standardizing Codes)
USE nta_portal;

-- Update Military Status with Codes
ALTER TABLE `military_status_master` ADD COLUMN `code` varchar(50) AFTER `name_ar`;
UPDATE `military_status_master` SET `code` = 'completed' WHERE `name_en` = 'Completed';
UPDATE `military_status_master` SET `code` = 'exempted' WHERE `name_en` = 'Exempted';
UPDATE `military_status_master` SET `code` = 'postponed' WHERE `name_en` = 'Postponed';
UPDATE `military_status_master` SET `code` = 'currently_serving' WHERE `name_en` = 'Currently Serving';

-- Update Degree Levels with Codes
ALTER TABLE `degree_levels_master` ADD COLUMN `code` varchar(50) AFTER `type`;
UPDATE `degree_levels_master` SET `code` = 'higher_degree' WHERE `name_en` = 'Higher Degree';
UPDATE `degree_levels_master` SET `code` = 'above_intermediate' WHERE `name_en` = 'Above Intermediate';
UPDATE `degree_levels_master` SET `code` = 'intermediate' WHERE `name_en` = 'Intermediate';
UPDATE `degree_levels_master` SET `code` = 'master' WHERE `name_en` = 'Master';
UPDATE `degree_levels_master` SET `code` = 'phd' WHERE `name_en` = 'PhD';

-- Update Grades with Codes (use English names as codes)
ALTER TABLE `grades_master` ADD COLUMN `code` varchar(50) AFTER `min_percentage`;
UPDATE `grades_master` SET `code` = LOWER(REPLACE(name_en, ' ', '_'));
