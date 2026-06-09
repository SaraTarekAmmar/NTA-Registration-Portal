-- AI Specific Tables (Extended from main schema)
-- These tables are managed via the Super Admin component but stored in the central nta_portal database.

-- 1. Attendance Logs (Face Recognition)
CREATE TABLE IF NOT EXISTS attendance_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    national_id VARCHAR(14) NOT NULL,
    session_id INT NOT NULL,
    match_score DECIMAL(5,2) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (national_id) REFERENCES users(national_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES course_sessions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Course Cohorts (Hungarian Matchmaker Results)
CREATE TABLE IF NOT EXISTS course_cohorts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    cohort_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Topic Priorities (Material Analysis Results)
CREATE TABLE IF NOT EXISTS topic_priorities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    priority_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. AI Verification Results (OCR & Identity Review)
CREATE TABLE IF NOT EXISTS ai_verification_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    national_id VARCHAR(14) NOT NULL,
    verification_type ENUM('OCR', 'ADMISSION', 'QUIZ') NOT NULL,
    status ENUM('Accepted', 'Rejected', 'Pending') NOT NULL DEFAULT 'Pending',
    rejection_reason TEXT,
    metadata JSON DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (national_id) REFERENCES users(national_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
