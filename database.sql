-- =============================================================================
-- COLLEGE EVENTS HUB
-- COMPLETE DATABASE SCHEMA
-- MySQL 8.0+
-- =============================================================================

-- =============================================================================
-- 0. DATABASE
-- =============================================================================

CREATE DATABASE IF NOT EXISTS college_events_hub
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE college_events_hub;


-- =============================================================================
-- 1. CORE REFERENCE TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- CATEGORIES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS categories (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_categories_name (name)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- SUB EVENTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sub_events (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    category_id INT UNSIGNED NOT NULL,
    name VARCHAR(150) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_sub_event_category_name (category_id, name),
    KEY idx_sub_events_category (category_id),

    CONSTRAINT fk_sub_events_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 2. USER MANAGEMENT
-- =============================================================================

-- -----------------------------------------------------------------------------
-- STAFF
-- Admin and Coordinator accounts
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS staff (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(120) NOT NULL,

    email VARCHAR(150) NOT NULL,

    password_hash VARCHAR(255) NOT NULL,

    role ENUM(
        'admin',
        'coordinator'
    ) NOT NULL,

    active TINYINT(1) NOT NULL DEFAULT 1,

    phone VARCHAR(20) NULL,

    department VARCHAR(100) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    last_login TIMESTAMP NULL DEFAULT NULL,

    UNIQUE KEY uq_staff_email (email),

    KEY idx_staff_role (role),

    KEY idx_staff_active (active)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- STUDENTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS students (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(120) NOT NULL,

    mobile VARCHAR(20) NOT NULL,

    email VARCHAR(150) NOT NULL,

    register_number VARCHAR(60) NOT NULL,

    college_name VARCHAR(180) NULL,

    department VARCHAR(120) NULL,

    course VARCHAR(120) NULL,

    year_semester VARCHAR(60) NULL,

    password_hash VARCHAR(255) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    last_login TIMESTAMP NULL DEFAULT NULL,

    is_verified TINYINT(1) NOT NULL DEFAULT 0,

    UNIQUE KEY uq_students_mobile (mobile),

    UNIQUE KEY uq_students_email (email),

    UNIQUE KEY uq_students_register_number (register_number)

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 3. EVENTS MANAGEMENT
-- =============================================================================

-- -----------------------------------------------------------------------------
-- EVENTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS events (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    category_id INT UNSIGNED NOT NULL,

    sub_event_id INT UNSIGNED NULL,

    coordinator_id INT UNSIGNED NULL,

    event_name VARCHAR(220) NOT NULL,

    description TEXT NULL,

    event_date DATE NOT NULL,

    event_time TIME NULL,

    registration_deadline DATE NULL,

    venue VARCHAR(220) NULL,

    registration_fee DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    banner VARCHAR(255) NULL,

    image VARCHAR(255) NULL,

    qr_image VARCHAR(255) NULL,

    max_capacity INT UNSIGNED NOT NULL DEFAULT 100,

    current_registrations INT UNSIGNED NOT NULL DEFAULT 0,

    status ENUM(
        'Draft',
        'Published',
        'Closed',
        'Cancelled'
    ) NOT NULL DEFAULT 'Draft',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    KEY idx_events_category (category_id),

    KEY idx_events_sub_event (sub_event_id),

    KEY idx_events_coordinator (coordinator_id),

    KEY idx_events_status (status),

    KEY idx_events_date (event_date),

    CONSTRAINT fk_events_category
        FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_events_sub_event
        FOREIGN KEY (sub_event_id)
        REFERENCES sub_events(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,

    CONSTRAINT fk_events_coordinator
        FOREIGN KEY (coordinator_id)
        REFERENCES staff(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- HOMEPAGE
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS homepage (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    hero_small VARCHAR(255) NULL,

    hero_title VARCHAR(255) NULL,

    hero_description TEXT NULL,

    hero_button_text VARCHAR(100) NULL,

    hero_button_link VARCHAR(255) NULL,

    featured_image VARCHAR(255) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- EVENT RULES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS event_rules (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    event_id INT UNSIGNED NOT NULL,

    rule_text TEXT NOT NULL,

    rule_order INT NOT NULL DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    KEY idx_event_rules_event (event_id),

    CONSTRAINT fk_event_rules_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- SPEAKERS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS speakers (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    event_id INT UNSIGNED NOT NULL,

    name VARCHAR(150) NOT NULL,

    designation VARCHAR(180) NULL,

    bio TEXT NULL,

    photo VARCHAR(255) NULL,

    email VARCHAR(150) NULL,

    phone VARCHAR(20) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    KEY idx_speakers_event (event_id),

    CONSTRAINT fk_speakers_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- SCHEDULES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schedules (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    event_id INT UNSIGNED NOT NULL,

    start_time TIME NOT NULL,

    end_time TIME NULL,

    title VARCHAR(180) NOT NULL,

    description TEXT NULL,

    order_index INT NOT NULL DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    KEY idx_schedules_event (event_id),

    KEY idx_schedules_order (event_id, order_index),

    CONSTRAINT fk_schedules_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- PRIZES
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS prizes (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    event_id INT UNSIGNED NOT NULL,

    title VARCHAR(150) NOT NULL,

    description TEXT NULL,

    prize_amount DECIMAL(10,2) NULL,

    position INT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    KEY idx_prizes_event (event_id),

    CONSTRAINT fk_prizes_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 4. EVENT CONTENT
-- =============================================================================

-- -----------------------------------------------------------------------------
-- EVENT PHOTOS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS event_photos (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    event_id INT UNSIGNED NOT NULL,

    photo_path VARCHAR(255) NOT NULL,

    photo_caption VARCHAR(255) NULL,

    uploaded_by INT UNSIGNED NULL,

    photo_order INT NOT NULL DEFAULT 0,

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    KEY idx_event_photos_event (event_id),

    KEY idx_event_photos_staff (uploaded_by),

    CONSTRAINT fk_event_photos_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_event_photos_staff
        FOREIGN KEY (uploaded_by)
        REFERENCES staff(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- EVENT CAPACITY
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS event_capacity (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    event_id INT UNSIGNED NOT NULL,

    max_capacity INT UNSIGNED NOT NULL DEFAULT 100,

    current_registrations INT UNSIGNED NOT NULL DEFAULT 0,

    waiting_list_count INT UNSIGNED NOT NULL DEFAULT 0,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_event_capacity_event (event_id),

    CONSTRAINT fk_event_capacity_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 5. REGISTRATION
-- =============================================================================

-- -----------------------------------------------------------------------------
-- REGISTRATIONS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS registrations (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    student_id INT UNSIGNED NOT NULL,

    event_id INT UNSIGNED NOT NULL,

    status ENUM(
        'Pending',
        'Confirmed',
        'Cancelled',
        'Attended',
        'No-Show'
    ) NOT NULL DEFAULT 'Pending',

    registration_number VARCHAR(100) NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_registration_number (registration_number),

    UNIQUE KEY uq_student_event (student_id, event_id),

    KEY idx_registrations_student (student_id),

    KEY idx_registrations_event (event_id),

    KEY idx_registrations_status (status),

    KEY idx_registrations_created (created_at),

    CONSTRAINT fk_registrations_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_registrations_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 6. PAYMENTS
-- =============================================================================

CREATE TABLE IF NOT EXISTS payments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    registration_id INT UNSIGNED NOT NULL,

    amount DECIMAL(10,2) NOT NULL,

    utr VARCHAR(120) NULL,

    upi_id VARCHAR(120) NULL,

    receipt_path VARCHAR(255) NULL,

    payment_method ENUM(
        'upi',
        'card',
        'razorpay',
        'bank_transfer',
        'cash'
    ) NOT NULL DEFAULT 'upi',

    razorpay_order_id VARCHAR(255) NULL,

    razorpay_payment_id VARCHAR(255) NULL,

    razorpay_signature VARCHAR(255) NULL,

    status ENUM(
        'Pending',
        'Submitted',
        'Verified',
        'Rejected',
        'Refunded'
    ) NOT NULL DEFAULT 'Pending',

    notes TEXT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    verified_by INT UNSIGNED NULL,

    verified_at TIMESTAMP NULL DEFAULT NULL,

    UNIQUE KEY uq_payment_registration (registration_id),

    KEY idx_payments_status (status),

    KEY idx_payments_method (payment_method),

    KEY idx_payments_created (created_at),

    KEY idx_payments_verified_by (verified_by),

    CONSTRAINT fk_payments_registration
        FOREIGN KEY (registration_id)
        REFERENCES registrations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_payments_verified_by
        FOREIGN KEY (verified_by)
        REFERENCES staff(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 7. ATTENDANCE
-- =============================================================================

CREATE TABLE IF NOT EXISTS attendance (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    registration_id INT UNSIGNED NOT NULL,

    attended TINYINT(1) NOT NULL DEFAULT 0,

    check_in_time TIMESTAMP NULL DEFAULT NULL,

    check_out_time TIMESTAMP NULL DEFAULT NULL,

    marked_by INT UNSIGNED NULL,

    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_attendance_registration (registration_id),

    KEY idx_attendance_marked_by (marked_by),

    KEY idx_attendance_marked_at (marked_at),

    CONSTRAINT fk_attendance_registration
        FOREIGN KEY (registration_id)
        REFERENCES registrations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_attendance_staff
        FOREIGN KEY (marked_by)
        REFERENCES staff(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 8. CERTIFICATES
-- =============================================================================

CREATE TABLE IF NOT EXISTS certificates (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    registration_id INT UNSIGNED NOT NULL,

    certificate_number VARCHAR(100) NOT NULL,

    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    file_path VARCHAR(255) NULL,

    certificate_code VARCHAR(100) NULL,

    verified TINYINT(1) NOT NULL DEFAULT 0,

    UNIQUE KEY uq_certificate_registration (registration_id),

    UNIQUE KEY uq_certificate_number (certificate_number),

    KEY idx_certificate_code (certificate_code),

    CONSTRAINT fk_certificates_registration
        FOREIGN KEY (registration_id)
        REFERENCES registrations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 9. STUDENT ENGAGEMENT
-- =============================================================================

-- -----------------------------------------------------------------------------
-- WISHLIST
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS wishlist (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    student_id INT UNSIGNED NOT NULL,

    event_id INT UNSIGNED NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_wishlist_student_event (student_id, event_id),

    KEY idx_wishlist_student (student_id),

    KEY idx_wishlist_event (event_id),

    CONSTRAINT fk_wishlist_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_wishlist_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- EVENT RATINGS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS event_ratings (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    registration_id INT UNSIGNED NOT NULL,

    rating TINYINT UNSIGNED NOT NULL,

    review TEXT NULL,

    helpful_count INT UNSIGNED NOT NULL DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_event_rating_registration (registration_id),

    KEY idx_event_ratings_rating (rating),

    CONSTRAINT fk_event_ratings_registration
        FOREIGN KEY (registration_id)
        REFERENCES registrations(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- WAITING LIST
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS waiting_list (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    student_id INT UNSIGNED NOT NULL,

    event_id INT UNSIGNED NOT NULL,

    position INT UNSIGNED NULL,

    status ENUM(
        'Waiting',
        'Offered',
        'Accepted',
        'Rejected',
        'Expired'
    ) NOT NULL DEFAULT 'Waiting',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_waiting_student_event (student_id, event_id),

    KEY idx_waiting_event_status (event_id, status),

    CONSTRAINT fk_waiting_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_waiting_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- -----------------------------------------------------------------------------
-- STUDENT POINTS
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS student_points (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    student_id INT UNSIGNED NOT NULL,

    points INT UNSIGNED NOT NULL DEFAULT 0,

    total_events INT UNSIGNED NOT NULL DEFAULT 0,

    attended_events INT UNSIGNED NOT NULL DEFAULT 0,

    `rank` INT UNSIGNED NULL,

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_student_points_student (student_id),

    KEY idx_student_points_points (points),

    KEY idx_student_points_rank (`rank`),

    CONSTRAINT fk_student_points_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 10. NOTIFICATIONS
-- =============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    student_id INT UNSIGNED NOT NULL,

    event_id INT UNSIGNED NULL,

    title VARCHAR(255) NOT NULL,

    message TEXT NOT NULL,

    type ENUM(
        'reminder',
        'update',
        'feedback',
        'announcement',
        'registration'
    ) NOT NULL DEFAULT 'reminder',

    read_status TINYINT(1) NOT NULL DEFAULT 0,

    notification_date DATETIME NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    KEY idx_notifications_student (student_id),

    KEY idx_notifications_event (event_id),

    KEY idx_notifications_read (read_status),

    KEY idx_notifications_type (type),

    KEY idx_notifications_created (created_at),

    CONSTRAINT fk_notifications_student
        FOREIGN KEY (student_id)
        REFERENCES students(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT fk_notifications_event
        FOREIGN KEY (event_id)
        REFERENCES events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;


-- =============================================================================
-- 11. SAMPLE CATEGORIES
-- =============================================================================

INSERT IGNORE INTO categories
(name, description)
VALUES
(
    'Seminar',
    'Educational seminars and talks'
),
(
    'Inter-College Meet',
    'Competitions and meets between colleges'
),
(
    'Webinar',
    'Online educational sessions'
),
(
    'National Level Conference',
    'National level academic conferences'
),
(
    'Workshop',
    'Hands-on workshops and training'
);


-- =============================================================================
-- 12. SAMPLE SUB EVENTS
-- =============================================================================

INSERT IGNORE INTO sub_events
(category_id, name, description)

SELECT
    id,
    'Quiz',
    'General knowledge and subject-based quizzes'
FROM categories
WHERE name = 'Inter-College Meet'

UNION ALL

SELECT
    id,
    'Debugging',
    'Code debugging and troubleshooting competition'
FROM categories
WHERE name = 'Inter-College Meet'

UNION ALL

SELECT
    id,
    'Coding Contest',
    'Programming competition'
FROM categories
WHERE name = 'Inter-College Meet'

UNION ALL

SELECT
    id,
    'Gaming',
    'E-sports and gaming tournament'
FROM categories
WHERE name = 'Inter-College Meet';


-- =============================================================================
-- 13. SAMPLE STAFF
-- =============================================================================
--
-- IMPORTANT:
-- These are DEMO password hashes only.
-- For real login, create the staff account using your Flask
-- create_staff.py script so Werkzeug generates a valid password hash.
--

INSERT IGNORE INTO staff
(
    full_name,
    email,
    password_hash,
    role,
    active,
    phone,
    department
)
VALUES
(
    'Admin User',
    'admin@collegeeventshub.com',
    'scrypt:32768:8:1$test$test',
    'admin',
    1,
    '9999999999',
    'Administration'
),
(
    'Event Coordinator',
    'coordinator@collegeeventshub.com',
    'scrypt:32768:8:1$test$test',
    'coordinator',
    1,
    '8888888888',
    'Events'
);


-- =============================================================================
-- 14. HOMEPAGE DEFAULT CONTENT
-- =============================================================================

INSERT INTO homepage
(
    hero_small,
    hero_title,
    hero_description,
    hero_button_text,
    hero_button_link
)
SELECT
    'Welcome to',
    'College Events Hub',
    'Discover and register for amazing events happening in your college',
    'Explore Events',
    '/events'
WHERE NOT EXISTS (
    SELECT 1 FROM homepage
);


-- =============================================================================
-- 15. VERIFY DATABASE
-- =============================================================================

SELECT 'College Events Hub database created successfully!' AS message;

SHOW TABLES;


-- =============================================================================
-- 16. VERIFY IMPORTANT TABLES
-- =============================================================================

SELECT
    TABLE_NAME,
    ENGINE,
    TABLE_COLLATION
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'college_events_hub'
ORDER BY TABLE_NAME;


-- =============================================================================
-- END OF DATABASE
-- =============================================================================