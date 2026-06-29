-- 1. Class Trainer Matrix
ALTER TABLE class_matrix_recommendations
  ADD COLUMN trainer_strengths TEXT,
  ADD COLUMN trainer_weaknesses TEXT,
  ADD COLUMN trainer_reason TEXT,
  ADD COLUMN trainee_strengths TEXT,
  ADD COLUMN trainee_weaknesses TEXT,
  ADD COLUMN trainee_reason TEXT,
  ADD COLUMN trainee_confidence_score INT DEFAULT 50,
  DROP COLUMN trainer_analysis,
  DROP COLUMN trainee_analysis;

-- 2. Requirement Analyzer
CREATE TABLE cv_matching_requirements (
  id INT NOT NULL AUTO_INCREMENT,
  match_id INT NOT NULL,
  requirement_topic VARCHAR(255) NOT NULL,
  score INT NOT NULL,
  evidence TEXT NOT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (match_id) REFERENCES cv_matching_results(id) ON DELETE CASCADE
);

ALTER TABLE cv_matching_results
  DROP COLUMN analysis_json;

-- 3. Electronic Sorting
CREATE TABLE admission_stage_1_identity (
  id INT NOT NULL AUTO_INCREMENT,
  trainee_id INT NOT NULL,
  full_name_score INT DEFAULT 0,
  full_name_ai VARCHAR(255),
  national_id_score INT DEFAULT 0,
  national_id_ai VARCHAR(255),
  gender_score INT DEFAULT 0,
  gender_ai VARCHAR(50),
  dob_score INT DEFAULT 0,
  dob_ai VARCHAR(50),
  overall_status VARCHAR(50),
  confidence INT DEFAULT 0,
  rejection_reason TEXT,
  PRIMARY KEY (id),
  FOREIGN KEY (trainee_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE admission_sorting_experience (
  id INT NOT NULL AUTO_INCREMENT,
  sorting_id INT NOT NULL,
  item_description TEXT,
  match_status VARCHAR(50),
  ai_comment TEXT,
  PRIMARY KEY (id),
  FOREIGN KEY (sorting_id) REFERENCES admission_sorting_results(id) ON DELETE CASCADE
);

CREATE TABLE admission_sorting_education (
  id INT NOT NULL AUTO_INCREMENT,
  sorting_id INT NOT NULL,
  degree_info TEXT,
  match_status VARCHAR(50),
  PRIMARY KEY (id),
  FOREIGN KEY (sorting_id) REFERENCES admission_sorting_results(id) ON DELETE CASCADE
);

ALTER TABLE admission_sorting_results
  DROP COLUMN identity_details,
  DROP COLUMN professional_details,
  DROP COLUMN education_details;
