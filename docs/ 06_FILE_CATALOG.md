# SGI COMMAND CENTER — FILE CATALOG

**Document:** `06_FILE_CATALOG.md`  
**Project:** SGI Command Center  
**Documentation Volume:** Volume 2  
**Document Role:** Source-File Navigation and Responsibility Catalog  
**Audience:** AI coding agents, maintainers, senior developers, reviewers  
**Primary Purpose:** Provide a structured map of important project files, their responsibilities, dependencies, investigation priority, and risk classification.

---

# 01. DOCUMENT PURPOSE

This document provides an AI-oriented catalog of the SGI Command Center source tree.

Its purpose is to help an AI agent answer:

- Which file should I inspect first?
- Which file owns this functionality?
- Which file contains the database operation?
- Which router exposes the functionality?
- Which utility is responsible for shared behavior?
- Which AI module is involved?
- Which files may be affected by a change?
- Which files should not be modified without dependency tracing?
- Which files are security-critical?
- Which files are safe to modify independently?
- Which files require regression testing after modification?

This document is a navigation layer.

It is NOT a replacement for reading the actual source code.

---

# 02. SOURCE-OF-TRUTH RULE

The actual project source code is authoritative.

This catalog provides:

```text
Navigation
Ownership hints
Dependency hints
Investigation order
Risk classification
Architectural context

It must not be treated as proof of implementation details that are not confirmed in the source.

If this document conflicts with the current source code:

CURRENT SOURCE CODE WINS

If this document conflicts with the actual database schema:

ACTUAL DATABASE SCHEMA WINS

If this document conflicts with current runtime behavior:

CURRENT RUNTIME BEHAVIOR WINS
03. PROJECT STRUCTURE OVERVIEW

The known SGI Command Center architecture is organized around these major areas:

SGI COMMAND CENTER
│
├── Root application files
│
├── routers/
│
├── database/
│
├── ai/
│
├── utils/
│
├── templates/
│
├── static/
│
├── private_uploads/
│
└── configuration

The project uses a FastAPI-based application architecture with:

FastAPI
Jinja2
MySQL
PyMySQL
JWT authentication
Role-based routing
AI modules
Report generation
HTML/CSS
Static assets
File uploads
04. KNOWN PROJECT TREE

The current known project structure is:

SGI_Command_Center/
│
├── .env
├── config.py
├── main.py
├── requirements.txt
├── create_admin.py
├── create_hod.py
├── create_principal.py
├── generate_doc_files.py
├── generate_qrcodes.py
│
├── ai/
│   ├── career.py
│   ├── principal.py
│   ├── resume.py
│   └── teacher.py
│
├── database/
│   ├── admin_queries.py
│   ├── asset_queries.py
│   ├── campus_queries.py
│   ├── connection.py
│   ├── database.sql
│   ├── docs_queries.py
│   ├── fee_queries.py
│   ├── hod_queries.py
│   ├── hr_queries.py
│   ├── principal_queries.py
│   ├── profile_queries.py
│   ├── student_queries.py
│   ├── teacher_queries.py
│   └── user_queries.py
│
├── routers/
│   ├── admin.py
│   ├── asset.py
│   ├── campus.py
│   ├── docs.py
│   ├── hod.py
│   ├── hr.py
│   ├── login.py
│   ├── principal.py
│   ├── profile.py
│   ├── student.py
│   └── teacher.py
│
├── utils/
│   ├── auth.py
│   ├── grade.py
│   ├── password.py
│   ├── pdf_generator.py
│   └── session.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── profile.html
│   │
│   ├── admin/
│   │   ├── admin_layout.html
│   │   ├── assets.html
│   │   ├── asset_details.html
│   │   ├── complaints.html
│   │   ├── dashboard.html
│   │   ├── departments.html
│   │   ├── department_details.html
│   │   ├── disposals.html
│   │   ├── fees.html
│   │   ├── finance_reports.html
│   │   ├── inventory.html
│   │   ├── maintenance.html
│   │   ├── notices.html
│   │   ├── reports.html
│   │   ├── report_preview.html
│   │   ├── results.html
│   │   ├── revaluation.html
│   │   ├── stock_requests.html
│   │   ├── students.html
│   │   ├── student_profile.html
│   │   ├── subjects.html
│   │   ├── subject_profile.html
│   │   ├── teachers.html
│   │   ├── teacher_profile.html
│   │   ├── timetable.html
│   │   └── users.html
│   │
│   ├── campus/
│   │   ├── dashboard.html
│   │   ├── hostel_applications.html
│   │   ├── hostel_rooms.html
│   │   ├── library.html
│   │   ├── transport.html
│   │   └── visitors.html
│   │
│   ├── docs/
│   │   ├── action_items.html
│   │   ├── compliance.html
│   │   ├── dashboard.html
│   │   ├── meetings.html
│   │   └── repository.html
│   │
│   ├── hod/
│   │   ├── dashboard.html
│   │   ├── hod_layout.html
│   │   ├── leaves.html
│   │   └── marks_verification.html
│   │
│   ├── hr/
│   │   ├── dashboard.html
│   │   ├── employees.html
│   │   ├── exits.html
│   │   ├── payroll.html
│   │   ├── salary_components.html
│   │   └── salary_revisions.html
│   │
│   ├── principal/
│   │   ├── ai_assistant.html
│   │   ├── concessions.html
│   │   ├── dashboard.html
│   │   ├── notice_approvals.html
│   │   ├── principal_layout.html
│   │   ├── results_approval.html
│   │   └── sensitive_complaints.html
│   │
│   ├── student/
│   │   ├── attendance_report.html
│   │   ├── career.html
│   │   ├── complaints.html
│   │   ├── dashboard.html
│   │   ├── fees.html
│   │   ├── marks.html
│   │   ├── notices.html
│   │   ├── placement.html
│   │   ├── result.html
│   │   ├── student_layout.html
│   │   └── timetable.html
│   │
│   └── teacher/
│       ├── ai_tools.html
│       ├── attendance.html
│       ├── dashboard.html
│       ├── leaves.html
│       ├── marks.html
│       ├── teacher_layout.html
│       └── timetable.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── images/
│   │   ├── default.png
│   │   ├── SGI_Campus.jpg
│   │   ├── sgi_login.png
│   │   ├── user_1.jpeg
│   │   ├── user_1.jpg
│   │   └── user_6.jpeg
│   │
│   └── uploads/
│       ├── qrcodes/
│       │   ├── SGI-ELE-0001.png
│       │   ├── SGI-FUR-0001.png
│       │   ├── SGI-FUR-0002.png
│       │   ├── SGI-IT-0001.png
│       │   ├── SGI-IT-0002.png
│       │   ├── SGI-IT-0003.png
│       │   ├── SGI-LAB-0001.png
│       │   └── visitor_VSR003.png
│       └── resume_4.pdf
│
├── private_uploads/
│   └── docs/
│       ├── aicte_2023.pdf
│       └── policy_2024.pdf
│
└── docs/
    ├── 01_PROJECT_OVERVIEW.md
    ├── 02_ARCHITECTURE.md
    ├── 03_DATABASE_SCHEMA.md
    ├── 04_FEATURE_MAP.md
    ├── 05_AUTH_AND_ROLES.md
    ├── 06_FILE_CATALOG.md
    └── 07_VOLUME_1_BASELINE.md

Archive/environment directories such as:

.idea/
.venv/
__pycache__/
test/.pytest_cache/

are development/environment artifacts and should not automatically be treated as application architecture.

05. ROOT APPLICATION FILES
05.1 main.py
Responsibility

Application entry point.

Potential responsibilities include:

Application startup
FastAPI application creation
Router registration
Global configuration
Static file mounting
Template configuration
Application-wide middleware
Investigation Priority
CRITICAL / HIGH
Inspect when
Adding a router
Removing a router
Changing global middleware
Changing startup behavior
Changing application-wide configuration
Changing static/template registration
Debugging route registration
Important rule

Do not assume all routes are defined directly inside main.py.

The architecture separates functionality into routers.

06. CONFIGURATION
06.1 config.py
Responsibility

Application configuration.

Known configuration areas include:

Database host
Database user
Database password
Database name

It is related to:

database/connection.py
Risk
HIGH
Inspect when
Database configuration changes
Environment configuration changes
Deployment configuration changes
Application configuration changes
Security Rule

Never hard-code secrets into source code.

07. ENVIRONMENT FILE
07.1 .env

The project uses environment-backed configuration.

Potential sensitive values include:

Database credentials
API credentials
AI provider credentials
Secret keys
Environment-specific configuration
Security rules

Never copy real secrets into:

Documentation
Markdown files
Source code
AI prompts
Git repositories
Screenshots

Never expose .env contents in generated documentation.

08. REQUIREMENTS FILE
08.1 requirements.txt
Responsibility

Defines Python package dependencies.

It should be inspected when:

Adding a Python dependency
Removing a dependency
Changing AI frameworks
Changing database libraries
Changing PDF/report functionality
Changing authentication libraries

Before adding a package:

Check whether an existing dependency already provides the required functionality.

Avoid unnecessary dependency duplication.

09. DATABASE PACKAGE

The current database package contains:

database/
│
├── connection.py
├── database.sql
├── admin_queries.py
├── asset_queries.py
├── campus_queries.py
├── docs_queries.py
├── fee_queries.py
├── hod_queries.py
├── hr_queries.py
├── principal_queries.py
├── profile_queries.py
├── student_queries.py
├── teacher_queries.py
└── user_queries.py

These files form the primary database/query layer.

The project uses:

MySQL
+
PyMySQL

The existing query-module architecture should be reused rather than introducing a parallel database abstraction without an explicit requirement.

10. DATABASE CONNECTION
10.1 database/connection.py
Responsibility

Creates database connections using the project's MySQL/PyMySQL architecture.

Related
config.py
database query modules
routers
Risk
CRITICAL

A database connection change can affect the entire application.

Inspect when
Database connection fails
Credentials/configuration change
Connection pooling is changed
Database host changes
Database driver changes
11. DATABASE SCHEMA FILE
11.1 database/database.sql
Responsibility

Database schema/reference SQL.

It should be treated as an important database source artifact.

Inspect this file when investigating:

Tables
Columns
Primary keys
Foreign keys
Indexes
Constraints
ENUM values
Relationships
Rule

Do not assume the documentation is more authoritative than the actual database.

When schema discrepancies exist:

Actual database
        ↓
Current application queries
        ↓
database.sql
        ↓
Documentation

should be investigated in that order.

12. ADMIN QUERY MODULE
12.1 database/admin_queries.py
Responsibility

Database operations supporting administrative functionality.

Major areas include:

Users
Students
Teachers
Departments
Subjects
Timetable
Notices
Events
Complaints
Fees
Reports
Administrative analytics
Assets / operational data where applicable
Risk
CRITICAL

Admin query changes may affect system-wide data.

Inspect before modifying

Trace:

routers/admin.py
templates/admin/
database schema
related query modules
13. ASSET QUERY MODULE
13.1 database/asset_queries.py
Responsibility

Database operations related to:

Assets
Inventory
Asset details
Maintenance
Disposal
Stock-related operations

Related router:

routers/asset.py

Related templates include areas under:

templates/admin/
Risk
HIGH

Asset and inventory records are institutional operational data.

14. CAMPUS QUERY MODULE
14.1 database/campus_queries.py
Responsibility

Database operations for campus operations.

Known areas include:

Hostel
Library
Transport
Visitors
Campus dashboard

Related router:

routers/campus.py

Related templates:

templates/campus/
Risk
HIGH

especially for operational records and personally identifiable information.

15. DOCUMENTS QUERY MODULE
15.1 database/docs_queries.py
Responsibility

Database operations for institutional document/compliance functionality.

Known areas include:

Document Repository
Compliance
Meetings
Action Items
Document Dashboard

Related router:

routers/docs.py

Related templates:

templates/docs/
Risk
HIGH

because documents may contain institutional and compliance information.

16. FEE QUERY MODULE
16.1 database/fee_queries.py
Responsibility

Database operations for financial/fee functionality.

Known areas include:

Student fees
Fee payments
Fee-related reporting
Fee concessions
Financial information

This module is used by more than one role.

Known consumers include:

Admin
Student
Principal-related functionality

depending on the current implementation.

Risk
CRITICAL

because financial data is involved.

Rule

Do not create a second fee ledger or parallel payment data model.

17. HOD QUERY MODULE
17.1 database/hod_queries.py
Responsibility

Database operations for HOD functionality.

Known areas:

Department analytics
Faculty workload
Subject performance
Student performance
Teacher leave
Department statistics

Related router:

routers/hod.py
Risk
HIGH
Main security concern

Department scope.

A query must not unintentionally expose data belonging to another department.

18. HR QUERY MODULE
18.1 database/hr_queries.py
Responsibility

Database operations for HR and payroll functionality.

Known areas:

Employees
Payroll
Salary components
Salary revisions
Employee exits
HR dashboard

Related router:

routers/hr.py

Related templates:

templates/hr/
Risk
CRITICAL / HIGH

because HR and payroll information is sensitive.

19. PRINCIPAL QUERY MODULE
19.1 database/principal_queries.py
Responsibility

Database operations for Principal-level functionality.

Known current areas include:

College statistics
Department analysis
Principal dashboard
Principal AI context
Principal approvals
Principal financial overview
Complaint overview

Related router:

routers/principal.py

Related templates:

templates/principal/
Risk
HIGH
Important rule

Principal queries must not duplicate authoritative systems already owned by:

admin_queries.py
fee_queries.py
hod_queries.py
hr_queries.py
campus_queries.py
docs_queries.py

Where existing query functionality is authoritative, reuse it where appropriate.

20. PROFILE QUERY MODULE
20.1 database/profile_queries.py
Responsibility

Profile-related database operations.

Potential entities include:

users
students
teachers

Related router:

routers/profile.py
Risk
MEDIUM / HIGH

Profile data can affect identity and account information.

21. STUDENT QUERY MODULE
21.1 database/student_queries.py
Responsibility

Student-side database operations.

Known areas include:

Student profile
Attendance
Marks
Results
Notices
Complaints
Career
Resume analysis
Student dashboard

Related router:

routers/student.py
Risk
CRITICAL / HIGH

Student academic records are sensitive and authoritative.

22. TEACHER QUERY MODULE
22.1 database/teacher_queries.py
Responsibility

Teacher-side academic operations.

Known functions/features documented for this module include areas such as:

Teacher identity
Subjects
Students for attendance
Existing attendance
Attendance records
Existing marks
Marks records
Leave
Teacher dashboard

Important academic records include:

Attendance
Marks

These affect academic reporting.

Risk
CRITICAL

when modifying attendance or marks logic.

23. USER QUERY MODULE
23.1 database/user_queries.py
Responsibility

Core user identity operations.

Known operations include:

create_user
get_user_by_email

Primary database entity:

users

Authentication flow:

login.py
     ↓
user_queries.py
     ↓
users
Risk
CRITICAL

Changes can affect authentication and role handling.

24. AUTHENTICATION ROUTER
24.1 routers/login.py
Responsibility

Authentication entry point.

Related components:

database/user_queries.py
utils/auth.py
utils/session.py
utils/password.py
users

Investigate this file when changing:

Login
Authentication
Password verification
Token generation
Session behavior
Inactive-user behavior
Role redirects
Logout
Risk
CRITICAL
25. ADMIN ROUTER
25.1 routers/admin.py
Responsibility

Administrative HTTP endpoints and workflows.

Major areas:

Users
Students
Teachers
Departments
Subjects
Timetable
Notices
Events
Complaints
Fees
Reports
Analytics
Assets
Inventory

Related query modules:

admin_queries.py
fee_queries.py
asset_queries.py
Risk
CRITICAL

because Admin functionality can affect system-wide records.

26. STUDENT ROUTER
26.1 routers/student.py
Responsibility

Student portal endpoints.

Major areas:

Profile
Attendance
Marks
Results
Notices
Events
Complaints
Fees
Career AI
Resume Analysis

Related query modules:

student_queries.py
fee_queries.py

Related AI modules:

ai/career.py
ai/resume.py
Risk
HIGH
27. TEACHER ROUTER
27.1 routers/teacher.py
Responsibility

Teacher portal endpoints.

Major areas:

Subjects
Attendance
Marks
Leave
Dashboard
AI tools
Timetable

Related query module:

teacher_queries.py

Related AI module:

ai/teacher.py
Risk
HIGH / CRITICAL

for academic operations.

28. HOD ROUTER
28.1 routers/hod.py
Responsibility

HOD department-management endpoints.

Major areas:

Department analytics
Faculty workload
Subject performance
Student performance
Leave management
Marks verification
Dashboard

Related query module:

hod_queries.py
Risk
HIGH
Primary security concern

Cross-department data exposure.

29. PRINCIPAL ROUTER
29.1 routers/principal.py
Responsibility

Principal-level endpoints.

Current known areas:

Principal Dashboard
College Statistics
Department Analysis
Result Approval
Fee Concession Approval
Notice Approval
Sensitive Complaints
Principal AI Assistant

Related query module:

principal_queries.py

Related AI module:

ai/principal.py

Related templates:

templates/principal/
Risk
HIGH

This router is a primary integration point for the future Principal Command Center.

30. PROFILE ROUTER
30.1 routers/profile.py
Responsibility

Profile-related endpoints.

Related query module:

profile_queries.py

Potential entities:

users
students
teachers
Risk
MEDIUM / HIGH

Profile changes can affect identity information.

31. ASSET ROUTER
31.1 routers/asset.py
Responsibility

Asset and inventory-related HTTP operations.

Related query module:

asset_queries.py

Related templates are primarily under:

templates/admin/

Known operational areas include:

Assets
Asset details
Inventory
Maintenance
Disposals
Stock requests
Risk
HIGH
32. CAMPUS ROUTER
32.1 routers/campus.py
Responsibility

Campus operations.

Known areas:

Campus dashboard
Hostel
Library
Transport
Visitors

Related query module:

campus_queries.py

Related templates:

templates/campus/
Risk
HIGH
33. HR ROUTER
33.1 routers/hr.py
Responsibility

HR and payroll functionality.

Known areas:

Employees
Payroll
Salary components
Salary revisions
Exits
HR dashboard

Related query module:

hr_queries.py

Related templates:

templates/hr/
Risk
CRITICAL / HIGH

because salary and employee information is sensitive.

34. DOCUMENTS ROUTER
34.1 routers/docs.py
Responsibility

Institutional document and compliance functionality.

Known areas:

Document repository
Compliance
Meetings
Action items
Document dashboard

Related query module:

docs_queries.py

Related templates:

templates/docs/
Risk
HIGH
35. AI MODULES

The project currently contains:

ai/
│
├── career.py
├── principal.py
├── resume.py
└── teacher.py

These modules represent feature-specific AI functionality.

AI modules should not be assumed to have direct authority over the database.

Their exact integration should always be verified through:

Router
Query layer
AI module
Prompt/context construction
Output handling
36. CAREER AI
36.1 ai/career.py
Responsibility

Student career recommendation functionality.

Related area:

Student portal

Potential database dependency:

career_recommendations

Conceptual flow:

Student Profile
       ↓
Career AI
       ↓
Recommendation
       ↓
Student Query Layer
       ↓
Database
Risk
MEDIUM / HIGH
37. RESUME AI
37.1 ai/resume.py
Responsibility

Resume analysis.

Related areas:

Student portal
Resume upload
Resume analysis

Potential database area:

resume_analysis

Potential file storage:

static/uploads/

The exact storage path must be verified from current source before modifying upload behavior.

Risk
HIGH

especially for file handling and user data.

38. TEACHER AI
38.1 ai/teacher.py
Responsibility

Teacher-oriented AI functionality.

Related router:

routers/teacher.py

Related UI:

templates/teacher/ai_tools.html

Before modifying this module, inspect:

Router caller
Query dependencies
Prompt construction
Input data
Output handling
Template usage
Risk
MEDIUM / HIGH
39. PRINCIPAL AI
39.1 ai/principal.py
Responsibility

Principal-oriented AI functionality.

Related router:

routers/principal.py

Related template:

templates/principal/ai_assistant.html

The current Principal AI should be treated as an existing feature that will later evolve toward the planned Principal Multi-Agent architecture.

Important future rule

The AI must remain an interface/orchestration layer.

It must not bypass:

Authentication
Authorization
Business Rules
Database Validation
Audit
Risk
HIGH

for future action-taking functionality.

40. AUTHENTICATION UTILITY
40.1 utils/auth.py
Responsibility

Authentication and authorization support.

Related areas:

JWT
Authentication
Role checking
Protected routes
RoleChecker

Related components:

routers
login.py
session.py
Risk
CRITICAL

Do not modify without tracing all callers.

41. SESSION UTILITY
41.1 utils/session.py
Responsibility

Authenticated-state/session support.

Related areas:

Access token
Authenticated user
Protected requests
Session state
Risk
CRITICAL

A session change can affect every protected role.

42. PASSWORD UTILITY
42.1 utils/password.py
Responsibility

Password handling.

Potential responsibilities:

Password hashing
Password verification
Password helpers

The exact implementation must be verified from current source.

Risk
CRITICAL

Never introduce a second password mechanism without inspecting the existing implementation.

43. GRADE UTILITY
43.1 utils/grade.py
Responsibility

Grade calculation.

Known related area:

Student marks/results

Potential consumer:

student_queries.py
Risk
MEDIUM / HIGH

Changing grade logic can affect academic reporting.

44. PDF GENERATOR
44.1 utils/pdf_generator.py
Responsibility

PDF report generation.

Potential consumers include:

Student reports
Administrative reports
Academic reports
Other reporting features

Exact consumers must be verified before modification.

Risk
MEDIUM
45. TEMPLATE ARCHITECTURE

The project uses Jinja2 templates.

Primary shared templates:

templates/base.html
templates/index.html
templates/login.html
templates/profile.html

Role-specific template directories:

templates/admin/
templates/principal/
templates/hod/
templates/teacher/
templates/student/

Additional operational template groups:

templates/campus/
templates/hr/
templates/docs/
46. SHARED BASE TEMPLATE
46.1 templates/base.html
Responsibility

Shared UI foundation.

Potential responsibilities include:

Common HTML structure
Shared navigation
Common CSS references
Shared scripts
Global layout
Risk
MEDIUM / HIGH

because a shared template can affect multiple roles.

Before modifying:

Search all template inheritance/usage.
47. LOGIN TEMPLATE
47.1 templates/login.html
Responsibility

Login user interface.

Related backend:

routers/login.py
utils/auth.py
utils/password.py
utils/session.py
Risk
MEDIUM

The visual layer must not be mistaken for the authentication security boundary.

48. PROFILE TEMPLATE
48.1 templates/profile.html
Responsibility

Profile UI.

Related backend:

routers/profile.py
database/profile_queries.py

Potential impact:

Users
Students
Teachers
Profile identity
Risk
MEDIUM / HIGH
49. ADMIN TEMPLATE DIRECTORY
templates/admin/

Contains administrative interfaces including:

Dashboard
Departments
Students
Teachers
Subjects
Timetable
Fees
Notices
Complaints
Results
Revaluation
Users
Assets
Inventory
Maintenance
Disposals
Stock Requests
Finance Reports
Reports
Report Preview

Representative files:

admin_layout.html
dashboard.html
departments.html
department_details.html
students.html
student_profile.html
teachers.html
teacher_profile.html
subjects.html
subject_profile.html
timetable.html
fees.html
notices.html
complaints.html
results.html
revaluation.html
users.html
assets.html
asset_details.html
inventory.html
maintenance.html
disposals.html
stock_requests.html
finance_reports.html
reports.html
report_preview.html
Risk

Varies by feature.

Administrative templates must not be treated as the authorization boundary.

50. PRINCIPAL TEMPLATE DIRECTORY
templates/principal/

Current known files:

ai_assistant.html
concessions.html
dashboard.html
notice_approvals.html
principal_layout.html
results_approval.html
sensitive_complaints.html

These represent the current Principal portal baseline.

The future Principal Command Center should extend this area rather than creating a second Principal portal unnecessarily.

51. HOD TEMPLATE DIRECTORY
templates/hod/

Known files:

dashboard.html
hod_layout.html
leaves.html
marks_verification.html

These support HOD department-level functionality.

52. TEACHER TEMPLATE DIRECTORY
templates/teacher/

Known files:

ai_tools.html
attendance.html
dashboard.html
leaves.html
marks.html
teacher_layout.html
timetable.html

These support Teacher operations.

53. STUDENT TEMPLATE DIRECTORY
templates/student/

Known files:

attendance_report.html
career.html
complaints.html
dashboard.html
fees.html
marks.html
notices.html
placement.html
result.html
student_layout.html
timetable.html

These support Student portal functionality.

54. CAMPUS TEMPLATE DIRECTORY
templates/campus/

Known files:

dashboard.html
hostel_applications.html
hostel_rooms.html
library.html
transport.html
visitors.html

These correspond to campus operational features.

55. HR TEMPLATE DIRECTORY
templates/hr/

Known files:

dashboard.html
employees.html
exits.html
payroll.html
salary_components.html
salary_revisions.html

These support HR/payroll functionality.

56. DOCUMENT TEMPLATE DIRECTORY
templates/docs/

Known files:

action_items.html
compliance.html
dashboard.html
meetings.html
repository.html

These support:

Documents
Compliance
Meetings
Action Items
57. STATIC ASSETS

The static directory contains:

static/
│
├── css/
│
├── images/
│
└── uploads/

Static files can be shared by multiple roles and modules.

Therefore changes to shared assets require dependency tracing.

58. GLOBAL CSS
58.1 static/css/style.css
Responsibility

Global application styling.

Potential consumers:

Multiple templates
Role dashboards
Shared layouts
Login page
Profile page
Risk
LOW / MEDIUM

unless the CSS affects security-sensitive UI or interactive behavior.

Before major modifications:

Search all templates referencing the stylesheet.
59. STATIC IMAGES

Known images include:

static/images/default.png
static/images/SGI_Campus.jpg
static/images/sgi_login.png
static/images/user_1.jpeg
static/images/user_1.jpg
static/images/user_6.jpeg

These are presentation assets.

Do not assume an image filename indicates application functionality.

60. UPLOAD STORAGE

Known upload areas include:

static/uploads/

with:

static/uploads/qrcodes/
static/uploads/resume_4.pdf

The project also contains:

private_uploads/docs/

with institutional documents.

File handling should be treated carefully.

Before changing upload behavior inspect:

File validation
Storage path
File naming
Authorization
Download endpoints
Database references
Template links
61. PRIVATE DOCUMENT STORAGE

Known private document storage:

private_uploads/docs/

Known documents include:

aicte_2023.pdf
policy_2024.pdf

These should not automatically be exposed as public static assets.

When modifying document handling, verify:

Authentication
Authorization
File access
Download route
Storage path
62. QR CODE GENERATION
62.1 generate_qrcodes.py
Responsibility

QR-code generation related to institutional assets/visitors.

Known generated QR examples include:

SGI-ELE-0001.png
SGI-FUR-0001.png
SGI-FUR-0002.png
SGI-IT-0001.png
SGI-IT-0002.png
SGI-IT-0003.png
SGI-LAB-0001.png
visitor_VSR003.png

Before modifying:

Trace asset/visitor database references
Trace file generation
Trace UI usage
63. DOCUMENT GENERATION
63.1 generate_doc_files.py

This is a project-level utility associated with document generation.

Before modifying it, inspect:

Who invokes it?
What documents does it generate?
Where are the generated files stored?
Are generated files referenced by the application?

Do not assume it is part of the runtime request path.

64. USER CREATION SCRIPTS

The project contains:

create_admin.py
create_hod.py
create_principal.py

These are administrative/bootstrap scripts for creating users of specific roles.

Important rule

They must remain consistent with:

users.role
authentication
password handling
department assignment

Do not introduce new role values through these scripts without updating the complete authorization architecture.

65. AI AGENT FILE INVESTIGATION PROCEDURE

When an AI coding agent receives a requirement, it should follow:

                    REQUIREMENT
                         │
                         ▼
                 Identify Feature
                         │
                         ▼
                 Find Likely Router
                         │
                         ▼
                Find Query Module
                         │
                         ▼
              Identify Database Tables
                         │
                         ▼
                Inspect Actual Source
                         │
                         ▼
             Trace Imported Utilities
                         │
                         ▼
              Inspect AI Dependencies
                         │
                         ▼
                Inspect Templates
                         │
                         ▼
                Inspect Static Assets
                         │
                         ▼
                 Trace All Consumers
                         │
                         ▼
                    IMPLEMENT
66. FILE INVESTIGATION ORDER

For a normal feature request:

1. Relevant router
2. Relevant query module
3. Database schema
4. Relevant utility
5. AI module if applicable
6. Relevant template
7. Relevant JavaScript/static assets
8. Related callers
9. Related consumers
10. Tests

Do not modify the first file found without dependency tracing.

67. EXAMPLE — ATTENDANCE CHANGE

Requirement:

"Change how attendance is calculated."

Investigate:

teacher_queries.py
student_queries.py
attendance-related database tables
teacher.py
student.py
teacher templates
student templates

Determine whether the request concerns:

Record storage
Attendance aggregation
Percentage calculation
Display
Reporting

Only then should implementation begin.

68. EXAMPLE — PAYMENT CHANGE

Requirement:

"Add a new online payment status."

Investigate:

fee_queries.py
fee-related tables
payment transaction tables
student fees
fee payments
payment audit structures if present
admin.py
student.py
fee UI

Do not change only an ENUM or status field.

Application logic may depend on existing status values.

69. EXAMPLE — NEW USER ROLE

Requirement:

"Add Accountant role."

Required investigation:

users.role
login.py
user_queries.py
utils/auth.py
utils/session.py
RoleChecker usage
All role comparisons
Navigation
Templates
Profile handling
admin.py

Search the entire project for:

Admin
Student
Teacher
HOD
Principal
role

A role is not merely a database ENUM value.

70. EXAMPLE — STUDENT PROFILE FIELD

Requirement:

"Add LinkedIn URL to student profile."

Potential investigation:

database schema
students
profile_queries.py
student_queries.py
profile.py
student.py
profile.html
student templates

Determine whether the change requires:

Database
Query
Backend
Frontend
Validation

All affected layers should be updated consistently.

71. EXAMPLE — CAREER AI CHANGE

Requirement:

"Add more information to career recommendations."

Investigate:

student.py
student_queries.py
ai/career.py
career recommendation data
student profile retrieval
student templates

Determine whether the change affects:

AI input
Prompt
AI output
Database storage
Database retrieval
UI rendering
72. EXAMPLE — RESUME FEATURE CHANGE

Requirement:

"Allow another resume format."

Investigate:

student.py
ai/resume.py
student_queries.py
resume analysis
upload handling
file validation
file storage
student templates

Do not assume changing AI parsing is sufficient.

73. FILE CREATION RULE

When implementing a new feature:

Prefer extending the existing responsible module when the architecture already provides a suitable location.

Do not create:

new_service.py
new_manager.py
new_helper.py
new_database_layer.py

merely to solve a small requirement.

A new file is justified only when:

Existing ownership is insufficient
The feature has a genuinely separate responsibility
The architecture benefits from separation
The change has been reviewed
74. FILE RENAMING RULE

Renaming an existing file is a high-impact change if it is imported elsewhere.

Before renaming:

Search imports
Search references
Search startup references
Search documentation references
Search tests
Search deployment configuration

Only rename after confirming all consumers.

75. FUNCTION MOVEMENT RULE

Moving a function between modules can break imports and architectural ownership.

Before moving a function:

Search callers
Search imports
Search route usage
Search tests
Search cross-module references

Prefer minimal modification when possible.

76. QUERY MODULE RULE

Database operations should remain within the existing query-layer architecture unless there is a strong project-level reason to change the architecture.

Current architecture:

Router
   ↓
Query Module
   ↓
PyMySQL
   ↓
MySQL

Do not introduce an ORM or second database abstraction merely for a small feature.

77. ROUTER RULE

Routers should remain responsible for:

Request handling
Response handling
Authentication/authorization integration
Feature routing
Template rendering

Database operations should remain in query modules when that is the established architecture.

Do not move large SQL blocks into routers unnecessarily.

78. AI MODULE RULE

AI-specific reasoning should remain within the relevant AI module structure.

Current examples:

Career  → ai/career.py
Resume  → ai/resume.py
Teacher → ai/teacher.py
Principal → ai/principal.py

Do not duplicate AI prompts across unrelated routers unless explicitly required.

For the future Principal Multi-Agent system, AI orchestration should be introduced without bypassing the existing backend authorization layer.

79. UTILITY RULE

Shared behavior should reuse existing utilities.

Examples:

Password → utils/password.py
Auth     → utils/auth.py
Session  → utils/session.py
Grades   → utils/grade.py
PDF      → utils/pdf_generator.py

Do not create duplicate helpers without first checking existing utilities.

80. TEMPLATE RULE

When modifying UI:

Identify exact template
        ↓
Identify route rendering it
        ↓
Identify backend data
        ↓
Identify shared base template
        ↓
Identify CSS/static dependencies

Do not assume a template is standalone.

81. STATIC FILE RULE

Before modifying a shared CSS or JavaScript/static asset:

Search all templates
Search all layouts
Search all references

A shared asset can affect multiple role dashboards.

82. DATABASE SCHEMA CHANGE RULE

A database schema change must be treated as a cross-layer change.

Potential impact:

Database schema
      ↓
Query module
      ↓
Router
      ↓
Template
      ↓
Reports
      ↓
AI context
      ↓
Authorization
      ↓
Tests

Do not make isolated schema modifications without tracing application dependencies.

83. FILE DEPENDENCY INVESTIGATION

For every important file, determine:

Who imports it?
What does it import?
Which router calls it?
Which database tables does it use?
Which templates consume its output?
Which utilities does it call?
Which AI modules does it call?
Which other features depend on it?

This creates a dependency graph instead of a filename-only catalog.

84. FILE CATALOG MAINTENANCE

This document must be updated when:

A source file is added
A source file is removed
A source file is renamed
A feature moves between modules
A router changes ownership
A query module changes ownership
A new AI module is introduced
A utility becomes shared
A major dependency changes
A new operational module is introduced

Documentation should evolve with the project.

85. UNKNOWN FILE RULE

If a requirement refers to a file not listed here:

DO NOT ASSUME THE FILE DOES NOT EXIST.

Search the actual project tree.

Similarly, if a documented file cannot be found:

DO NOT CREATE A REPLACEMENT IMMEDIATELY.

First determine whether:

The file was renamed
The architecture changed
The file is nested elsewhere
The documentation is stale
86. SOURCE SEARCH RULE

For unknown functionality, search by:

Filename
Function name
Route path
HTML title
Database table
SQL keyword
Feature name
Role name

Example:

For placement functionality search:

placement
company
application
companies
placement_applications

Search both:

Source
Templates
87. FILE RISK CLASSIFICATION
CRITICAL
main.py
login.py

utils/auth.py
utils/session.py
utils/password.py

database/connection.py
database/user_queries.py
database/admin_queries.py
database/fee_queries.py

routers/admin.py

Potential impact:

Authentication
Authorization
Financial records
System-wide behavior
User management
HIGH
routers/student.py
routers/teacher.py
routers/hod.py
routers/principal.py
routers/profile.py
routers/hr.py
routers/campus.py
routers/docs.py
routers/asset.py

database/student_queries.py
database/teacher_queries.py
database/hod_queries.py
database/principal_queries.py
database/profile_queries.py
database/hr_queries.py
database/campus_queries.py
database/docs_queries.py
database/asset_queries.py

ai/resume.py
ai/principal.py

Potential impact:

Academic records
Sensitive user data
Institutional records
HR/payroll
Principal operations
Documents
MEDIUM / HIGH
ai/career.py
ai/teacher.py
utils/grade.py

Potential impact:

AI-generated information
Academic calculations
Teacher workflows
Student recommendations
MEDIUM
utils/pdf_generator.py
templates/base.html
templates/profile.html
templates/login.html

These may affect multiple features.

LOWER RISK

Generally:

static/css/style.css
static/images/*

unless the asset participates in:

Security-sensitive UI
Interactive controls
Authorization-related presentation
88. AI FILE CATALOG RULE

The AI coding agent should use this document as:

MAP

not:

SOURCE CODE

Correct workflow:

FILE CATALOG
     ↓
Identify Candidate Files
     ↓
Open Actual Files
     ↓
Verify Implementation
     ↓
Trace Dependencies
     ↓
Modify Required Areas

Never implement based only on filenames.

89. FINAL NO-GUESS RULE

The AI must never invent a file because a feature "should" have one.

For example:

Feature exists

does not prove:

feature_service.py exists

Similarly:

Database table exists

does not prove:

feature_router.py exists

And:

AI module exists

does not prove:

AI module is connected to a router

Always verify.

90. FINAL FILE INVESTIGATION PRINCIPLE

When a requirement arrives, the AI should think:

WHAT FEATURE?
      ↓
WHICH ROUTER?
      ↓
WHICH QUERY MODULE?
      ↓
WHICH DATABASE TABLE?
      ↓
WHICH UTILITY?
      ↓
WHICH AI MODULE?
      ↓
WHICH TEMPLATE?
      ↓
WHICH STATIC ASSET?
      ↓
WHO ELSE DEPENDS ON IT?

Only after completing this chain should implementation begin.

91. PRINCIPAL COMMAND CENTER FILE INVESTIGATION

For the future Principal Command Center, the initial investigation should focus on:

routers/principal.py
database/principal_queries.py
ai/principal.py
templates/principal/

Then trace shared dependencies:

utils/auth.py
utils/session.py
database/fee_queries.py
database/hr_queries.py
database/campus_queries.py
database/docs_queries.py
database/asset_queries.py
database/admin_queries.py

The purpose is to extend existing functionality rather than create duplicate institutional systems.

92. PRINCIPAL DASHBOARD FILE DIRECTION

The existing Principal dashboard should be upgraded rather than duplicated.

Primary current files:

routers/principal.py
database/principal_queries.py
templates/principal/dashboard.html

Future Executive Dashboard functionality may include:

Executive KPI Overview
Academic Health
Student & Faculty Overview
Department Performance
Financial Health
Approval & Pending Actions
Campus Operations Overview
Compliance & Document Health
Institutional Alerts
Today's Priorities

These are planned Principal Command Center capabilities.

They must use authoritative existing data.

93. MULTI-AGENT AI FILE DIRECTION

The planned Multi-Agent architecture should not immediately result in arbitrary new files.

First inspect:

ai/principal.py
routers/principal.py
database/principal_queries.py
requirements.txt

Then determine whether existing AI architecture can be extended or whether a new package structure is justified.

Potential future technologies include:

LangGraph
LangChain
CrewAI

but their addition must be based on an actual implementation requirement.

Do not add multiple AI frameworks merely because they are available.

94. AI TOOL FILE PRINCIPLE

Future Principal AI tools should call authorized backend operations.

Preferred:

Principal
   ↓
Principal AI
   ↓
Agent
   ↓
Tool
   ↓
Existing Backend Operation
   ↓
Authorization
   ↓
Business Validation
   ↓
Database
   ↓
Audit

Avoid:

Principal
   ↓
AI
   ↓
Arbitrary SQL
   ↓
Database

The AI must not become an unrestricted database client.

95. DOCUMENTATION SEQUENCE

The current documentation sequence is:

01_PROJECT_OVERVIEW.md     COMPLETE
02_ARCHITECTURE.md         COMPLETE
03_DATABASE_SCHEMA.md      COMPLETE
04_FEATURE_MAP.md          COMPLETE
05_AUTH_AND_ROLES.md       COMPLETE
06_FILE_CATALOG.md         CURRENT
07_VOLUME_1_BASELINE.md    NEXT
96. FINAL PROJECT FILE AUTHORITY

For implementation decisions, the authority hierarchy is:

                    ACTUAL SOURCE CODE
                           │
                           ▼
                   ACTUAL DATABASE
                           │
                           ▼
                  CURRENT RUNTIME
                           │
                           ▼
                    DOCUMENTATION
                           │
                           ▼
                     AI ASSUMPTION

The lower a source is in this hierarchy, the less it should be trusted when it conflicts with a higher-authority source.

In particular:

AI assumption

must never override:

Actual source code

or:

Actual database schema
97. FINAL OPERATING PRINCIPLE

The purpose of this catalog is to prevent random file modification.

The AI coding agent should follow:

PROJECT OVERVIEW
        ↓
ARCHITECTURE
        ↓
DATABASE SCHEMA
        ↓
FEATURE MAP
        ↓
AUTH & ROLES
        ↓
FILE CATALOG
        ↓
ACTUAL SOURCE CODE
        ↓
ACTUAL DATABASE
        ↓
IMPLEMENTATION
        ↓
TESTING

The final authority is always:

ACTUAL PROJECT SOURCE
+
ACTUAL DATABASE SCHEMA
+
CURRENT RUNTIME BEHAVIOR

Documentation provides structured context.

It does not replace source-code verification.