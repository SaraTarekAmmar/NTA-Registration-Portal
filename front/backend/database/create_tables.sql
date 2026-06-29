-- ============================================================
--  FRONT PAGE PORTAL — DATABASE SCHEMA
--  All tables prefixed `front_` to stay isolated.
--  Run against: nta_portal database
-- ============================================================

-- ── 1. Front-page public signups (4-step registration) ──────
CREATE TABLE IF NOT EXISTS front_signups (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    national_id VARCHAR(20)  NOT NULL UNIQUE,
    full_name   VARCHAR(255) NOT NULL,
    phone       VARCHAR(20)  NOT NULL,
    email       VARCHAR(255) NULL,
    status      ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_front_signups_status  (status),
    INDEX idx_front_signups_nat_id  (national_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 2. Career / job listings ────────────────────────────────
CREATE TABLE IF NOT EXISTS front_careers (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    type         VARCHAR(50)  NOT NULL DEFAULT 'Full Time',
    location     VARCHAR(255) NULL,
    description  TEXT         NULL,
    requirements TEXT         NULL,
    is_active    TINYINT(1)   NOT NULL DEFAULT 1,
    created_by   VARCHAR(100) NULL,          -- editor national_id
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_front_careers_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 3. Career applications ───────────────────────────────────
CREATE TABLE IF NOT EXISTS front_career_applications (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    career_id   INT          NOT NULL,
    full_name   VARCHAR(255) NOT NULL,
    national_id VARCHAR(20)  NOT NULL,
    phone       VARCHAR(20)  NOT NULL,
    email       VARCHAR(255) NULL,
    cover_note  TEXT         NOT NULL,
    cv_filename VARCHAR(255) NOT NULL,
    cv_path     VARCHAR(512) NOT NULL,
    status      ENUM('new','reviewed','shortlisted','rejected') NOT NULL DEFAULT 'new',
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (career_id) REFERENCES front_careers(id) ON DELETE CASCADE,
    INDEX idx_fca_career (career_id),
    INDEX idx_fca_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 4. Page content / CMS ────────────────────────────────────
CREATE TABLE IF NOT EXISTS front_page_content (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    section_key     VARCHAR(100) NOT NULL,
    lang            ENUM('en','ar') NOT NULL DEFAULT 'en',
    sort_order      INT          NOT NULL DEFAULT 0,
    content_json    LONGTEXT     NULL,           -- all text / config fields
    media_type      ENUM('none','image','video') NOT NULL DEFAULT 'none',
    media_path      VARCHAR(512) NULL,           -- server path or external URL
    bg_color        VARCHAR(50)  NULL,           -- e.g. #FFFFFF or gradient string
    text_color      VARCHAR(50)  NULL,
    is_visible      TINYINT(1)   NOT NULL DEFAULT 1,
    last_updated_by VARCHAR(100) NULL,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_section_lang (section_key, lang),
    INDEX idx_fpc_visible (is_visible),
    INDEX idx_fpc_order   (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 5. Seed default page sections (EN + AR) ──────────────────
INSERT IGNORE INTO front_page_content (section_key, lang, sort_order, is_visible)
VALUES
  ('hero',                'en', 10, 1), ('hero',                'ar', 10, 1),
  ('about-us',            'en', 20, 1), ('about-us',            'ar', 20, 1),
  ('executive-education', 'en', 30, 1), ('executive-education', 'ar', 30, 1),
  ('partners-clients',    'en', 40, 1), ('partners-clients',    'ar', 40, 1),
  ('events',              'en', 50, 1), ('events',              'ar', 50, 1),
  ('services',            'en', 60, 1), ('services',            'ar', 60, 1),
  ('newsroom',            'en', 70, 1), ('newsroom',            'ar', 70, 1),
  ('alumni-hero',         'en', 80, 1), ('alumni-hero',         'ar', 80, 1),
  ('careers',             'en', 90, 1), ('careers',             'ar', 90, 1);
