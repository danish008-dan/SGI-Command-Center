-- =============================================================================
-- SGI COMMAND CENTER ERP DATABASE
-- Comprehensive MySQL schema, reference data, and repeat-safe compatibility updates
-- =============================================================================
-- Recommended: MySQL 8.0+ or a compatible MariaDB release.
-- Run this script using an account with CREATE/ALTER/INDEX privileges.
-- CREATE TABLE IF NOT EXISTS preserves existing tables; guarded updates below
-- add selected missing columns/indexes when upgrading an older SGI database.
-- This script does not drop tables or delete existing records.
-- =============================================================================

-- ==========================================================
-- SGI Command Center - Comprehensive Database Schema
-- ==========================================================
-- ARCHITECTURE OVERVIEW:
-- This database is the backbone of the SGI Command Center ERP.
-- It is built around a central 'users' table for authentication, linking to role-specific profiles ('students', 'teachers', 'employees').
-- The schema is divided into logical modules: Academic (Attendance, Marks, Subjects), Finance (Fees, Payroll),
-- Campus Operations (Hostel, Transport, Library), and Document Management.
-- Role-Based Access Control (RBAC) is handled via 'permissions' and 'role_permissions' tables.
-- Historical data and audit trails are maintained using append-only tables (e.g., 'audit_logs', 'complaint_history', 'result_history').
-- ==========================================================

CREATE DATABASE IF NOT EXISTS sgi_command_center;
USE sgi_command_center;

-- 1. Departments Table
-- Stores academic department information and its Head of Department (HOD).
CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL,
    department_code VARCHAR(20) UNIQUE,
    short_name VARCHAR(20),
    description TEXT,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    hod_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. Users Table
-- Central login table for all roles (Student, Teacher, HOD, Principal, Admin, Staff).
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mobile VARCHAR(15),
    password VARCHAR(255) NOT NULL,
    role ENUM('Student', 'Teacher', 'HOD', 'Principal', 'Admin', 'Staff') NOT NULL,
    department_id INT,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    session_version INT NOT NULL DEFAULT 0,
    password_reset_token VARCHAR(255) NULL,
    reset_token_expiry DATETIME NULL,
    force_password_change BOOLEAN DEFAULT FALSE,
    profile_image VARCHAR(255) DEFAULT 'default.png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 3. Students Table
-- Stores student-specific academic information linked to a user account.
CREATE TABLE IF NOT EXISTS students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    enrollment_no VARCHAR(30) UNIQUE,
    semester INT,
    section VARCHAR(10),
    cgpa DECIMAL(3,2),
    skills TEXT,
    interests TEXT,
    preferred_domain VARCHAR(100),
    dream_salary DECIMAL(10,2),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- 4. Teachers Table
-- Stores faculty-specific professional information linked to a user account.
CREATE TABLE IF NOT EXISTS teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    designation VARCHAR(100),
    qualification VARCHAR(100),
    experience INT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- 5. Employees Table
-- Stores non-teaching staff information linked to a user account.
CREATE TABLE IF NOT EXISTS employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    employee_code VARCHAR(20) NOT NULL UNIQUE,
    department_id INT NULL,
    designation VARCHAR(100) NOT NULL,
    employment_type ENUM('Permanent', 'Contractual', 'Temporary', 'Probationary') DEFAULT 'Probationary',
    joining_date DATE NOT NULL,
    bank_account_number VARCHAR(50) NULL,
    bank_ifsc VARCHAR(20) NULL,
    status ENUM('Active', 'Resigned', 'Retired', 'Terminated') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 6. Subjects Table
-- Stores subject details, including credits, type, and assigned teacher.
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(100),
    subject_code VARCHAR(20) UNIQUE,
    semester INT,
    department_id INT,
    teacher_id INT,
    credits INT DEFAULT 4,
    subject_type ENUM('Theory', 'Practical', 'Lab') DEFAULT 'Theory',
    classes_per_week INT DEFAULT 4,
    section VARCHAR(10) NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    FOREIGN KEY(department_id) REFERENCES departments(department_id),
    FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id)
);

-- 7. Attendance Table
-- Records daily attendance for students, linked to subject and teacher.
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('Present', 'Absent') NOT NULL DEFAULT 'Present',
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_attendance (student_id, subject_id, attendance_date),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

-- 8. Marks Table
-- Stores student marks for various exam types, with a workflow status for verification.
CREATE TABLE IF NOT EXISTS marks (
    marks_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    exam_type ENUM('Assignment', 'Quiz', 'Mid-1', 'Mid-2', 'Practical', 'Internal', 'Final') NOT NULL,
    maximum_marks INT NOT NULL,
    obtained_marks DECIMAL(5,2) NOT NULL,
    submission_status ENUM('Draft', 'Submitted', 'Verified', 'Returned') DEFAULT 'Draft',
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_marks (student_id, subject_id, exam_type),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

-- 9. Results Table
-- Stores calculated semester results, including SGPA/CGPA and approval workflow status.
CREATE TABLE IF NOT EXISTS results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester INT NOT NULL,
    total_marks DECIMAL(8,2) NOT NULL,
    obtained_marks DECIMAL(8,2) NOT NULL,
    percentage DECIMAL(5,2) NOT NULL,
    sgpa DECIMAL(4,2),
    cgpa DECIMAL(4,2),
    grade VARCHAR(5),
    status ENUM('Draft', 'Published') DEFAULT 'Draft',
    approval_status ENUM('Draft', 'Pending Principal', 'Approved', 'Rejected') DEFAULT 'Draft',
    approval_remarks TEXT NULL,
    published_at DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    UNIQUE KEY unique_result(student_id, semester)
);

-- 10. Notices Table
-- Stores institutional notices with category routing and approval workflow.
CREATE TABLE IF NOT EXISTS notices (
    notice_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    category VARCHAR(50) DEFAULT 'General',
    status ENUM('Draft', 'Pending', 'Approved', 'Published', 'Expired', 'Cancelled') DEFAULT 'Published',
    target_audience ENUM('All', 'Students', 'Teachers', 'Department') DEFAULT 'All',
    target_department_id INT NULL,
    publish_at DATETIME NULL,
    expire_at DATETIME NULL,
    approved_by INT NULL,
    approval_remarks TEXT NULL,
    attachment_path VARCHAR(255) NULL,
    description TEXT,
    posted_by INT,
    posted_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(target_department_id) REFERENCES departments(department_id),
    FOREIGN KEY(approved_by) REFERENCES users(user_id),
    FOREIGN KEY(posted_by) REFERENCES users(user_id)
);

