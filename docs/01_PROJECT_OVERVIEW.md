# SGI Command Center — Project Overview

## 1. Document Purpose

This document provides the high-level technical and functional context of the SGI Command Center application.

It is intended to be read by:

- Developers working on the project
- AI coding assistants
- AI agents responsible for implementing future requirements
- Maintainers of Volume 1 and Volume 2
- Anyone who needs to understand the system before modifying it

This document describes the verified high-level structure, purpose, technology stack, user roles, major functional areas, AI components, and Volume 1 baseline of the application.

This document does NOT replace the source code.

The actual source code remains the implementation source of truth.

Detailed technical information is maintained separately in:

- `ARCHITECTURE.md`
- `DATABASE_SCHEMA.md`
- `FEATURE_MAP.md`
- `AUTH_AND_ROLES.md`
- `FILE_CATALOG.md`
- `VOLUME_1_BASELINE.md`

---

# 2. Project Identity

## 2.1 Project Name

**SGI Command Center**

The application identifies itself as:

> SGI Command Center — Comprehensive Campus Management System

The main FastAPI application is initialized with the following title:

```text
SGI Command Center

2.2 Project Type

SGI Command Center is a web-based college/campus management system.

The application provides role-specific portals and functionality for different institutional users, including the following:

Administrator
Principal
Head of Department (HOD)
Teacher
Student

The system combines:

Campus administration
Student management
Teacher management
Academic management
Attendance management
Marks and results
Fees
Notices
Complaints
Leave management
Timetable management
Placement-related functionality
Career assistance
Resume analysis
AI-powered assistance and teaching tools
Reports and PDF generation
3. Primary Objective

The primary objective of SGI Command Center is to provide a centralized digital platform for managing and accessing college-related information and operations.

Instead of treating administrative, academic, student, teacher, and AI-assisted functions as isolated systems, the application provides role-specific interfaces over a shared backend and database.

The system is designed around the following general model:

College/Campus
      |
      +----------------------+
      |                      |
      v                      v
Administration          Academic Operations
      |                      |
      |                      +------------------+
      |                      |                  |
      v                      v                  v
   Principal               HOD              Teachers
      |                      |                  |
      +----------------------+------------------+
                             |
                             v
                          Students

The actual application implementation is organized around FastAPI routers, database query modules, utility modules, AI modules, and Jinja2 templates.

4. High-Level System Concept

At a high level, the application follows a role-based web application architecture.

A typical request follows this general pattern:

Browser
   |
   v
FastAPI Application
   |
   v
Role-Specific Router
   |
   +--------------------+
   |                    |
   v                    v
Authentication       Database Query Layer
   |                    |
   |                    v
   |                 MySQL
   |
   v
Role-specific response
   |
   v
Jinja2 HTML Template / API Response

AI-assisted functionality introduces an additional path:

User
 |
 v
Role-specific Router
 |
 v
AI Module
 |
 v
Groq API
 |
 v
AI-generated response
 |
 v
Application UI

The exact implementation flow for each feature is documented separately in ARCHITECTURE.md and FEATURE_MAP.md.

5. Technology Stack
5.1 Backend Framework

The application uses:

FastAPI

FastAPI is responsible for:

Application initialization
HTTP routing
Request handling
Response handling
Router organization
Dependency-based authentication
API endpoints
HTML page endpoints

The application entry point is:

main.py
5.2 ASGI Server

The application is designed to run using:

Uvicorn

The main.py file starts Uvicorn when executed directly.

The configured development server is:

127.0.0.1:8000
5.3 HTML Templating

The application uses:

Jinja2

FastAPI's Jinja2Templates is configured against:

templates/

HTML pages are therefore rendered server-side through Jinja2 templates.

The project contains both:

Shared templates
Role-specific templates

Role-specific template directories include:

templates/admin/
templates/hod/
templates/principal/
templates/student/
templates/teacher/

Shared templates include:

templates/base.html
templates/index.html
templates/login.html
templates/profile.html
5.4 Static Files

The application exposes:

/static

through FastAPI's StaticFiles.

Static resources are stored under:

static/

The current project contains the following:

static/css/
static/images/
static/uploads/

The main stylesheet is:

static/css/style.css

The images directory contains application and user-related image assets.

The uploads directory currently contains an uploaded resume PDF.

5.5 Database

The application uses:

MySQL

The Python database connection layer uses:

PyMySQL

Database connection configuration is loaded from environment variables.

The database-related implementation is organized under:

database/

The project contains:

database/database.sql
database/connection.py

and role/domain-specific query modules.

5.6 Authentication

The application uses:

JWT-based authentication

JWT tokens are stored and retrieved through an HTTP cookie named:

access_token

The authentication implementation is primarily located in:

utils/auth.py
utils/session.py
routers/login.py

The JWT algorithm configured by the application is:

HS256

The JWT secret is loaded from the environment rather than being directly defined in the source code.

5.7 Password Security

Passwords are handled using:

bcrypt

The password utility is:

utils/password.py

It provides functionality for:

Hashing passwords
Verifying passwords against stored hashes
5.8 Environment Configuration

The application uses:

python-dotenv

Configuration is loaded from:

.env

The project currently uses the following environment variables:

DB_HOST
DB_USER
DB_PASSWORD
DB_NAME
JWT_SECRET
GROQ_API_KEY

Secret values must NOT be stored in project documentation or provided to AI coding agents as part of normal context.

Only variable names and configuration semantics should be documented.

5.9 AI Integration

The application contains multiple AI modules under:

ai/

The current AI modules are:

ai/career.py
ai/principal.py
ai/resume.py
ai/teacher.py

The AI functionality uses the Groq API.

The code uses the OpenAI Python SDK interface with a Groq-compatible API base URL.

The configured AI model in the current AI implementations is:

llama-3.1-8b-instant

The AI functionality currently covers several application-specific use cases, including:

Student career roadmap generation
Principal data analysis assistant
Resume-related analysis
Teacher AI tools

The detailed behavior of each AI module is documented separately and must be verified against the source code before modification.

5.10 PDF Generation

The application contains:

utils/pdf_generator.py

and uses ReportLab for PDF generation.

PDF functionality is used for application reporting functionality.

5.11 Data Visualization

The project's declared dependencies include the following:

matplotlib

This indicates support for data visualization functionality.

Any future AI or reporting implementation that relies on visualization must be verified against the actual implementation before assuming where or how charts are generated.

5.12 Image Processing

The project declares the following dependency:

Pillow

as a dependency.

The project also contains image assets under:

static/images/

and supports profile image uploads through the profile router.

6. Application Entry Point

The primary application entry point is:

main.py

The application creates a FastAPI instance:

app = FastAPI(title="SGI Command Center")

The application mounts the static directory:

/static

and registers the following routers:

login
admin
student
teacher
hod
principal
profile

Therefore, the application is organized into role/domain-specific routing modules rather than placing all endpoints in a single file.

7. User Roles

The application currently implements the following major user roles:

ADMIN
PRINCIPAL
HOD
TEACHER
STUDENT

Each role has its own router and, where applicable, its own templates.

The role-specific backend structure is:

routers/
├── admin.py
├── hod.py
├── principal.py
├── student.py
└── teacher.py

Authentication itself is handled separately through:

routers/login.py

Role-independent profile functionality is handled through:

routers/profile.py
8. Administrator

The administrator is responsible for institution-level management functionality.

The administrator router is:

routers/admin.py

The administrator interface is located under:

templates/admin/

The currently implemented administrator areas include:

Dashboard
Departments
Students
Teachers
Subjects
Results
Notices
Events
Complaints
Timetable
Fees
Users
Reports

The administrator router contains both HTML page endpoints and API-style endpoints for several of these functions.

Examples of implemented administrative routes include:

/admin/dashboard
/admin/departments
/admin/results
/admin/notices
/admin/complaints
/admin/students
/admin/teachers
/admin/subjects
/admin/timetable
/admin/fees
/admin/users
/admin/reports

Administrative functionality includes operations such as:

Adding and updating departments
Managing students
Managing teachers
Managing subjects
Generating and publishing results
Adding notices and events
Updating complaints
Managing timetable rooms and slots
Generating timetable data
Managing fee structures and student fees
Recording fee payments
Managing users
Generating reports

The exact permissions and database relationships are documented separately in:

AUTH_AND_ROLES.md
DATABASE_SCHEMA.md
FEATURE_MAP.md
9. Principal

The principal has an institution-level overview and AI-assisted data analysis functionality.

The backend router is:

routers/principal.py

The templates are:

templates/principal/

The principal functionality currently includes:

Principal dashboard
Institution-level dashboard analytics
Principal AI assistant

The AI assistant endpoint is:

/principal/api/ai/ask

The corresponding AI implementation is:

ai/principal.py

The principal AI assistant receives database-derived context and is instructed to answer questions strictly using the provided records.

The implementation specifically instructs the AI assistant to state when requested information is not available in the supplied database records.

10. Head of Department (HOD)

The HOD functionality is implemented through:

routers/hod.py

The corresponding templates are:

templates/hod/

The currently implemented HOD areas include:

Department dashboard
Department-level dashboard API
Leave management
Leave retrieval
Leave status updates

The HOD router exposes endpoints under:

/hod/

including:

/hod/dashboard
/hod/api/dashboard
/hod/leaves
/hod/api/leaves
/hod/api/leaves/update

The HOD functionality is intended to operate within department-level institutional management.

Exact department-level access rules must be read from the implementation and are documented separately in AUTH_AND_ROLES.md.

11. Teacher

Teacher functionality is implemented through:

routers/teacher.py

Teacher templates are located under:

templates/teacher/

The current teacher portal includes the following:

Teacher dashboard
Attendance
Marks
AI teaching tools
Leave management
Teacher dashboard analytics
11.1 Teacher Attendance

The teacher router provides functionality for:

Retrieving assigned subjects
Retrieving students
Saving attendance

Relevant endpoints include:

/teacher/attendance
/teacher/api/subjects
/teacher/api/students
/teacher/api/save-attendance
11.2 Teacher Marks

The teacher portal supports:

Viewing marks-related information
Saving marks

Relevant endpoints include:

/teacher/marks
/teacher/api/marks
/teacher/api/save-marks
11.3 Teacher AI Tools

The teacher portal contains:

templates/teacher/ai_tools.html

and exposes AI-related endpoints for:

Question paper generation
Assignment generation

Relevant endpoints include:

/teacher/api/ai/question-paper
/teacher/api/ai/assignment

The corresponding AI implementation is:

ai/teacher.py
11.4 Teacher Leave Management

Teacher leave functionality includes:

Leave page
Leave retrieval
Leave submission

Relevant endpoints include:

/teacher/leaves
/teacher/api/leaves
/teacher/api/leaves/add
12. Student

Student functionality is implemented through:

routers/student.py

Student templates are located under:

templates/student/

The current student portal includes the following:

Dashboard
Profile information
Attendance
Marks
Results
Fees
Notices
Complaints
Career assistance
Placement-related functionality
Resume upload
12.1 Student Dashboard

The student dashboard is available through:

/student/dashboard

The student interface is designed around student-specific information and quick access to major student services.

12.2 Student Attendance

Student attendance functionality includes:

/student/attendance
/student/api/attendance

The student can retrieve attendance information through the corresponding API endpoint.

12.3 Student Marks

Student marks functionality includes:

/student/marks
/student/api/marks
12.4 Student Results

Student results functionality includes:

/student/result
/student/api/result
12.5 Student Fees

Student fee functionality includes:

/student/fees
/student/api/fees

The application also contains payment-related endpoints:

/student/api/payment/create
/student/api/payment/verify

The exact payment implementation and transaction flow must be verified from the relevant router and database query implementation before extending it.

12.6 Student Notices

Student notices are exposed through:

/student/notices
/student/api/notices
12.7 Student Complaints

Student complaint functionality includes:

/student/complaints
/student/api/complaints
/student/api/complaints/add
12.8 Student Career Assistance

The student career module is available through:

/student/career
/student/api/career/saved
/student/api/career/generate

The AI implementation is:

ai/career.py

The career AI receives student information including:

CGPA
Skills
Interests
Preferred domain
Desired salary

and generates structured career guidance.

The generated response is designed as structured JSON containing areas such as:

Career roles
Skill gaps
Courses
Certifications
Projects
Interview preparation

The exact persistence mechanism for generated recommendations must be verified through the student router and database query layer.

12.9 Student Placement and Resume

The student placement interface is:

/student/placement

The current student router also provides:

/student/api/placement/saved
/student/api/placement/upload

The application therefore supports placement-related information and resume uploading.

Resume-related AI processing is implemented in:

ai/resume.py
13. Profile Management

Profile functionality is implemented independently of the role-specific routers.

The router is:

routers/profile.py

The current profile functionality includes:

/profile
/api/profile/details
/api/profile/update
/api/profile/upload

The application therefore supports:

Viewing profile details
Updating profile details
Uploading a profile image

Profile database operations are separated into:

database/profile_queries.py
14. Authentication and Session Model

Authentication is implemented using JWT tokens.

The main authentication components are:

routers/login.py
utils/auth.py
utils/session.py
utils/password.py

The general authentication flow is:

User
 |
 v
Login Page
 |
 v
Login Request
 |
 v
Credential Verification
 |
 v
JWT Session Creation
 |
 v
access_token Cookie
 |
 v
Authenticated Request
 |
 v
JWT Validation
 |
 v
Role Validation
 |
 v
Protected Resource

The authentication utility retrieves the JWT from the access_token cookie.

The decoded JWT payload contains:

user_id
full_name
email
role
department_id

Role checking is implemented through a reusable RoleChecker.

Detailed authentication behavior is documented separately in:

AUTH_AND_ROLES.md
15. Database Organization

The application uses a MySQL database.

The database schema is maintained in:

database/database.sql

The current schema contains tables covering areas such as the following:

departments
users
students
teachers
subjects
attendance
marks
notices
events
complaints
assignments
assignment_submissions
companies
placement_applications
career_recommendations
resume_analysis
leave_requests
feedback
login_history
audit_logs
results
rooms
time_slots
timetable
teacher_availability
fee_structure
student_fees
fee_payments
payment_transactions
payment_audit

These tables represent the major institutional, academic, student, teacher, placement, AI, security, timetable, and financial areas present in the Volume 1 database schema.

The database access layer is separated into domain-oriented query modules:

database/admin_queries.py
database/fee_queries.py
database/hod_queries.py
database/principal_queries.py
database/profile_queries.py
database/student_queries.py
database/teacher_queries.py
database/user_queries.py

Detailed table structures, keys, relationships, and query responsibilities belong in:

DATABASE_SCHEMA.md
16. Major Functional Domains

Based on the current implementation, SGI Command Center contains the following major functional domains.

16.1 Authentication

Responsible for:

Login
Credential verification
JWT session creation
Authentication validation
Role authorization

Primary files:

routers/login.py
utils/auth.py
utils/session.py
utils/password.py
16.2 User Management

Responsible primarily for administrator-level user management.

Primary files include:

routers/admin.py
database/admin_queries.py
database/user_queries.py
16.3 Department Management

Department-related functionality is primarily exposed through the administrator portal and HOD-related functionality.

Primary components include:

routers/admin.py
routers/hod.py
database/admin_queries.py
database/hod_queries.py
16.4 Student Management

Student management includes:

Student records
Student dashboard
Attendance
Marks
Results
Fees
Complaints
Notices
Career
Placement

Primary backend component:

routers/student.py

with additional administrative functionality in:

routers/admin.py
16.5 Teacher Management

Teacher management includes:

Teacher records
Teacher dashboard
Attendance
Marks
AI teaching tools
Leave management

Primary backend components:

routers/teacher.py
routers/admin.py
16.6 Attendance

Attendance functionality exists for:

Teacher-side attendance recording
Student-side attendance viewing
Administrative attendance reporting

Teacher endpoints include:

/teacher/attendance

Student endpoints include:

/student/attendance
/student/api/attendance

Administrative attendance/reporting functionality must be verified against the current administrator implementation.

16.7 Marks and Results

Marks and results functionality is distributed across:

Teacher
Student
Administrator
Principal

Teacher functionality includes marks entry.

Student functionality includes marks/result viewing.

Administrator functionality includes result management and publication.

Principal functionality currently includes institution-level result-related visibility/approval areas where implemented.

The exact authority boundaries are documented in:

AUTH_AND_ROLES.md
16.8 Fees and Finance

The application contains fee-related functionality for:

Fee structures
Student fees
Fee payments
Payment transactions
Payment audit
Student fee viewing
Administrative fee management

Relevant backend components include:

database/fee_queries.py
routers/admin.py
routers/student.py

The database contains financial tables including:

fee_structure
student_fees
fee_payments
payment_transactions
payment_audit
16.9 Notices and Events

The application supports notices and events.

Administrative functionality includes notice/event management.

Students have access to published notices.

Relevant areas include:

templates/admin/notices.html
templates/student/notices.html
routers/admin.py
routers/student.py
16.10 Complaints

Complaint functionality exists for students and administrators, with principal-related sensitive complaint functionality also present.

Student complaint endpoints include:

/student/complaints
/student/api/complaints
/student/api/complaints/add

Administrative complaint functionality is available through:

/admin/complaints

The principal portal also contains:

templates/principal/sensitive_complaints.html

Complaint authority and visibility must follow the role/permission rules documented in AUTH_AND_ROLES.md.

16.11 Timetable

The application contains timetable functionality involving:

rooms
time_slots
timetable
teacher_availability

Administrative timetable functionality includes management of:

Rooms
Time slots
Timetable data

The relevant backend implementation is primarily in:

routers/admin.py

and supporting database queries.

16.12 Leave Management

Leave management exists for:

Teachers
HODs

Teacher leave functionality includes:

/teacher/leaves
/teacher/api/leaves
/teacher/api/leaves/add

HOD leave functionality includes:

/hod/leaves
/hod/api/leaves
/hod/api/leaves/update
16.13 Placement

Placement-related functionality exists primarily for students.

Relevant student routes include:

/student/placement
/student/api/placement/saved
/student/api/placement/upload

The database contains placement-related structures including:

companies
placement_applications
16.14 Career Assistance

Career assistance is implemented for students.

The student-facing career interface is:

/student/career

AI generation is exposed through:

/student/api/career/generate

The corresponding AI module is:

ai/career.py

Career recommendations may include:

Career roles
Skill gaps
Courses
Certifications
Projects
Interview preparation
16.15 Resume Analysis

Resume functionality is associated with student placement/career features.

The corresponding AI module is:

ai/resume.py

The student router provides resume upload functionality.

Resume analysis must use the actual implementation and database behavior rather than assumptions about future functionality.

16.16 AI-Powered Features

The project currently contains multiple AI modules:

ai/career.py
ai/principal.py
ai/resume.py
ai/teacher.py

Current application-level AI use cases include:

Student Career Assistance
Principal AI Assistant
Resume Analysis
Teacher Question Paper Generation
Teacher Assignment Generation

The current implementation uses Groq-backed AI.

AI behavior must not be assumed beyond the functionality implemented in the relevant source files.

16.17 Reports and PDF Generation

The project contains reporting functionality and PDF generation support.

The PDF utility is:

utils/pdf_generator.py

The project also contains administrator report templates such as:

templates/admin/reports.html
templates/admin/report_preview.html

The exact report types and data sources must be verified against the implementation before extending the reporting system.

17. Current Template Organization

The template structure is divided into shared templates and role-specific templates.

The main shared templates are:

templates/
├── base.html
├── index.html
├── login.html
└── profile.html

Administrator templates are located under:

templates/admin/

HOD templates are located under:

templates/hod/

Principal templates are located under:

templates/principal/

Student templates are located under:

templates/student/

Teacher templates are located under:

templates/teacher/

The exact file-level responsibilities are catalogued separately in:

FILE_CATALOG.md
18. Current Principal Portal Baseline

The current Principal portal contains:

templates/principal/
├── ai_assistant.html
├── concessions.html
├── dashboard.html
├── notice_approvals.html
├── principal_layout.html
├── results_approval.html
└── sensitive_complaints.html

The backend implementation is:

routers/principal.py

and the database query implementation is:

database/principal_queries.py

The current AI implementation is:

ai/principal.py

The existing Principal portal should be treated as the baseline when implementing future Principal Command Center functionality.

Future enhancements must extend the existing system rather than creating duplicate student, teacher, fee, result, complaint, or document data stores.

19. Current Administrator Portal Baseline

The administrator portal currently contains a broad set of institutional management functionality.

The administrator templates include areas for:

Dashboard
Assets
Asset details
Complaints
Departments
Department details
Disposals
Fees
Finance reports
Inventory
Maintenance
Notices
Reports
Report preview
Results
Revaluation
Stock requests
Students
Student profile
Subjects
Subject profile
Teachers
Teacher profile
Timetable
Users

The administrator portal therefore already contains substantial institutional functionality.

Future modules must reuse this existing functionality and its underlying database structures where appropriate.

20. Campus and Operational Functionality

The project contains a separate campus template area:

templates/campus/

The current templates include:

dashboard.html
hostel_applications.html
hostel_rooms.html
library.html
transport.html
visitors.html

The corresponding backend functionality is associated with:

routers/campus.py
database/campus_queries.py

These areas represent campus operations such as:

Hostel
Library
Transport
Visitors

Future Principal-level oversight functionality should use these existing campus operations rather than introducing duplicate operational data models.

21. HR and Payroll Functionality

The project contains:

routers/hr.py

and:

templates/hr/

The current HR templates include:

dashboard.html
employees.html
exits.html
payroll.html
salary_components.html
salary_revisions.html

The HR domain is therefore represented as a separate application area.

Future Principal-level HR oversight should consume the existing HR data and business logic rather than maintaining a separate Principal-specific HR system.

22. Documents and Compliance Functionality

The project contains a document/compliance domain through:

routers/docs.py

and:

templates/docs/

The current document-related templates include:

action_items.html
compliance.html
dashboard.html
meetings.html
repository.html

This area provides functionality related to:

Institutional documents
Compliance
Meetings
Action items
Document repository

The project also contains:

private_uploads/docs/

with institutional document files.

Future Principal Command Center functionality should integrate with this existing document/compliance domain rather than creating a duplicate document repository.

23. Asset and Inventory Functionality

The project contains asset/inventory functionality.

Relevant backend components include:

routers/asset.py
database/asset_queries.py

Administrator templates include:

templates/admin/assets.html
templates/admin/asset_details.html
templates/admin/disposals.html
templates/admin/inventory.html
templates/admin/maintenance.html
templates/admin/stock_requests.html

The project also contains QR code assets under:

static/uploads/qrcodes/

The existing asset and inventory system should remain authoritative for institutional asset data.

24. Testing

The project contains a dedicated test directory:

test/

Current test files include:

test_asset_inventory.py
test_campus_operations.py
test_complaints.py
test_docs_compliance.py
test_fee_queries.py
test_grade.py
test_hr_payroll.py
test_notices.py
test_reports.py
test_users.py

These tests cover several existing application domains.

Any future modification should preserve existing behavior and should add or update tests where appropriate.

25. Existing Documentation Set

The project documentation set contains the following documents:

docs/
├── 01_PROJECT_OVERVIEW.md
├── 02_ARCHITECTURE.md
├── 03_DATABASE_SCHEMA.md
├── 04_FEATURE_MAP.md
├── 05_AUTH_AND_ROLES.md
├── 06_FILE_CATALOG.md
└── 07_VOLUME_1_BASELINE.md

Each document has a specific purpose.

01_PROJECT_OVERVIEW.md

Provides:

Project identity
Technology stack
User roles
Major functional areas
High-level architecture
AI components
Current system overview
02_ARCHITECTURE.md

Provides the deeper application architecture and implementation structure.

03_DATABASE_SCHEMA.md

Provides database tables, fields, keys, relationships, and database responsibilities.

04_FEATURE_MAP.md

Maps functional requirements and features to application areas.

05_AUTH_AND_ROLES.md

Documents authentication, authorization, roles, and access rules.

06_FILE_CATALOG.md

Documents project files and their responsibilities.

07_VOLUME_1_BASELINE.md

Documents the Volume 1 implementation baseline.

26. Important Development Rules

The following principles should be followed when modifying the application.

26.1 Source Code Is the Source of Truth

Documentation provides context, but the actual source code is authoritative.

AI coding assistants must inspect the relevant source files before making assumptions about implementation details.

26.2 Existing Data Models Must Be Reused

Future functionality should reuse existing:

Students
Teachers
Departments
Subjects
Fees
Results
Complaints
Timetable
Assets
Campus operations
Documents
HR
Payroll
Users

where applicable.

Duplicate authoritative data stores must not be created without a clear architectural requirement.

26.3 Existing Authentication Must Be Reused

Future protected functionality must integrate with the existing:

JWT authentication
access_token cookie
RoleChecker

implementation.

A second independent authentication mechanism should not be introduced without an explicit architectural decision.

26.4 Existing Database Layer Must Be Respected

Database operations should follow the existing project structure.

Existing query modules should be reused or extended where appropriate.

New functionality should not bypass established database access patterns without justification.

26.5 AI Must Not Replace Application Authorization

AI-generated responses or AI tools must not be treated as an authorization mechanism.

The application backend must remain responsible for:

Authentication
Role authorization
Data access
Validation
Business rules
Database operations

AI functionality must operate within those boundaries.

26.6 Do Not Invent Institutional Data

AI assistants and future development tools must not fabricate:

Student records
Faculty records
Fees
Results
Departments
Institutional policies
Compliance status
Approval status

When required information is unavailable, the system should clearly indicate that it is unavailable.

27. Current Development Baseline

The current SGI Command Center project should be understood as a working multi-role college management application with:

FastAPI
+
Jinja2
+
MySQL
+
PyMySQL
+
JWT Authentication
+
Role-Based Access
+
Groq AI Integration
+
ReportLab
+
Matplotlib
+
Pillow

The application already contains substantial functionality across:

Administration
Students
Teachers
HOD
Principal
HR
Fees
Academic Management
Attendance
Marks
Results
Timetable
Complaints
Notices
Campus Operations
Documents
Compliance
Assets
Inventory
Placement
Career Assistance
Resume Analysis
AI Assistance
Reports

Therefore, future development should be treated as an extension of an existing production-oriented application rather than as a greenfield project.

28. Principal Command Center Development Context

The existing Principal functionality is currently smaller than the overall administrator functionality.

The current Principal implementation includes:

Principal Dashboard
Principal AI Assistant
Result Approval
Fee Concession
Notice Approval
Sensitive Complaints

Future Principal Command Center development may expand the Principal role into a more comprehensive institution-level oversight interface.

However, any future expansion must preserve the existing role boundaries and must reuse authoritative application data.

The Principal should operate as an institution-level oversight and decision-making layer, not as a duplicate administrator portal.

29. Future Multi-Agent AI Context

The project is expected to evolve toward a more capable Principal AI system.

The intended future concept is an agentic system capable of:

Understanding Principal requests
Identifying user intent
Retrieving authorized institutional information
Performing permitted actions
Generating reports
Providing analytics
Supporting multilingual interaction
Maintaining task context
Requesting confirmation for sensitive operations

A future architecture may contain specialized agents such as:

Principal Supervisor Agent
        |
        +-- Academic Agent
        |
        +-- Finance Agent
        |
        +-- HR/Payroll Agent
        |
        +-- Campus Operations Agent
        |
        +-- Compliance & Document Agent
        |
        +-- Grievance Agent
        |
        +-- Reporting Agent

This architecture is a future development direction and must not be treated as already implemented unless verified in the source code.

30. AI Safety and Authorization Context

Any future AI agent implementation must respect the following principles:

User Request
     |
     v
Intent Understanding
     |
     v
Authorization Check
     |
     v
Scope Validation
     |
     v
Business Rule Validation
     |
     v
Confirmation if Required
     |
     v
Authorized Backend Operation
     |
     v
Database
     |
     v
Audit
     |
     v
Response

The AI layer must not receive unrestricted database access.

AI tools should interact with controlled backend functionality rather than arbitrary SQL execution.

Sensitive operations should use explicit confirmation and appropriate audit logging.

31. Documentation Maintenance

Whenever a major architectural change is made, the relevant documentation should be updated.

Examples:

New database table → update DATABASE_SCHEMA.md
New router/module → update FILE_CATALOG.md
New feature → update FEATURE_MAP.md
New permission → update AUTH_AND_ROLES.md
Major architecture change → update ARCHITECTURE.md
Major baseline change → update VOLUME_1_BASELINE.md
Overall system change → update PROJECT_OVERVIEW.md

Documentation should describe the implemented system rather than an aspirational system.

32. Final Project Summary

SGI Command Center is a FastAPI-based, MySQL-backed, role-oriented college/campus management platform.

The system currently provides:

                    SGI COMMAND CENTER
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   Administration      Academics          Students
        |                  |                  |
        |                  +--------+---------+
        |                           |
        v                           v
     Principal                     HOD
        |                           |
        +-------------+-------------+
                      |
                      v
                   Teachers

The backend is organized into:

main.py
routers/
database/
utils/
ai/
templates/
static/
test/

Authentication is based on JWT.

Database operations are handled through PyMySQL and domain-specific query modules.

The UI is rendered through Jinja2 templates.

AI capabilities are implemented through Groq-backed modules.

The application already contains substantial functionality across administration, academics, student services, teacher operations, campus operations, documents, compliance, HR, finance, placement, and AI assistance.

The existing source code remains authoritative.

Future development must extend the existing architecture carefully, preserve authorization boundaries, reuse existing data models, avoid duplicate authoritative systems, and verify implementation details before making changes.