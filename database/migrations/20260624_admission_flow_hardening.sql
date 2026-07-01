-- Admission flow hardening
-- Apply manually before enabling security/silent rejection production workflows.

-- 1) Preserve rejected applicant audit rows after a user is removed or anonymized.
-- If your constraint name differs, inspect SHOW CREATE TABLE stage_reviews first.
ALTER TABLE stage_reviews DROP FOREIGN KEY stage_reviews_ibfk_1;
ALTER TABLE stage_reviews MODIFY trainee_id INT NULL;
ALTER TABLE stage_reviews
  ADD CONSTRAINT stage_reviews_ibfk_1
  FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE SET NULL;

-- 2) Internal-only security decision ledger. Do not expose these notes to applicants.
CREATE TABLE IF NOT EXISTS admission_security_decisions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  applicant_user_id INT NULL,
  national_id VARCHAR(64) NULL,
  passport_number VARCHAR(64) NULL,
  course_id INT NULL,
  decision ENUM('clear','hold','silent_reject','block_future') NOT NULL DEFAULT 'hold',
  internal_reason TEXT NULL,
  decided_by INT NULL,
  decided_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_security_national_id (national_id),
  INDEX idx_security_passport (passport_number),
  INDEX idx_security_course (course_id),
  CONSTRAINT fk_security_applicant FOREIGN KEY (applicant_user_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_security_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL,
  CONSTRAINT fk_security_decider FOREIGN KEY (decided_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 3) Optional normalized committee scoring table for the 10/15-axis interview forms.
CREATE TABLE IF NOT EXISTS admission_interview_scores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trainee_id INT NULL,
  course_id INT NULL,
  stage_id INT NOT NULL,
  committee_member_name VARCHAR(255) NOT NULL,
  criteria_json JSON NOT NULL,
  total_score DECIMAL(8,2) NOT NULL DEFAULT 0,
  total_max DECIMAL(8,2) NOT NULL DEFAULT 0,
  recommendation ENUM('accept','waitlist','unsuitable') NULL,
  notes TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_interview_scores_trainee_stage (trainee_id, stage_id),
  INDEX idx_interview_scores_course_stage (course_id, stage_id),
  CONSTRAINT fk_interview_score_trainee FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_interview_score_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE SET NULL
);