-- 11. Events Table
-- Stores campus events with audience targeting and publication status.
CREATE TABLE IF NOT EXISTS events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    event_name VARCHAR(150),
    description TEXT,
    event_date DATE,
    venue VARCHAR(100),
    status ENUM('Draft', 'Pending', 'Approved', 'Published', 'Cancelled') DEFAULT 'Published',
    target_audience ENUM('All', 'Students', 'Teachers', 'Department') DEFAULT 'All',
    target_department_id INT NULL,
    organizer VARCHAR(100) NULL
);

-- 12. Complaints Table
-- Stores student complaints with routing, SLA tracking, and escalation support.
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    category VARCHAR(100),
    priority VARCHAR(50) DEFAULT 'Normal',
    sensitivity ENUM('Normal', 'Sensitive') DEFAULT 'Normal',
    complaint TEXT,
    status ENUM('Pending', 'Assigned', 'In Progress', 'Awaiting Student', 'Escalated', 'Resolved', 'Closed', 'Reopened') DEFAULT 'Pending',
    assigned_to INT NULL,
    escalated_from INT NULL,
    escalation_reason TEXT NULL,
    sla_due_at DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(assigned_to) REFERENCES users(user_id),
    FOREIGN KEY(escalated_from) REFERENCES users(user_id)
);

-- 13. Assignments Table
-- Stores teacher-created assignments linked to specific subjects.
CREATE TABLE IF NOT EXISTS assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT,
    teacher_id INT,
    title VARCHAR(200),
    description TEXT,
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(subject_id) REFERENCES subjects(subject_id),
    FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id)
);

-- 14. Assignment Submissions Table
-- Stores student submissions for assignments, including marks and file paths.
CREATE TABLE IF NOT EXISTS assignment_submissions (
    submission_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT,
    student_id INT,
    file_path VARCHAR(255),
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    marks DECIMAL(5,2),
    remarks VARCHAR(255),
    FOREIGN KEY(assignment_id) REFERENCES assignments(assignment_id),
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);

-- 15. Companies Table
-- Stores placement company information and eligibility criteria.
CREATE TABLE IF NOT EXISTS companies (
    company_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(150),
    location VARCHAR(100),
    package DECIMAL(10,2),
    eligibility_cgpa DECIMAL(3,2),
    required_skills TEXT,
    website VARCHAR(255)
);

-- 16. Placement Applications Table
-- Tracks student applications for placement drives.
CREATE TABLE IF NOT EXISTS placement_applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    company_id INT,
    status ENUM('Applied', 'Shortlisted', 'Interview', 'Selected', 'Rejected') DEFAULT 'Applied',
    applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(company_id) REFERENCES companies(company_id)
);

-- 17. AI Career Recommendations Table
-- Stores AI-generated career roadmaps for students.
CREATE TABLE IF NOT EXISTS career_recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    recommended_career VARCHAR(150),
    recommended_courses TEXT,
    required_skills TEXT,
    suggested_companies TEXT,
    full_response TEXT,
    generated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);

-- 18. Resume Analysis Table
-- Stores AI-generated resume analysis results for students.
CREATE TABLE IF NOT EXISTS resume_analysis (
    analysis_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    resume_file VARCHAR(255),
    ats_score INT,
    missing_skills TEXT,
    improvements TEXT,
    recommended_companies TEXT,
    full_response TEXT,
    analyzed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id)
);

-- 19. Leave Requests Table
-- Stores teacher leave applications and their approval status.
CREATE TABLE IF NOT EXISTS leave_requests (
    leave_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT,
    leave_type VARCHAR(100),
    from_date DATE,
    to_date DATE,
    reason TEXT,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id)
);

-- 20. Feedback Table
-- Stores student feedback for teachers.
CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT,
    teacher_id INT,
    rating INT,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(teacher_id) REFERENCES teachers(teacher_id)
);

