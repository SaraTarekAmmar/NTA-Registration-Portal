-- Interview session metadata on each committee evaluation row.
-- MySQL has no ADD COLUMN IF NOT EXISTS; guard manually or ignore dup-column errors.
ALTER TABLE admission_interview_scores ADD COLUMN session_start DATETIME NULL;
ALTER TABLE admission_interview_scores ADD COLUMN session_end DATETIME NULL;
ALTER TABLE admission_interview_scores ADD COLUMN governorate VARCHAR(128) NULL;
ALTER TABLE admission_interview_scores ADD COLUMN still_on_duty TINYINT(1) NULL;
