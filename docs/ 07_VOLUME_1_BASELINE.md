# SGI COMMAND CENTER — VOLUME 1 BASELINE

**Document:** `07_VOLUME_1_BASELINE.md`  
**Project:** SGI Command Center  
**Documentation Volume:** Volume 2  
**Purpose:** Preserve the known baseline state of the existing SGI Command Center before future feature changes.  
**Audience:** AI coding agents, maintainers, developers, reviewers

---

# 01. PURPOSE OF THIS DOCUMENT

This document defines the known baseline state of the SGI Command Center.

The purpose is to give an AI agent a stable understanding of:

- what the existing system already does,
- how major modules currently interact,
- what behavior must be preserved,
- which database entities already exist,
- which role-based workflows exist,
- which AI capabilities already exist,
- which areas are sensitive,
- and what must be verified from source code before making changes.

This document is intended to prevent an AI agent from treating an existing feature as a new feature.

---

# 02. BASELINE PRINCIPLE

The SGI Command Center is an existing application.

Future requirements should normally be interpreted as:

```text
MODIFY EXISTING SYSTEM

rather than:

BUILD A NEW SYSTEM

unless the requirement explicitly asks for a new subsystem.

The AI must first understand the existing implementation before introducing new files, functions, routes, tables, or architectural patterns.

03. CURRENT SYSTEM CHARACTER

The known application architecture consists of:

FastAPI
    +
Jinja2 templates
    +
MySQL
    +
PyMySQL
    +
JWT/session-based authentication
    +
Role-based access
    +
Role-specific routers
    +
Query modules
    +
AI modules
    +
Utility modules

The application is organized around role-specific functionality for:

Student
Teacher
HOD
Principal
Admin
04. CURRENT ROLE MODEL

The database defines these application roles:

Student
Teacher
HOD
Principal
Admin

The central identity table is:

users

A user record contains the role and can optionally be associated with a department.

Students and teachers have additional role-specific records:

users
   |
   +---- students
   |
   +---- teachers

The system therefore separates:

Authentication identity

from:

Role-specific profile data
05. CURRENT USER IDENTITY MODEL

The central user table contains:

user_id
full_name
email
mobile
password
role
department_id
status
profile_image
created_at

The email field is unique.

The role is restricted to:

Student
Teacher
HOD
Principal
Admin

The account status is:

Active
Inactive

Student records are linked to users through:

students.user_id

Teacher records are linked through:

teachers.user_id
06. CURRENT DEPARTMENT MODEL

The system has a central:

departments

table.

Department records contain:

department_id
department_name
hod_name
created_at

Users can be associated with departments.

This department relationship is important for:

HOD scope
Student scope
Teacher scope
Subjects
Timetable
Department analytics
07. CURRENT STUDENT MODEL

The student entity contains:

student_id
user_id
enrollment_no
semester
section
cgpa
skills
interests
preferred_domain
dream_salary

The student record is connected to:

users
departments
subjects
attendance
marks
results
complaints
fees
career recommendations
resume analysis

The student profile is therefore both:

Academic data

and:

AI input/context
08. CURRENT TEACHER MODEL

The teacher entity contains:

teacher_id
user_id
designation
qualification
experience

Teachers are connected to:

subjects
attendance
marks
leave_requests
timetable
feedback

Teacher-specific functionality is handled through the teacher router and teacher query module.

09. CURRENT SUBJECT MODEL

The subject entity contains:

subject_id
subject_name
subject_code
semester
department_id
teacher_id
credits
subject_type
classes_per_week
status

Supported subject types include:

Theory
Practical
Lab

Subjects may be associated with:

department
teacher
students
attendance
marks
assignments
timetable
10. CURRENT ATTENDANCE SYSTEM

Attendance is stored in:

attendance

The main identity of an attendance record is based on:

student
subject
date

The table also records:

teacher_id
status
marked_at

Supported attendance states are:

Present
Absent

The database prevents duplicate attendance for the same:

student
subject
attendance_date

combination.

11. CURRENT ATTENDANCE SUMMARY

The database contains a view:

attendance_summary

The view provides:

student_id
subject_name
total_classes
present
absent
percentage

The percentage is calculated from present classes divided by total classes.

The view groups attendance using:

student_id
subject_name

It is not a physical table.

12. CURRENT MARKS SYSTEM

Marks are stored in:

marks

A marks record contains:

student_id
subject_id
teacher_id
exam_type
maximum_marks
obtained_marks
remarks
created_at
updated_at

Supported exam types include:

Assignment
Quiz
Mid-1
Mid-2
Practical
Internal
Final

The database prevents duplicate records for the same:

student
subject
exam_type

combination.

13. CURRENT RESULT SYSTEM

Final/semester results are stored in:

results

The result contains:

student_id
semester
total_marks
obtained_marks
percentage
sgpa
cgpa
grade
status
published_at
created_at

Result status is:

Draft
Published

A student can have only one result record for a given:

student_id
semester

combination according to the current unique constraint.

14. CURRENT GRADE CALCULATION

The project contains:

utils/grade.py

which is responsible for grade-related calculation logic.

The student query layer uses the grade utility when academic result/grade information is calculated.

AI agents must inspect the existing grade utility before introducing new grade logic.

Do not duplicate grade calculation rules in routers or templates.

15. CURRENT ASSIGNMENT SYSTEM

The database contains:

assignments
assignment_submissions

Assignments are associated with:

subject
teacher

An assignment contains:

title
description
due_date
created_at

Student submissions contain:

assignment_id
student_id
file_path
submission_date
marks
remarks

Before modifying assignment functionality, the actual current router/template implementation must be verified.

16. CURRENT PLACEMENT SYSTEM

The database contains:

companies
placement_applications

Company records contain:

company_name
location
package
eligibility_cgpa
required_skills
website

Placement applications associate:

student
company
status

Supported application states are:

Applied
Shortlisted
Interview
Selected
Rejected

Before modifying placement functionality, inspect the actual source implementation because the database presence alone does not prove that every possible UI workflow is currently active.

17. CURRENT CAREER AI SYSTEM

The application contains:

ai/career.py

for career recommendation functionality.

Student-specific AI context is retrieved through:

student_queries.py

The student profile can provide AI-relevant information such as:

CGPA
skills
interests
preferred domain
dream salary

Career recommendations are persisted in:

career_recommendations

Stored information includes:

recommended_career
recommended_courses
required_skills
suggested_companies
full_response
generated_on

The full AI response is stored as part of the recommendation record.

18. CURRENT RESUME AI SYSTEM

The application contains:

ai/resume.py

for resume analysis.

Student resume analysis is persisted in:

resume_analysis

Stored information includes:

resume_file
ats_score
missing_skills
improvements
recommended_companies
full_response
analyzed_on

Resume-related files may use the application's upload area.

Before modifying resume functionality, inspect:

upload handling
file validation
storage path
AI parsing
database persistence
retrieval
UI rendering

Do not assume the exact implementation from the database schema alone.

19. CURRENT TEACHER AI

The project contains:

ai/teacher.py

for teacher-oriented AI functionality.

The exact current input, prompt, output, and calling route must be verified from source code before modifying the teacher AI subsystem.

Do not infer implementation details merely from the filename.

20. CURRENT PRINCIPAL AI

The project contains:

ai/principal.py

for principal-oriented AI functionality.

Principal-specific database context is prepared through:

principal_queries.py

The known context includes college-level information such as:

departments
students
teachers
fees
complaints

The exact AI prompt and output contract must be verified from the source before modification.

21. CURRENT NOTICE SYSTEM

The database contains:

notices

A notice contains:

notice_id
title
description
posted_by
posted_on

Notices are associated with the user who posted them.

Student-facing notice retrieval is supported through:

student_queries.py

Administrative notice management is associated with:

admin_queries.py
22. CURRENT EVENT SYSTEM

The database contains:

events

Event information includes:

event_name
description
event_date
venue

Student-facing upcoming events are retrieved through:

student_queries.py

Administrative event operations are associated with:

admin_queries.py
23. CURRENT COMPLAINT SYSTEM

The system contains:

complaints

A complaint contains:

student_id
category
complaint
status
created_at
resolved_at

Supported complaint statuses are:

Pending
In Progress
Resolved

Student functionality includes:

submit complaint
view complaints

The query layer also implements a complaint eligibility/cooldown check.

The exact UI behavior must be verified from the current router/templates.

24. CURRENT LEAVE SYSTEM

Teacher leave requests are stored in:

leave_requests

A leave request contains:

teacher_id
leave_type
from_date
to_date
reason
status

Supported statuses are:

Pending
Approved
Rejected

Teachers can submit/view leave requests.

HOD functionality includes:

view department leaves
update leave status

Department scoping is important.

25. CURRENT TIMETABLE SYSTEM

The database contains:

rooms
time_slots
timetable
teacher_availability

The timetable connects:

department
semester
section
subject
teacher
room
slot
day
academic year

Timetable status is:

Draft
Published

The admin query layer contains timetable generation logic.

Known conflict checks include:

teacher conflict
room conflict
class conflict
teacher availability

Before changing timetable generation, inspect the complete existing query implementation.

26. CURRENT FEE SYSTEM

The project contains a dedicated fee query module:

fee_queries.py

The fee subsystem contains:

fee_structure
student_fees
fee_payments
payment_transactions
payment_audit

This is one of the most sensitive parts of the application.

27. CURRENT FEE STRUCTURE

Fee structure records contain:

department_id
course
semester
admission_fee
tuition_fee
examination_fee
lab_fee
library_fee
other_fee
total_fee
academic_year
status

Supported status:

Active
Inactive
28. CURRENT STUDENT FEE ASSIGNMENT

Student fee records are stored in:

student_fees

They contain:

student_id
fee_structure_id
total_fee
discount
scholarship
payable_fee
due_date
status

Supported status:

Pending
Partial
Paid
29. CURRENT FEE PAYMENT SYSTEM

Actual fee payments are stored in:

fee_payments

Payment information includes:

receipt_number
payment_date
payment_mode
amount_paid
transaction_id
remarks
collected_by

Supported payment modes include:

Cash
UPI
Card
Bank Transfer
Cheque
30. CURRENT ONLINE PAYMENT TRANSACTION SYSTEM

Online/simulated payment processing uses:

payment_transactions

The transaction contains:

payment_reference
student_fee_id
gateway
payment_mode
gateway_transaction_id
amount
payment_status
gateway_response
created_at
updated_at

Supported payment states are:

Pending
Success
Failed
Refunded

The current query layer supports a transaction lifecycle involving:

Create pending transaction
        ↓
Verify transaction
        ↓
Update transaction
        ↓
Create payment record
        ↓
Recalculate student fee status
        ↓
Create audit records

This flow must not be casually rewritten.

31. CURRENT PAYMENT AUDIT SYSTEM

Payment-specific auditing is stored in:

payment_audit

Audit records contain:

transaction_id
action
performed_by
action_time
remarks

Known payment actions include events such as:

Created
Gateway Success
Receipt Generated

The exact action vocabulary should be verified from the current query source before introducing new values.

32. CURRENT GENERAL AUDIT SYSTEM

The database also contains:

audit_logs

with:

user_id
action
log_time

This is distinct from:

payment_audit

Do not merge the two concepts without explicit architectural justification.

33. CURRENT LOGIN HISTORY

The database contains:

login_history

which records:

user_id
login_time
ip_address
device

This should be treated as security/audit data.

34. CURRENT FEEDBACK SYSTEM

The database contains:

feedback

with:

student_id
teacher_id
rating
comments
created_at

The current schema does not define a database-level range check for rating.

Application behavior should therefore be verified before assuming allowed rating values.

35. CURRENT PROFILE SYSTEM

Profile functionality is distributed across:

profile.py
profile_queries.py
profile.html

The profile query layer contains:

get_full_profile
update_basic_info
update_student_info
update_teacher_info

Profile data spans:

users
students
teachers
36. CURRENT DATABASE CONNECTION BEHAVIOR

The project uses:

PyMySQL

The database connection uses:

DictCursor
autocommit=True

The connection function reads configuration from:

config.py

A failed connection is handled by the connection module.

Some query functions temporarily control transaction behavior where multi-step operations require it.

Do not assume every query runs inside an explicit transaction.

Inspect the specific function.

37. CURRENT USER CREATION FLOW

User creation is handled through the user/query and administrative layers.

Known behavior includes duplicate checks around identity information.

Student creation additionally checks enrollment uniqueness.

Teacher/student creation can involve multiple database inserts:

users
    ↓
student/teacher profile

Such multi-step operations use transactional handling where implemented.

Before changing user creation:

inspect user_queries.py
inspect admin_queries.py
inspect password handling
inspect role validation
inspect database constraints
38. CURRENT STUDENT CREATION MODEL

Student creation involves both:

users

and:

students

The student record references the created user.

Known duplicate checks include:

email
enrollment number

The exact validation rules should be taken from the current implementation.

39. CURRENT TEACHER CREATION MODEL

Teacher creation involves:

users

and:

teachers

Duplicate email checks are part of the current teacher creation flow.

The teacher profile is linked to the central user identity.

40. CURRENT ADMIN DASHBOARD

The admin query layer provides dashboard statistics.

Known statistics include counts related to:

students
teachers
departments
active users

Additional admin analytics include areas such as:

fee payments
complaints
published results

The exact dashboard presentation should be verified in the current admin templates.

41. CURRENT TEACHER DASHBOARD

Teacher dashboard statistics include information related to:

active subjects
current timetable classes
students associated with teacher subjects

The current teacher query layer calculates these statistics.

Do not assume dashboard values are stored directly in a dashboard table.

They are derived from existing academic/timetable data.

42. CURRENT HOD DASHBOARD / ANALYTICS

HOD analytics include:

department statistics
top performers
weak students
department leaves
subject performance
faculty workload

HOD scope is derived from the authenticated user's department relationship.

43. CURRENT PRINCIPAL DASHBOARD / ANALYTICS

Principal analytics operate at college level.

Known functionality includes:

college statistics
department-wise analysis
principal AI context

Unlike HOD analytics, principal functionality is not limited to a single department by default.

The exact authorization logic must still be verified in the current router.

44. CURRENT STUDENT PORTAL

Known student capabilities include:

Profile
Attendance
Marks
Results
Notices
Events
Complaints
Fees
Career recommendations
Resume analysis

Some database features may exist without complete UI exposure.

Therefore:

Database existence
        ≠
Fully implemented frontend feature
45. CURRENT TEACHER PORTAL

Known teacher capabilities include:

Dashboard
Subjects
Attendance
Marks
Leave requests

Teacher actions are constrained by the teacher identity and subject relationships.

46. CURRENT HOD PORTAL

Known HOD capabilities include:

Department dashboard
Student performance
Subject performance
Faculty workload
Leave management

The HOD is department-scoped.

47. CURRENT PRINCIPAL PORTAL

Known Principal capabilities include:

College dashboard
Department analysis
College-level analytics
Principal AI

The principal operates at a broader organizational scope than HOD.

48. CURRENT ADMIN PORTAL

Known administrative capabilities include areas such as:

User management
Student management
Teacher management
Department management
Subject management
Timetable management
Notice management
Event management
Complaint management
Fee management
Reports
Analytics

Admin is the broadest operational role in the current role model.

49. CURRENT AUTHENTICATION BASELINE

The application uses authentication utilities involving:

utils/auth.py
utils/session.py
utils/password.py

JWT-based authentication is part of the known architecture.

The authenticated token is associated with the application session/authentication flow.

The exact token creation, decoding, expiry, cookie, and header behavior must be verified from the current source before changing authentication.

50. CURRENT AUTHORIZATION BASELINE

Authorization is role-aware.

Known roles:

Student
Teacher
HOD
Principal
Admin

The project uses role-checking logic and manual role checks in relevant places.

The AI must not rely on frontend visibility as authorization.

Authorization must be enforced server-side.

51. CURRENT DEPARTMENT-SCOPE BASELINE

Department-level scoping is especially important for:

HOD
Students
Teachers
Subjects
Timetable
Academic analytics

An HOD should not automatically gain access to another department's records merely because the records exist in the same database.

Before modifying HOD functionality:

verify authenticated user
verify department_id
verify query filters
verify router authorization
52. CURRENT DATA FLOW MODEL

The application generally follows this conceptual flow:

Browser
   ↓
Router
   ↓
Query / AI module
   ↓
Database / AI provider
   ↓
Query / AI result
   ↓
Router
   ↓
Template / response
   ↓
Browser

Not every feature necessarily follows exactly the same path.

The actual source code is authoritative.

53. CURRENT AI DATA FLOW

For student career functionality, the known conceptual flow is:

Authenticated Student
        ↓
Student Profile
        ↓
AI Context
        ↓
Career AI
        ↓
Generated Recommendation
        ↓
Database Persistence
        ↓
Student Retrieval

For resume functionality:

Resume Upload
        ↓
Resume Analysis
        ↓
AI Processing
        ↓
Analysis Result
        ↓
Database Persistence
        ↓
Student Retrieval

The exact implementation should be verified from source.

54. CURRENT DATABASE ACCESS PATTERN

The application does not use an ORM as its known database abstraction.

Database access is handled through query modules using SQL/PyMySQL.

The established pattern is:

Router
   ↓
Query module
   ↓
get_connection()
   ↓
cursor
   ↓
SQL

Future feature work should follow this pattern unless there is an explicit architectural decision to change it.

55. CURRENT DATABASE TRANSACTION PATTERN

The global connection uses:

autocommit=True

However, multi-step operations can temporarily disable autocommit and use explicit commit/rollback behavior.

Examples include operations such as:

student creation
teacher creation
payment verification

Before changing such operations, inspect the complete function.

Do not introduce partial commits into a multi-step operation without understanding its current transaction behavior.

56. CURRENT ERROR-HANDLING BASELINE

Different query functions have different error-handling behavior.

Therefore:

Do not assume a single global error-handling strategy.

Some functions:

return data

Some:

return None

Some:

return False

Some:

catch exceptions

Some operations explicitly rollback transactions.

Before changing error behavior, inspect the exact caller expectations.

57. CURRENT DATA VALIDATION BASELINE

Validation exists at the application layer in addition to database constraints.

Examples include:

duplicate email checks
duplicate enrollment checks
role restrictions
status checks
business-rule checks

Database constraints also provide:

PRIMARY KEY
UNIQUE
FOREIGN KEY
ENUM
NOT NULL
DEFAULT

The AI should not assume that database constraints replace application validation.

Both layers may matter.

58. CURRENT DATABASE CONSTRAINT BASELINE

Important uniqueness rules include:

users.email
departments.department_name
students.enrollment_no
subjects.subject_code
rooms.room_number
fee_payments.receipt_number
payment_transactions.payment_reference

Relationship constraints exist between major entities.

The complete schema is documented in:

03_DATABASE_SCHEMA.md

That document should be consulted before modifying database-related features.

59. CURRENT ACADEMIC DATA FLOW

The academic chain can be understood as:

Department
    ↓
Subject
    ↓
Teacher
    ↓
Student
    ↓
Attendance
    ↓
Marks
    ↓
Results

Additional academic entities include:

Assignments
Assignment submissions
Timetable
Teacher availability
60. CURRENT FINANCIAL DATA FLOW

The financial chain can be understood as:

Department
      ↓
Fee Structure
      ↓
Student Fee
      ↓
Payment Transaction
      ↓
Fee Payment
      ↓
Audit

The system also tracks:

discount
scholarship
payable fee
due date
payment status
61. CURRENT AI DATA FLOW

The AI-related data chain includes:

Student Profile
       ↓
AI Context
       ↓
Career Recommendation
       ↓
career_recommendations

and:

Student Resume
       ↓
Resume AI
       ↓
resume_analysis

Principal AI uses college-level context.

Teacher AI uses teacher-oriented context.

62. CURRENT REPORTING BASELINE

The system contains PDF-generation support:

utils/pdf_generator.py

The exact report types and callers must be verified from source before modifying report generation.

Do not assume every database entity already has a PDF report.

63. CURRENT STATIC/UPLOAD BASELINE

Known static structure:

static/
├── css/
├── images/
└── uploads/

Known stylesheet:

static/css/style.css

Uploads should be treated as untrusted external data.

Before changing upload behavior, verify:

file validation
file naming
storage
database path
access control
64. CURRENT TEMPLATE BASELINE

Known shared templates include:

base.html
index.html
login.html
profile.html

Role-specific template directories include:

admin/
hod/
principal/
student/
teacher/

Individual template filenames should be discovered from the current project source rather than inferred.

65. CURRENT SYSTEM FEATURE MATRIX
Feature	Main Role	Main Backend Area	Database
Login	All	login.py, auth utilities	users
User management	Admin	admin.py	users
Departments	Admin	admin_queries.py	departments
Students	Admin/Student	admin/student query modules	students
Teachers	Admin/Teacher	admin/teacher query modules	teachers
Subjects	Admin/Teacher	admin/teacher query modules	subjects
Attendance	Teacher/Student	teacher/student query modules	attendance
Marks	Teacher/Student	teacher/student query modules	marks
Results	Student/Admin	student/admin query modules	results
Assignments	Student/Teacher	verify current source	assignments, assignment_submissions
Placements	Student/Admin	verify current source	companies, placement_applications
Career AI	Student	ai/career.py	career_recommendations
Resume AI	Student	ai/resume.py	resume_analysis
Teacher AI	Teacher	ai/teacher.py	verify current source
Principal AI	Principal	ai/principal.py	verify current source
Notices	Admin/Student	admin/student query modules	notices
Events	Admin/Student	admin/student query modules	events
Complaints	Student/Admin	student/admin query modules	complaints
Teacher Leave	Teacher/HOD	teacher/HOD query modules	leave_requests
Timetable	Admin/Teacher/Student	admin/teacher query modules	timetable
Fees	Admin/Student	fee_queries.py	fee/payment tables
Payments	Admin/Student	fee_queries.py	payment tables
Profile	All	profile_queries.py	users, students, teachers
Login history	System	auth/login flow	login_history
Audit logs	System/Admin	verify current callers	audit_logs
Feedback	Student/Teacher	verify current source	feedback
PDF reports	Various	utils/pdf_generator.py	verify callers
66. CURRENT HIGH-RISK AREAS

The following areas require extra caution:

Authentication
Authorization
Role handling
Password handling
Department scoping
Student academic records
Attendance
Marks
Results
Fees
Online payments
Payment verification
Audit logs
Resume uploads
AI-generated data persistence

These areas should not be modified based on assumptions.

67. CURRENT FEATURES THAT REQUIRE SOURCE VERIFICATION

The following database-backed capabilities should not automatically be considered fully implemented merely because their tables exist:

Assignments
Placement workflows
Feedback workflows
Login history presentation
Audit-log presentation
Some report workflows
Some timetable UI workflows
Some AI UI workflows

Before modifying these areas:

Search actual router
Search query module
Search templates
Search references
68. BASELINE PRESERVATION RULE

Unless the requirement explicitly changes behavior, preserve:

Existing routes
Existing database structures
Existing role values
Existing query interfaces
Existing function names
Existing template contracts
Existing authentication behavior
Existing status values
Existing transaction behavior
Existing AI persistence behavior
69. CHANGE IMPACT RULE

Every requirement should be classified as one of:

UI-only
Backend-only
Database-only
AI-only
Cross-layer
Security-sensitive
Financial
Academic-data-sensitive

Examples:

Change button text
→ UI-only
Change attendance calculation
→ Cross-layer / academic-sensitive
Add payment status
→ Database + backend + UI / financial-sensitive
Change role
→ Security-sensitive
Change career recommendation format
→ AI + persistence + UI
70. AI INVESTIGATION BASELINE

When a new requirement arrives, the AI should follow:

STEP 1
Understand the requested behavior.

STEP 2
Identify the affected feature.

STEP 3
Read 04_FEATURE_MAP.md.

STEP 4
Read relevant section of 03_DATABASE_SCHEMA.md.

STEP 5
Read relevant section of 05_AUTH_AND_ROLES.md if authorization is involved.

STEP 6
Use 06_FILE_CATALOG.md to identify candidate files.

STEP 7
Open the actual source files.

STEP 8
Trace callers and dependencies.

STEP 9
Determine the smallest safe change.

STEP 10
Implement.

STEP 11
Verify existing behavior.

STEP 12
Update documentation if architecture or behavior changed.
71. NO-GUESS BASELINE

The AI must never infer an implementation merely because:

a table exists
a filename exists
a feature is described
a router name suggests a behavior
a template directory exists

For example:

companies table exists

does not prove:

placement UI is complete

Likewise:

ai/teacher.py exists

does not prove:

teacher.py router calls it

The AI must verify actual source references.

72. EXISTING FUNCTIONALITY MUST NOT BE DUPLICATED

Before creating a new function, search for existing functionality.

Examples:

Need authentication
→ inspect utils/auth.py
Need password handling
→ inspect utils/password.py
Need student ID
→ inspect student_queries.py
Need grade calculation
→ inspect utils/grade.py
Need fee transaction
→ inspect fee_queries.py
Need profile update
→ inspect profile_queries.py

Reuse existing behavior where appropriate.

73. EXISTING DATABASE QUERIES MUST NOT BE DUPLICATED

Before writing a new SQL query:

Search relevant query module.

If the required query already exists:

reuse or safely extend it.

Do not create multiple competing versions of the same database operation.

74. EXISTING AUTHORIZATION MUST NOT BE BYPASSED

A new route must not rely only on:

hidden button
hidden page
frontend restriction
JavaScript condition

Server-side authorization must remain authoritative.

75. EXISTING DATABASE CONSTRAINTS MUST BE RESPECTED

Before inserting or updating data, check:

PRIMARY KEY
UNIQUE
FOREIGN KEY
ENUM
NOT NULL
DEFAULT

The AI must not silently design around a database constraint without understanding why it exists.

76. EXISTING STATUS VALUES MUST BE PRESERVED

Important status sets include:

User
Active / Inactive
Attendance
Present / Absent
Result
Draft / Published
Fee
Pending / Partial / Paid
Payment
Pending / Success / Failed / Refunded
Complaint
Pending / In Progress / Resolved
Leave
Pending / Approved / Rejected
Placement
Applied / Shortlisted / Interview / Selected / Rejected
Timetable
Draft / Published

If a new status is required, identify all code paths using the existing status values before changing the model.

77. CURRENT DATABASE SOURCE OF TRUTH

The authoritative schema documentation is:

03_DATABASE_SCHEMA.md

The underlying SQL schema is authoritative over this baseline.

The current schema contains:

30 tables
+
1 view

The known view is:

attendance_summary
78. CURRENT ARCHITECTURAL SOURCE OF TRUTH

The architectural reference is:

02_ARCHITECTURE.md

Use it to understand:

application layers
router organization
query organization
AI modules
utilities
templates
authentication

Then verify the actual source before making implementation decisions.

79. CURRENT FEATURE SOURCE OF TRUTH

The feature reference is:

04_FEATURE_MAP.md

Use it to locate:

feature
router
query module
database
AI module
utility

Then verify actual code.

80. CURRENT SECURITY SOURCE OF TRUTH

The authentication and authorization reference is:

05_AUTH_AND_ROLES.md

Use it whenever the requirement touches:

login
role
permission
user identity
department scope
session
JWT
password
protected route
81. CURRENT FILE NAVIGATION SOURCE OF TRUTH

The file navigation reference is:

06_FILE_CATALOG.md

Use it to identify likely files before opening source code.

Do not treat it as a substitute for source verification.

82. BASELINE VS ACTUAL SOURCE

The AI must maintain this distinction:

DOCUMENTATION
    =
structured understanding
SOURCE CODE
    =
actual implementation
DATABASE
    =
actual persistence contract
RUNTIME
    =
actual executed behavior

When these disagree:

Runtime/source/schema evidence
        >
documentation assumptions
83. BASELINE UPDATE POLICY

This document should be updated whenever a major change modifies the known system baseline.

Examples:

New role
New major module
New database subsystem
New AI module
Authentication redesign
Payment architecture change
Major academic workflow change
Major timetable redesign
Major frontend architecture change

Small implementation changes do not necessarily require rewriting this document.

84. WHAT THIS DOCUMENT MUST NOT BECOME

Do not turn this document into:

full source code
full SQL dump
full API documentation
full template documentation
full AI prompt repository

Those belong in their respective source/documentation layers.

This file is the:

CURRENT BASELINE
85. BASELINE SUMMARY

The SGI Command Center currently consists of a role-based institutional management system covering:

Authentication
Users
Departments
Students
Teachers
Subjects
Attendance
Marks
Results
Assignments
Placements
Career AI
Resume AI
Teacher AI
Principal AI
Notices
Events
Complaints
Teacher Leave
Timetable
Fees
Payments
Profiles
Auditing
Feedback
Reporting

The system is backed by MySQL and accessed through PyMySQL query modules.

The application uses FastAPI-style routing, role-based authentication/authorization, server-rendered templates, utility modules, and separate AI modules.

86. FINAL BASELINE STATEMENT

The SGI Command Center should be treated as an existing integrated system.

Future AI agents must:

UNDERSTAND
    ↓
LOCATE
    ↓
VERIFY
    ↓
TRACE
    ↓
MODIFY
    ↓
TEST

and must not:

GUESS
    ↓
CREATE RANDOM FILE
    ↓
DUPLICATE LOGIC
    ↓
BREAK EXISTING BEHAVIOR

The complete project context is distributed across:

01_PROJECT_OVERVIEW.md
02_ARCHITECTURE.md
03_DATABASE_SCHEMA.md
04_FEATURE_MAP.md
05_AUTH_AND_ROLES.md
06_FILE_CATALOG.md
07_VOLUME_1_BASELINE.md

Together, these documents provide the AI with the project's:

Business context
Architecture
Database model
Feature map
Security model
File navigation
Current baseline

However, these documents remain a navigation and reasoning layer.

The actual project source code remains the final implementation authority.