-- 21. Login History Table
-- Records user login attempts, including IP and device info.
CREATE TABLE IF NOT EXISTS login_history (
    login_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(50),
    device VARCHAR(100),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- 22. Audit Logs Table
-- General system audit trail for user actions.
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(255),
    target_table VARCHAR(50) NULL,
    target_id INT NULL,
    old_state LONGTEXT NULL,
    new_state LONGTEXT NULL,
    source_interface ENUM('Manual UI', 'AI Agent', 'System') DEFAULT 'Manual UI',
    ai_tool_name VARCHAR(100) NULL,
    ip_address VARCHAR(50) NULL,
    log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- 23. Rooms Table
-- Stores physical rooms used for classes, labs, and scheduling.
CREATE TABLE IF NOT EXISTS rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(30) NOT NULL UNIQUE,
    room_name VARCHAR(100),
    room_type ENUM('Classroom', 'Lab', 'Seminar Hall') NOT NULL,
    capacity INT NOT NULL,
    building VARCHAR(100),
    floor INT,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 24. Time Slots Table
-- Defines time periods used in the weekly timetable.
CREATE TABLE IF NOT EXISTS time_slots (
    slot_id INT AUTO_INCREMENT PRIMARY KEY,
    slot_name VARCHAR(30),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_break BOOLEAN DEFAULT FALSE,
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- 25. Timetable Table
-- Stores generated or manual timetable entries with conflict checking.
CREATE TABLE IF NOT EXISTS timetable (
    timetable_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    semester INT NOT NULL,
    section VARCHAR(10) NOT NULL,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    room_id INT NOT NULL,
    slot_id INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday') NOT NULL,
    academic_year VARCHAR(20) DEFAULT '2024-2025',
    status ENUM('Draft', 'Pending Approval', 'Approved', 'Published', 'Rejected') DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (slot_id) REFERENCES time_slots(slot_id)
);

-- 26. Teacher Availability Table
-- Stores teacher availability for timetable generation.
CREATE TABLE IF NOT EXISTS teacher_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'),
    slot_id INT,
    available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (slot_id) REFERENCES time_slots(slot_id)
);

-- 27. Fee Structure Table
-- Defines fee components and total fees for departments and semesters.
CREATE TABLE IF NOT EXISTS fee_structure (
    fee_structure_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    course VARCHAR(100),
    semester INT,
    admission_fee DECIMAL(10,2) DEFAULT 0,
    tuition_fee DECIMAL(10,2) DEFAULT 0,
    examination_fee DECIMAL(10,2) DEFAULT 0,
    lab_fee DECIMAL(10,2) DEFAULT 0,
    library_fee DECIMAL(10,2) DEFAULT 0,
    other_fee DECIMAL(10,2) DEFAULT 0,
    total_fee DECIMAL(10,2) NOT NULL,
    academic_year VARCHAR(20) DEFAULT '2024-2025',
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 28. Student Fees Table
-- Assigns fee structures to students, tracking payable amounts and status.
CREATE TABLE IF NOT EXISTS student_fees (
    student_fee_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    fee_structure_id INT NOT NULL,
    total_fee DECIMAL(10,2),
    discount DECIMAL(10,2) DEFAULT 0,
    scholarship DECIMAL(10,2) DEFAULT 0,
    payable_fee DECIMAL(10,2),
    due_date DATE,
    status ENUM('Pending', 'Partial', 'Paid') DEFAULT 'Pending',
    FOREIGN KEY(student_id) REFERENCES students(student_id),
    FOREIGN KEY(fee_structure_id) REFERENCES fee_structure(fee_structure_id)
);

-- 29. Fee Payments Table
-- Records actual fee payments, including mode and transaction details.
CREATE TABLE IF NOT EXISTS fee_payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_fee_id INT NOT NULL,
    receipt_number VARCHAR(50) UNIQUE,
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    payment_mode ENUM('Cash', 'UPI', 'Card', 'Bank Transfer', 'Cheque'),
    amount_paid DECIMAL(10,2),
    transaction_id VARCHAR(100),
    remarks VARCHAR(255),
    collected_by INT,
    FOREIGN KEY(student_fee_id) REFERENCES student_fees(student_fee_id),
    FOREIGN KEY(collected_by) REFERENCES users(user_id)
);

-- 30. Payment Transactions Table
-- Tracks online/simulated payment gateway transactions.
CREATE TABLE IF NOT EXISTS payment_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_reference VARCHAR(100) UNIQUE,
    student_fee_id INT NOT NULL,
    gateway VARCHAR(50) DEFAULT 'Simulated Gateway',
    payment_mode VARCHAR(50),
    gateway_transaction_id VARCHAR(200),
    amount DECIMAL(10,2),
    payment_status ENUM('Pending', 'Success', 'Failed', 'Refunded') DEFAULT 'Pending',
    gateway_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(student_fee_id) REFERENCES student_fees(student_fee_id)
);

-- 31. Payment Audit Table
-- Audit trail specific to payment gateway transactions.
CREATE TABLE IF NOT EXISTS payment_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT,
    action VARCHAR(100),
    performed_by INT,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    remarks TEXT,
    FOREIGN KEY(transaction_id) REFERENCES payment_transactions(transaction_id)
);

-- 32. Refunds Table
-- Records internal fee refunds and reversals.
CREATE TABLE IF NOT EXISTS refunds (
    refund_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_id INT NOT NULL,
    student_fee_id INT NOT NULL,
    refund_amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    processed_by INT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payment_id) REFERENCES fee_payments(payment_id),
    FOREIGN KEY (student_fee_id) REFERENCES student_fees(student_fee_id)
);

-- 33. Concession Requests Table
-- Tracks scholarship and concession approval workflows.
CREATE TABLE IF NOT EXISTS concession_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    student_fee_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    requested_by INT NULL,
    approved_by INT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    FOREIGN KEY (student_fee_id) REFERENCES student_fees(student_fee_id)
);

-- 34. Salary Components Table
-- Configurable earnings and deductions for payroll calculation.
CREATE TABLE IF NOT EXISTS salary_components (
    component_id INT AUTO_INCREMENT PRIMARY KEY,
    component_name VARCHAR(50) NOT NULL UNIQUE,
    component_type ENUM('Earning', 'Deduction', 'Employer_Contribution') NOT NULL,
    is_taxable BOOLEAN DEFAULT FALSE,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    calculation_type ENUM('Fixed Amount', 'Percentage of Basic', 'Pending Configuration') DEFAULT 'Pending Configuration',
    calculation_value DECIMAL(10,2) NULL
);

-- 35. Employee Salary Assignments Table
-- Effective-dated salary structure assignments for employees.
CREATE TABLE IF NOT EXISTS employee_salary_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    component_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    effective_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (component_id) REFERENCES salary_components(component_id)
);

-- 36. Salary Revisions Table
-- Tracks salary increment and revision approval workflows.
CREATE TABLE IF NOT EXISTS salary_revisions (
    revision_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    component_id INT NOT NULL,
    old_amount DECIMAL(10,2) NULL,
    new_amount DECIMAL(10,2) NOT NULL,
    effective_date DATE NOT NULL,
    reason VARCHAR(255) NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    requested_by INT NOT NULL,
    approved_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (component_id) REFERENCES salary_components(component_id),
    FOREIGN KEY (requested_by) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
);

-- 37. Payroll Periods Table
-- Defines monthly payroll processing periods.
CREATE TABLE IF NOT EXISTS payroll_periods (
    period_id INT AUTO_INCREMENT PRIMARY KEY,
    month INT NOT NULL,
    year INT NOT NULL,
    status ENUM('Open', 'Processing', 'Closed') DEFAULT 'Open',
    UNIQUE(month, year)
);

