-- Interview committee model for the digital interview-evaluation module.
-- Apply manually (or via deploy/run_migration). Idempotent (IF NOT EXISTS).

-- Interview committees: one per program/governorate/date grouping.
CREATE TABLE IF NOT EXISTS interview_committees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  committee_number VARCHAR(64) NOT NULL,
  course_id INT NULL,
  governorate VARCHAR(128) NULL,
  interview_date DATE NULL,
  coordinator_id INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_committee_course (course_id),
  INDEX idx_committee_number (committee_number),
  CONSTRAINT fk_committee_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL,
  CONSTRAINT fk_committee_coordinator FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Members of a committee (interviewers).
CREATE TABLE IF NOT EXISTS interview_committee_members (
  id INT AUTO_INCREMENT PRIMARY KEY,
  committee_id INT NOT NULL,
  member_name VARCHAR(255) NOT NULL,
  member_user_id INT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_member_committee (committee_id),
  CONSTRAINT fk_member_committee FOREIGN KEY (committee_id) REFERENCES interview_committees(id) ON DELETE CASCADE,
  CONSTRAINT fk_member_user FOREIGN KEY (member_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Applicants assigned to a committee.
CREATE TABLE IF NOT EXISTS interview_committee_applicants (
  id INT AUTO_INCREMENT PRIMARY KEY,
  committee_id INT NOT NULL,
  applicant_user_id INT NOT NULL,
  stage_id INT NOT NULL DEFAULT 5,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_committee_applicant (committee_id, applicant_user_id, stage_id),
  INDEX idx_applicant_committee (applicant_user_id),
  CONSTRAINT fk_ca_committee FOREIGN KEY (committee_id) REFERENCES interview_committees(id) ON DELETE CASCADE,
  CONSTRAINT fk_ca_applicant FOREIGN KEY (applicant_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Link interview scores to a committee (nullable; scores can predate committees).
ALTER TABLE admission_interview_scores
  ADD COLUMN IF NOT EXISTS committee_id INT NULL AFTER stage_id;
