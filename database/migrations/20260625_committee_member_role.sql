-- Add 'committee_member' to users.role ENUM.
-- Idempotent script: Safe to run multiple times.

ALTER TABLE users MODIFY COLUMN role
  ENUM('trainee','admin','editor','superadmin','trainer','applicant','coordinator','committee_member')
  COLLATE utf8mb4_unicode_ci NOT NULL;