-- 38. Payroll Runs Table
-- Stores calculated payroll for each employee per period, with approval workflow.
CREATE TABLE IF NOT EXISTS payroll_runs (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    period_id INT NOT NULL,
    employee_id INT NOT NULL,
    gross_earnings DECIMAL(10,2) DEFAULT 0,
    total_deductions DECIMAL(10,2) DEFAULT 0,
    net_payable DECIMAL(10,2) DEFAULT 0,
    calendar_days INT NOT NULL DEFAULT 30,
    payable_days DECIMAL(5,2) NOT NULL DEFAULT 30.00,
    lwp_days DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    status ENUM('Draft', 'Calculated', 'Under Review', 'Approved', 'Finalized', 'Paid') DEFAULT 'Draft',
    payment_date DATE NULL,
    payment_reference VARCHAR(100) NULL,
    prepared_by INT NULL,
    approved_by INT NULL,
    UNIQUE(period_id, employee_id),
    FOREIGN KEY (period_id) REFERENCES payroll_periods(period_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- 39. Payslip Items Table
-- Snapshot of payroll line items for historical integrity.
CREATE TABLE IF NOT EXISTS payslip_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    component_name VARCHAR(50) NOT NULL,
    component_type ENUM('Earning', 'Deduction', 'Employer_Contribution') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (run_id) REFERENCES payroll_runs(run_id)
);

-- 40. Exit & Clearance Table
-- Tracks employee resignation/retirement and clearance workflows.
CREATE TABLE IF NOT EXISTS exit_clearances (
    clearance_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    exit_type ENUM('Resignation', 'Retirement', 'Termination') NOT NULL,
    last_working_day DATE NOT NULL,
    reason TEXT NULL,
    status ENUM('Pending', 'Cleared', 'Rejected') DEFAULT 'Pending',
    final_settlement_amount DECIMAL(10,2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- 41. Payroll Settings Table
-- Configurable proration and rounding rules for payroll calculation.
CREATE TABLE IF NOT EXISTS payroll_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,
    proration_method ENUM('ACTUAL_CALENDAR_DAYS_IN_MONTH', 'WORKING_DAYS', 'FIXED_30_DAYS') DEFAULT 'ACTUAL_CALENDAR_DAYS_IN_MONTH',
    rounding_rule ENUM('ROUND_TO_2_DECIMALS', 'ROUND_TO_NEAREST_RUPEE') DEFAULT 'ROUND_TO_2_DECIMALS',
    updated_by INT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 42. Asset Categories Table
-- Configurable categories for durable assets (e.g., IT, Furniture, Lab).
CREATE TABLE IF NOT EXISTS asset_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    prefix VARCHAR(10) NOT NULL UNIQUE,
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- 43. Assets Table
-- Durable asset registry with unique codes and lifecycle status.
CREATE TABLE IF NOT EXISTS assets (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_code VARCHAR(20) NOT NULL UNIQUE,
    category_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    serial_number VARCHAR(100) NULL,
    acquisition_date DATE NULL,
    acquisition_cost DECIMAL(10,2) NULL,
    supplier VARCHAR(100) NULL,
    condition_status ENUM('Good', 'Fair', 'Damaged', 'Under Repair') DEFAULT 'Good',
    lifecycle_status ENUM('Active', 'Allocated', 'In Storage', 'Disposed', 'Lost') DEFAULT 'Active',
    room_id INT NULL,
    department_id INT NULL,
    custodian_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES asset_categories(category_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (custodian_id) REFERENCES users(user_id)
);

-- 44. Asset Allocation History Table
-- Tracks allocation and transfer history of durable assets.
CREATE TABLE IF NOT EXISTS asset_allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    allocated_to_user INT NULL,
    allocated_to_dept INT NULL,
    allocated_to_room INT NULL,
    allocated_by INT NOT NULL,
    allocation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    return_date TIMESTAMP NULL,
    status ENUM('Active', 'Returned', 'Transferred') DEFAULT 'Active',
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (allocated_to_user) REFERENCES users(user_id),
    FOREIGN KEY (allocated_to_dept) REFERENCES departments(department_id),
    FOREIGN KEY (allocated_to_room) REFERENCES rooms(room_id),
    FOREIGN KEY (allocated_by) REFERENCES users(user_id)
);

-- 45. Inventory Items Table
-- Consumable stock catalogue with current balance and reorder levels.
CREATE TABLE IF NOT EXISTS inventory_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    current_stock DECIMAL(10,2) NOT NULL DEFAULT 0,
    reorder_level DECIMAL(10,2) NOT NULL DEFAULT 0,
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- 46. Stock Movement Ledger Table
-- Append-only ledger tracking all stock receipts, issues, and adjustments.
CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    movement_type ENUM('Receipt', 'Issue', 'Return', 'Transfer', 'Adjustment') NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    balance_after DECIMAL(10,2) NOT NULL,
    reason VARCHAR(255) NULL,
    performed_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
    FOREIGN KEY (performed_by) REFERENCES users(user_id)
);

-- 47. Stock Requests Table
-- Tracks consumable stock request and approval workflows.
CREATE TABLE IF NOT EXISTS stock_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    purpose TEXT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Issued') DEFAULT 'Pending',
    requested_by INT NOT NULL,
    approved_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
    FOREIGN KEY (requested_by) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
);

-- 48. Maintenance Requests Table
-- Tracks breakdown reporting and work order status for assets.
CREATE TABLE IF NOT EXISTS maintenance_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    issue_description TEXT NOT NULL,
    priority ENUM('Low', 'Medium', 'High') DEFAULT 'Medium',
    status ENUM('Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Submitted',
    resolution_notes TEXT NULL,
    requested_by INT NOT NULL,
    assigned_to INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (requested_by) REFERENCES users(user_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
);

-- 49. AMC & Warranty Contracts Table
-- Stores Annual Maintenance Contract details and expiry dates.
CREATE TABLE IF NOT EXISTS amc_contracts (
    contract_id INT AUTO_INCREMENT PRIMARY KEY,
    provider VARCHAR(100) NOT NULL,
    contract_reference VARCHAR(100) NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    cost DECIMAL(10,2) NULL,
    document_path VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 50. Asset-AMC Mapping Table
-- Many-to-Many relationship between assets and AMC contracts.
CREATE TABLE IF NOT EXISTS asset_amc_mapping (
    mapping_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    contract_id INT NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (contract_id) REFERENCES amc_contracts(contract_id)
);

-- 51. Asset Disposals Table
-- Tracks asset write-off and disposal approval workflows.
CREATE TABLE IF NOT EXISTS asset_disposals (
    disposal_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    reason TEXT NOT NULL,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    requested_by INT NOT NULL,
    approved_by INT NULL,
    disposal_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (requested_by) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
);

-- 52. Hostel Rooms Table
-- Stores hostel room configuration and capacity.
CREATE TABLE IF NOT EXISTS hostel_rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    hostel_name VARCHAR(50) NOT NULL,
    floor VARCHAR(10) NOT NULL,
    room_number VARCHAR(10) NOT NULL,
    capacity INT NOT NULL DEFAULT 1,
    room_type ENUM('AC', 'Non-AC', 'Deluxe') DEFAULT 'Non-AC',
    status ENUM('Active', 'Maintenance', 'Inactive') DEFAULT 'Active',
    UNIQUE(hostel_name, floor, room_number)
);

-- 53. Hostel Beds Table
-- Tracks individual bed availability and occupancy status.
CREATE TABLE IF NOT EXISTS hostel_beds (
    bed_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL,
    bed_number VARCHAR(10) NOT NULL,
    status ENUM('Available', 'Occupied', 'Maintenance') DEFAULT 'Available',
    UNIQUE(room_id, bed_number),
    FOREIGN KEY (room_id) REFERENCES hostel_rooms(room_id)
);

-- 54. Hostel Applications Table
-- Student applications for hostel accommodation.
CREATE TABLE IF NOT EXISTS hostel_applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    preferred_hostel VARCHAR(50) NULL,
    status ENUM('Pending', 'Approved', 'Rejected', 'Allocated') DEFAULT 'Pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INT NULL,
    review_notes TEXT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (reviewed_by) REFERENCES users(user_id)
);

-- 55. Hostel Allocations Table
-- Active bed allocations and check-in/check-out history.
CREATE TABLE IF NOT EXISTS hostel_allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    bed_id INT NOT NULL,
    check_in_date DATE NOT NULL,
    expected_check_out DATE NULL,
    actual_check_out DATE NULL,
    status ENUM('Active', 'Checked Out') DEFAULT 'Active',
    allocated_by INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (bed_id) REFERENCES hostel_beds(bed_id),
    FOREIGN KEY (allocated_by) REFERENCES users(user_id)
);

