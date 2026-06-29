-- 1. Update `users` table `role` ENUM to include all valid roles plus `committee_member`
ALTER TABLE users MODIFY COLUMN role ENUM('trainee','admin','editor','superadmin','trainer','coordinator','admission_manager','committee_member') COLLATE utf8mb4_unicode_ci NOT NULL;

-- 2. Add `reviewer_id` to `admission_interview_scores` if it doesn't exist, and add UNIQUE constraint
-- Note: MySQL doesn't have "ADD COLUMN IF NOT EXISTS" elegantly, so we'll just add it. If it fails, manual intervention might be needed, or we use a safe stored procedure.
-- However, since this table was recently created in the previous migration without reviewer_id, it should be safe to add.

ALTER TABLE admission_interview_scores 
ADD COLUMN reviewer_id INT NULL AFTER stage_id,
ADD CONSTRAINT fk_interview_score_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE SET NULL;

-- Remove old index and add unique constraint to prevent duplicate submissions per reviewer
-- The name might be slightly different so we just add the unique constraint.
ALTER TABLE admission_interview_scores
ADD UNIQUE KEY idx_unique_interview_eval (trainee_id, stage_id, reviewer_id);

-- 3. Create `interview_assignments` table
CREATE TABLE IF NOT EXISTS interview_assignments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  trainee_id INT NOT NULL,
  stage_id INT NOT NULL,
  reviewer_id INT NOT NULL,
  course_id INT NULL,
  status ENUM('pending', 'completed', 'cancelled') NOT NULL DEFAULT 'pending',
  assigned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  assigned_by INT NULL,
  UNIQUE KEY idx_unique_assignment (trainee_id, stage_id, reviewer_id),
  CONSTRAINT fk_assignment_trainee FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_assignment_reviewer FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_assignment_assigner FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL,
  CONSTRAINT fk_assignment_course FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);