-- 56. Transport Routes Table
-- Defines transport routes and their operational status.
CREATE TABLE IF NOT EXISTS transport_routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL,
    start_point VARCHAR(100) NOT NULL,
    end_point VARCHAR(100) NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- 57. Transport Stops Table
-- Defines stops and their sequence for each transport route.
CREATE TABLE IF NOT EXISTS transport_stops (
    stop_id INT AUTO_INCREMENT PRIMARY KEY,
    route_id INT NOT NULL,
    stop_name VARCHAR(100) NOT NULL,
    sequence_order INT NOT NULL,
    pickup_time TIME NULL,
    FOREIGN KEY (route_id) REFERENCES transport_routes(route_id)
);

-- 58. Transport Vehicles Table
-- Links assets (buses) to transport routes and drivers.
CREATE TABLE IF NOT EXISTS transport_vehicles (
    transport_vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL UNIQUE,
    route_id INT NULL,
    driver_name VARCHAR(100) NULL,
    driver_contact VARCHAR(15) NULL,
    capacity INT NOT NULL,
    status ENUM('Active', 'Maintenance', 'Inactive') DEFAULT 'Active',
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id),
    FOREIGN KEY (route_id) REFERENCES transport_routes(route_id)
);

-- 59. Transport Allocations Table
-- Tracks student transport allocations and active status.
CREATE TABLE IF NOT EXISTS transport_allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    route_id INT NOT NULL,
    stop_id INT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    status ENUM('Active', 'Cancelled') DEFAULT 'Active',
    allocated_by INT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (route_id) REFERENCES transport_routes(route_id),
    FOREIGN KEY (stop_id) REFERENCES transport_stops(stop_id),
    FOREIGN KEY (allocated_by) REFERENCES users(user_id)
);

-- 60. Library Books Table
-- Bibliographic catalogue of library book titles.
CREATE TABLE IF NOT EXISTS library_books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) NULL,
    publisher VARCHAR(100) NULL,
    category VARCHAR(50) NULL,
    status ENUM('Active', 'Withdrawn') DEFAULT 'Active'
);

-- 61. Library Copies Table
-- Tracks physical book copies and their circulation status.
CREATE TABLE IF NOT EXISTS library_copies (
    copy_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    accession_number VARCHAR(20) NOT NULL UNIQUE,
    status ENUM('Available', 'Issued', 'Lost', 'Damaged', 'Withdrawn') DEFAULT 'Available',
    FOREIGN KEY (book_id) REFERENCES library_books(book_id)
);

-- 62. Library Loans Table
-- Tracks book issue, return, and overdue status.
CREATE TABLE IF NOT EXISTS library_loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    copy_id INT NOT NULL,
    user_id INT NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    return_date DATE NULL,
    status ENUM('Issued', 'Returned', 'Overdue') DEFAULT 'Issued',
    fine_amount DECIMAL(10,2) DEFAULT 0.00,
    issued_by INT NOT NULL,
    FOREIGN KEY (copy_id) REFERENCES library_copies(copy_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (issued_by) REFERENCES users(user_id)
);

-- 63. Visitors Table
-- Tracks visitor registration, approval, and gate check-in/out.
CREATE TABLE IF NOT EXISTS visitors (
    visitor_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    mobile VARCHAR(15) NOT NULL,
    host_user_id INT NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    visit_date DATE NOT NULL,
    approval_status ENUM('Pending', 'Approved', 'Rejected', 'Walk-in') DEFAULT 'Pending',
    check_in_time DATETIME NULL,
    check_out_time DATETIME NULL,
    status ENUM('Scheduled', 'Checked In', 'Checked Out', 'Cancelled') DEFAULT 'Scheduled',
    qr_reference VARCHAR(50) NULL UNIQUE,
    registered_by INT NOT NULL,
    FOREIGN KEY (host_user_id) REFERENCES users(user_id),
    FOREIGN KEY (registered_by) REFERENCES users(user_id)
);

-- 64. Document Categories Table
-- Configurable categories for institutional documents.
CREATE TABLE IF NOT EXISTS document_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    status ENUM('Active', 'Inactive') DEFAULT 'Active'
);

-- 65. Documents Table
-- Metadata for institutional documents with approval workflow.
CREATE TABLE IF NOT EXISTS documents (
    document_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    department_id INT NULL,
    reference_number VARCHAR(50) NULL,
    status ENUM('Draft', 'Pending Review', 'Approved', 'Published', 'Archived', 'Rejected') DEFAULT 'Draft',
    expiry_date DATE NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES document_categories(category_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- 66. Document Versions Table
-- Secure file storage references and version history for documents.
CREATE TABLE IF NOT EXISTS document_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    document_id INT NOT NULL,
    version_number INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    change_summary TEXT NULL,
    status ENUM('Draft', 'Pending', 'Approved', 'Rejected') DEFAULT 'Draft',
    uploaded_by INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id),
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
);

-- 67. Compliance Requirements Table
-- Tracks AICTE/University compliance requirements and submission status.
CREATE TABLE IF NOT EXISTS compliance_requirements (
    requirement_id INT AUTO_INCREMENT PRIMARY KEY,
    body_name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    academic_year VARCHAR(10) NULL,
    status ENUM('Not Started', 'In Progress', 'Under Review', 'Ready', 'Submitted', 'Verified', 'Not Applicable') DEFAULT 'Not Started',
    due_date DATE NULL,
    responsible_dept INT NULL,
    evidence_doc_id INT NULL,
    FOREIGN KEY (responsible_dept) REFERENCES departments(department_id),
    FOREIGN KEY (evidence_doc_id) REFERENCES documents(document_id)
);

-- 68. Meetings Table
-- Stores meeting schedules, agenda, and approved minutes.
CREATE TABLE IF NOT EXISTS meetings (
    meeting_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    meeting_type VARCHAR(50) NULL,
    department_id INT NULL,
    meeting_date DATE NOT NULL,
    venue VARCHAR(100) NULL,
    chairperson_id INT NOT NULL,
    organizer_id INT NOT NULL,
    agenda TEXT NULL,
    minutes TEXT NULL,
    status ENUM('Scheduled', 'Held', 'Minutes Draft', 'Approved', 'Archived') DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (chairperson_id) REFERENCES users(user_id),
    FOREIGN KEY (organizer_id) REFERENCES users(user_id)
);

-- 69. Meeting Attendees Table
-- Tracks invited and present attendees for meetings.
CREATE TABLE IF NOT EXISTS meeting_attendees (
    attendee_id INT AUTO_INCREMENT PRIMARY KEY,
    meeting_id INT NOT NULL,
    user_id INT NOT NULL,
    attendance_status ENUM('Invited', 'Present', 'Absent') DEFAULT 'Invited',
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 70. Action Items Table
-- Tracks tasks assigned during meetings and their completion status.
CREATE TABLE IF NOT EXISTS action_items (
    action_id INT AUTO_INCREMENT PRIMARY KEY,
    meeting_id INT NOT NULL,
    description TEXT NOT NULL,
    assigned_to INT NOT NULL,
    due_date DATE NULL,
    status ENUM('Open', 'In Progress', 'Completed', 'On Hold', 'Cancelled') DEFAULT 'Open',
    progress_notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meeting_id) REFERENCES meetings(meeting_id),
    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
);

-- 71. Complaint SLA Policies Table
-- Configurable SLA rules for complaint categories.
CREATE TABLE IF NOT EXISTS complaint_sla_policies (
    policy_id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    priority VARCHAR(50) NOT NULL DEFAULT 'Normal',
    sla_hours INT NOT NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_sla_policy (category, priority)
);

-- 72. Complaint History Table
-- Append-only audit trail for complaint status and assignment changes.
CREATE TABLE IF NOT EXISTS complaint_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    changed_by INT NOT NULL,
    old_status VARCHAR(50) NULL,
    new_status VARCHAR(50) NULL,
    old_assignee INT NULL,
    new_assignee INT NULL,
    action VARCHAR(100) NOT NULL,
    reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
    FOREIGN KEY (changed_by) REFERENCES users(user_id)
);

-- 73. Complaint Messages Table
-- Stores communication and internal notes for complaint cases.
CREATE TABLE IF NOT EXISTS complaint_messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_text TEXT NOT NULL,
    is_internal_note BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
    FOREIGN KEY (sender_id) REFERENCES users(user_id)
);

-- 74. Complaint Attachments Table
-- Metadata for files uploaded as evidence or communication in complaints.
CREATE TABLE IF NOT EXISTS complaint_attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    complaint_id INT NOT NULL,
    uploaded_by INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id)
);

-- 75. Permissions Table
-- Granular permission identifiers for RBAC.
CREATE TABLE IF NOT EXISTS permissions (
    permission_id INT AUTO_INCREMENT PRIMARY KEY,
    permission_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL
);

-- 76. Role-Permissions Mapping Table
-- Maps existing roles to permitted actions.
CREATE TABLE IF NOT EXISTS role_permissions (
    role_permission_id INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    permission_id INT NOT NULL,
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id),
    UNIQUE(role, permission_id)
);

-- 77. Academic Sessions Table
-- Configurable academic years/semesters for enrollment.
CREATE TABLE IF NOT EXISTS academic_sessions (
    academic_session_id INT AUTO_INCREMENT PRIMARY KEY,
    session_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 78. Student Enrollments History Table
-- Tracks student enrollment history (promotions/transfers) per session.
CREATE TABLE IF NOT EXISTS student_enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    academic_session_id INT NULL,
    department_id INT NOT NULL,
    semester INT NOT NULL,
    section VARCHAR(10) NULL,
    enrollment_status VARCHAR(30) NOT NULL DEFAULT 'Active',
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (academic_session_id) REFERENCES academic_sessions(academic_session_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 79. Teacher Service History Table
-- Tracks teacher designation and department transfer history.
CREATE TABLE IF NOT EXISTS teacher_service_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    department_id INT NOT NULL,
    designation VARCHAR(100) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    service_status VARCHAR(30) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- 80. Subject Assignments History Table
-- Tracks faculty assignment history for subjects.
CREATE TABLE IF NOT EXISTS subject_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    teacher_id INT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    assignment_status VARCHAR(30) NOT NULL DEFAULT 'Active',
    assigned_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
);

-- 81. Department HOD Assignments Table
-- Tracks HOD assignment history for departments.
CREATE TABLE IF NOT EXISTS department_hod_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    user_id INT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    status ENUM('Active', 'Inactive') DEFAULT 'Active',
    assigned_by INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(department_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 82. Revaluation Requests Table
-- Tracks student requests for exam paper rechecking.
CREATE TABLE IF NOT EXISTS revaluation_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester INT NOT NULL,
    subject_id INT NOT NULL,
    reason TEXT,
    status ENUM('Pending', 'Approved', 'Rejected', 'Completed') DEFAULT 'Pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- 83. Result History Table
-- Audit trail for changes to student results (e.g., revaluation updates).
CREATE TABLE IF NOT EXISTS result_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    semester INT NOT NULL,
    total_marks DECIMAL(8,2),
    obtained_marks DECIMAL(8,2),
    percentage DECIMAL(5,2),
    sgpa DECIMAL(4,2),
    cgpa DECIMAL(4,2),
    grade VARCHAR(5),
    changed_by INT NULL,
    change_reason VARCHAR(255),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 84. Security Audit Table
-- Extended audit trail for security-sensitive actions (e.g., role changes, password resets).
CREATE TABLE IF NOT EXISTS security_audit (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    actor_id INT NOT NULL,
    target_user_id INT NULL,
    action VARCHAR(100) NOT NULL,
    old_value VARCHAR(255) NULL,
    new_value VARCHAR(255) NULL,
    reason TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actor_id) REFERENCES users(user_id),
    FOREIGN KEY (target_user_id) REFERENCES users(user_id)
);


-- 85. Lesson Plans
CREATE TABLE IF NOT EXISTS lesson_plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    section VARCHAR(10) NOT NULL,
    plan_date DATE NOT NULL,
    topic VARCHAR(255) NOT NULL,
    learning_objective TEXT,
    teaching_method VARCHAR(100),
    duration_minutes INT,
    status ENUM('Planned', 'Completed', 'Postponed') DEFAULT 'Planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- 86. Syllabus Coverage
CREATE TABLE IF NOT EXISTS syllabus_coverage (
    coverage_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    section VARCHAR(10) NOT NULL,
    unit_name VARCHAR(255) NOT NULL,
    status ENUM('Not Started', 'In Progress', 'Completed') DEFAULT 'Not Started',
    coverage_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- 87. Question Bank
CREATE TABLE IF NOT EXISTS question_bank (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    topic VARCHAR(255),
    question_text TEXT NOT NULL,
    question_type ENUM('MCQ', 'Short Answer', 'Long Answer', 'Practical') DEFAULT 'Short Answer',
    difficulty ENUM('Easy', 'Medium', 'Hard') DEFAULT 'Medium',
    marks INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);


-- 88. Resume Analysis History
CREATE TABLE IF NOT EXISTS resume_analysis_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    resume_file_path VARCHAR(255) NOT NULL,
    analysis_json TEXT NOT NULL,
    jd_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

-- 89. Resume Builder Drafts
CREATE TABLE IF NOT EXISTS resume_drafts (
    draft_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(100) DEFAULT 'My Resume',
    content_json TEXT NOT NULL,
    template_id VARCHAR(50) DEFAULT 'clean_professional',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);


-- Attendance Summary View
-- Aggregated view of attendance percentage by student and subject.
-- Upgrade audit_logs safely when this script is run against an older database.
-- The columns are already present in newly created databases, so these checks become no-ops.
SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'target_table');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN target_table VARCHAR(50) NULL AFTER action',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'target_id');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN target_id INT NULL AFTER target_table',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'old_state');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN old_state LONGTEXT NULL AFTER target_id',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'new_state');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN new_state LONGTEXT NULL AFTER old_state',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'source_interface');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN source_interface ENUM(''Manual UI'', ''AI Agent'', ''System'') DEFAULT ''Manual UI'' AFTER new_state',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'ai_tool_name');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN ai_tool_name VARCHAR(100) NULL AFTER source_interface',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

SET @column_exists = (SELECT COUNT(*) FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = 'audit_logs' AND column_name = 'ip_address');
SET @migration_sql = IF(@column_exists = 0,
    'ALTER TABLE audit_logs ADD COLUMN ip_address VARCHAR(50) NULL AFTER ai_tool_name',
    'SELECT 1');
PREPARE migration_stmt FROM @migration_sql; EXECUTE migration_stmt; DEALLOCATE PREPARE migration_stmt;

CREATE OR REPLACE VIEW attendance_summary AS
SELECT
    a.student_id,
    s.subject_name,
    COUNT(a.attendance_id) AS total_classes,
    SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
    SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent,
    ROUND((SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) / COUNT(a.attendance_id))*100, 2) AS percentage
FROM attendance a
INNER JOIN subjects s ON a.subject_id = s.subject_id
GROUP BY a.student_id, s.subject_name;



-- ==========================================
-- DATA INSERTION (Defaults)
-- ==========================================

-- Insert Default Academic Session
INSERT INTO academic_sessions (session_name, start_date, end_date, status)
VALUES ('2024-25', '2024-07-01', '2025-06-30', 'Active')
ON DUPLICATE KEY UPDATE status='Active';

-- Insert Default Payroll Settings
INSERT INTO payroll_settings (setting_id, proration_method, rounding_rule) VALUES (1, 'ACTUAL_CALENDAR_DAYS_IN_MONTH', 'ROUND_TO_2_DECIMALS')
ON DUPLICATE KEY UPDATE setting_id=setting_id;

-- Insert Default Asset Categories
INSERT INTO asset_categories (category_name, prefix, status) VALUES
('IT Equipment', 'IT', 'Active'),
('Furniture', 'FUR', 'Active'),
('Laboratory Equipment', 'LAB', 'Active'),
('Electrical', 'ELE', 'Active')
ON DUPLICATE KEY UPDATE category_name=VALUES(category_name);

-- Insert Default Document Categories
INSERT INTO document_categories (category_name, status) VALUES
('Institutional Policies & Procedures', 'Active'),
('Affiliation & Accreditation', 'Active'),
('AICTE Documentation', 'Active'),
('Meeting Minutes (MoM)', 'Active'),
('HR & Employee Documents', 'Active'),
('MoUs & Agreements', 'Active'),
('Official Circulars & Notices', 'Active'),
('Inspection & Compliance Evidence', 'Active')
ON DUPLICATE KEY UPDATE category_name=VALUES(category_name);

-- Insert Default Salary Components
INSERT INTO salary_components (component_name, component_type, is_taxable, status, calculation_type, calculation_value) VALUES
('Basic Salary', 'Earning', 0, 'Active', 'Fixed Amount', 0),
('House Rent Allowance (HRA)', 'Earning', 0, 'Active', 'Fixed Amount', 0),
('Special Allowance', 'Earning', 1, 'Active', 'Fixed Amount', 0),
('Provident Fund (PF)', 'Deduction', 0, 'Inactive', 'Pending Configuration', NULL),
('Employee State Insurance (ESI)', 'Deduction', 0, 'Inactive', 'Pending Configuration', NULL),
('Professional Tax (PT)', 'Deduction', 0, 'Inactive', 'Pending Configuration', NULL),
('Tax Deducted at Source (TDS)', 'Deduction', 1, 'Inactive', 'Pending Configuration', NULL)
ON DUPLICATE KEY UPDATE component_name=VALUES(component_name);

-- Insert Default RBAC Permissions
INSERT INTO permissions (permission_name, description) VALUES
('user.view', 'View User Directory'),
('user.create', 'Create New Users'),
('user.update', 'Update User Profiles'),
('user.activate', 'Activate User Accounts'),
('user.deactivate', 'Deactivate User Accounts'),
('user.reset_password', 'Reset User Passwords'),
('user.assign_role', 'Assign Roles to Users'),
('user.manage_permissions', 'Manage RBAC Permissions'),
('user.view_audit', 'View Security Audit Logs'),
('reports.view', 'Access Reports Workspace'),
('reports.students.view', 'View Student Reports'),
('reports.faculty.view', 'View Faculty Reports'),
('reports.academics.view', 'View Academic Reports'),
('reports.finance.view', 'View Finance Reports'),
('reports.administration.view', 'View Administration Reports'),
('reports.audit.view', 'View Audit Reports'),
('reports.export_pdf', 'Export Reports to PDF'),
('reports.export_csv', 'Export Reports to CSV'),
('assets.view', 'View Asset Register'),
('assets.create', 'Create New Assets'),
('assets.update', 'Update Asset Details'),
('assets.allocate', 'Allocate and Transfer Assets'),
('assets.request_maintenance', 'Request Asset Maintenance'),
('assets.manage_maintenance', 'Manage Maintenance Work Orders'),
('assets.approve_disposal', 'Approve Asset Disposals'),
('inventory.view', 'View Inventory'),
('inventory.manage', 'Manage Stock and Movements'),
('inventory.approve', 'Approve Stock Requests'),
('hr.view', 'View Employee Directory'),
('hr.manage', 'Manage Employees and Salary'),
('payroll.view', 'View Payroll'),
('payroll.manage', 'Process Payroll'),
('payroll.approve', 'Approve Payroll'),
('payslip.view', 'View Payslips'),
('hr.exit.manage', 'Manage Exits and Clearance'),
('documents.view', 'View Institutional Documents'),
('documents.upload', 'Upload and Manage Documents'),
('documents.approve', 'Approve and Publish Documents'),
('compliance.view', 'View Compliance Register'),
('compliance.manage', 'Manage Compliance Requirements'),
('meetings.view', 'View Meetings'),
('meetings.manage', 'Create and Manage Meetings'),
('meetings.approve', 'Approve Meeting Minutes'),
('hostel.view', 'View Hostel'),
('hostel.manage', 'Manage Hostel Rooms and Allocations'),
('hostel.approve', 'Approve Hostel Applications'),
('transport.view', 'View Transport'),
('transport.manage', 'Manage Transport Routes and Allocations'),
('library.view', 'View Library Catalogue'),
('library.manage', 'Manage Library Books and Copies'),
('library.circulation', 'Issue and Return Books'),
('visitors.view', 'View Visitor Log'),
('visitors.manage', 'Register and Approve Visitors'),
('visitors.check_in', 'Check-in and Check-out Visitors')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- Assign Default Permissions to Admin Role
INSERT INTO role_permissions (role, permission_id)
SELECT 'Admin', permission_id FROM permissions
WHERE permission_name LIKE 'user.%' OR
      permission_name LIKE 'reports.%' OR
      permission_name LIKE 'assets.%' OR
      permission_name LIKE 'inventory.%' OR
      permission_name LIKE 'hr.%' OR
      permission_name LIKE 'payroll.%' OR
      permission_name LIKE 'payslip.%' OR
      permission_name LIKE 'documents.%' OR
      permission_name LIKE 'compliance.%' OR
      permission_name LIKE 'meetings.%' OR
      permission_name LIKE 'hostel.%' OR
      permission_name LIKE 'transport.%' OR
      permission_name LIKE 'library.%' OR
      permission_name LIKE 'visitors.%'
ON DUPLICATE KEY UPDATE role=VALUES(role);

-- Assign View Permissions to Principal Role
INSERT INTO role_permissions (role, permission_id)
SELECT 'Principal', permission_id FROM permissions
WHERE permission_name IN ('user.view', 'user.view_audit',
      'reports.view', 'reports.students.view', 'reports.faculty.view', 'reports.academics.view', 'reports.finance.view', 'reports.administration.view', 'reports.audit.view', 'reports.export_pdf',
      'assets.view', 'inventory.view',
      'hr.view', 'payroll.view', 'payslip.view',
      'documents.view', 'compliance.view', 'meetings.view')
ON DUPLICATE KEY UPDATE role=VALUES(role);

-- Assign Department-Scoped View Permissions to HOD Role
INSERT INTO role_permissions (role, permission_id)
SELECT 'HOD', permission_id FROM permissions
WHERE permission_name IN ('user.view',
      'reports.view', 'reports.students.view', 'reports.faculty.view', 'reports.academics.view',
      'assets.view', 'inventory.view', 'assets.request_maintenance',
      'hr.view',
      'documents.view', 'compliance.view', 'meetings.view')
ON DUPLICATE KEY UPDATE role=VALUES(role);

-- OPTIONAL SECURITY SETUP:
-- Run these statements separately as a database administrator after replacing the placeholder
-- with a strong, unique password. They are intentionally not executed by this schema script.
-- CREATE USER IF NOT EXISTS 'sgi_ai_readonly'@'localhost' IDENTIFIED BY 'REPLACE_WITH_A_STRONG_PASSWORD';
-- GRANT SELECT ON sgi_command_center.* TO 'sgi_ai_readonly'@'localhost';
-- FLUSH PRIVILEGES;

-- Additive index to optimize HOD department lookup
-- Create the index only when it does not already exist.
SET @index_exists = (
    SELECT COUNT(*)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'department_hod_assignments'
      AND index_name = 'idx_hod_assignments'
);
SET @migration_sql = IF(
    @index_exists = 0,
    'CREATE INDEX idx_hod_assignments ON department_hod_assignments(user_id, status)',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;


-- Add the section column only when upgrading an older database.
SET @column_exists = (
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'subjects'
      AND column_name = 'section'
);
SET @migration_sql = IF(
    @column_exists = 0,
    'ALTER TABLE subjects ADD COLUMN section VARCHAR(10) NULL',
    'SELECT 1'
);
PREPARE migration_stmt FROM @migration_sql;
EXECUTE migration_stmt;
DEALLOCATE PREPARE migration_stmt;

-- Backfill the section for existing subject records without overwriting assigned sections.
UPDATE subjects
SET section = 'A'
WHERE section IS NULL;

ALTER TABLE students DROP COLUMN hostel_service_enabled;
ALTER TABLE students DROP COLUMN transport_service_enabled;