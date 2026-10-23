# SGI Command Center — Feature Map

**Project:** SGI Command Center  
**Document:** 04_FEATURE_MAP.md  
**Document Type:** Current-State Feature Inventory + Planned Principal Expansion  
**Status:** Baseline Documentation  
**Last Updated:** 2026-10-05

---

## 1. Document Purpose

This document provides a structured map of the functionality currently present in the SGI Command Center project.

It is intended to answer:

- What features currently exist?
- Which role owns or uses each feature?
- Where is the feature implemented?
- Which backend/query/template area supports it?
- Which features belong to the Principal portal?
- Which features are planned for the Principal Command Center?
- Which features are operational versus executive?
- Which features should be reused instead of duplicated?

This document distinguishes clearly between:

```text
CURRENT

and:

PLANNED / FUTURE

A planned feature must never be treated as implemented until it is actually present in the repository and verified.

2. Feature Map Legend

The following terminology is used throughout this document.

CURRENT

Feature exists in the current project and is represented by the repository structure and/or implementation.

EXISTING SUPPORT

A feature/domain exists elsewhere in the system and can potentially support another module.

PLANNED

Feature is part of the future development direction but is not necessarily implemented yet.

FUTURE AI

Feature is intended to be exposed through the planned Principal AI/Multi-Agent architecture.

3. High-Level Feature Architecture

The current ERP can be divided into these major functional domains:

SGI COMMAND CENTER
│
├── Authentication & User Access
│
├── Administrator
│
├── Principal
│
├── HOD
│
├── Teacher
│
├── Student
│
├── HR & Payroll
│
├── Asset & Inventory
│
├── Campus Operations
│
├── Documents & Compliance
│
├── Reports & PDFs
│
├── AI Capabilities
│
└── Testing / Quality
4. Current Role Map

The current application contains these primary roles:

Administrator
Principal
HOD
Teacher
Student

Conceptually:

                    SGI COMMAND CENTER
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
       ▼                   ▼                   ▼
 Administrator          Principal            HOD
       │                   │                   │
       ▼                   ▼                   ▼
   Management          Oversight           Department
       │                   │               Academic
       │                   │
       └──────────┬────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
     Teacher              Student

The actual permission boundary must be determined from the current authorization implementation.

5. Authentication & Access Features
5.1 Login

Status: CURRENT

Relevant area:

routers/login.py
templates/login.html

Purpose:

Authenticate users
Establish authenticated application context
Route users into authorized areas
5.2 Session Management

Status: CURRENT

Relevant files:

utils/session.py

Purpose:

Maintain authenticated session context
Support protected application requests
5.3 Authentication Utilities

Status: CURRENT

Relevant file:

utils/auth.py

Purpose:

Authentication/authorization support
Protected route handling

The exact implementation must remain aligned with the source code.

5.4 Password Management

Status: CURRENT

Relevant file:

utils/password.py

Purpose:

Password hashing/verification support
Secure credential handling
6. Administrator Feature Map

Administrator functionality is primarily represented through:

routers/admin.py
database/admin_queries.py
templates/admin/

The Admin portal currently covers a broad range of institutional management operations.

6.1 Administrator Dashboard

Status: CURRENT

File:

templates/admin/dashboard.html

Purpose:

Administrative overview
Institutional management summary
7. Department Management

Status: CURRENT

Relevant templates:

templates/admin/departments.html
templates/admin/department_details.html

Relevant backend:

routers/admin.py
database/admin_queries.py

Capabilities include:

Department listing
Department details
Department-related management

The exact fields and operations are determined by the existing implementation.

8. Student Management

Status: CURRENT

Relevant templates:

templates/admin/students.html
templates/admin/student_profile.html

Relevant query areas include student-related database operations.

Capabilities include:

Student listing
Student details/profile
Administrative student management

Student records remain an authoritative institutional data domain.

9. Teacher Management

Status: CURRENT

Relevant templates:

templates/admin/teachers.html
templates/admin/teacher_profile.html

Capabilities include:

Teacher listing
Teacher profile/details
Administrative faculty management
10. Subject Management

Status: CURRENT

Relevant templates:

templates/admin/subjects.html
templates/admin/subject_profile.html

Capabilities include:

Subject management
Subject details
Academic master-data management
11. Timetable Management

Status: CURRENT

Relevant template:

templates/admin/timetable.html

Purpose:

Administrative timetable management
Timetable visibility/configuration

The exact workflow must be verified from the implementation.

12. Fee Management

Status: CURRENT

Relevant template:

templates/admin/fees.html

Relevant query module:

database/fee_queries.py

Purpose:

Fee-related administrative operations
Financial record visibility
Fee management

The existing fee system remains the authoritative financial source.

13. Notice Management

Status: CURRENT

Relevant template:

templates/admin/notices.html

Purpose:

Notice management
Institutional communication

Principal notice approval is handled separately within the Principal portal.

14. Complaint Management

Status: CURRENT

Relevant template:

templates/admin/complaints.html

Purpose:

Administrative complaint management

Complaint access must remain permission/scope controlled because complaints can contain sensitive information.

15. Result Management

Status: CURRENT

Relevant template:

templates/admin/results.html

Purpose:

Result-related administrative functionality

Academic authority must not be inferred solely from the existence of an Admin result page.

16. Revaluation

Status: CURRENT

Relevant template:

templates/admin/revaluation.html

Purpose:

Revaluation-related academic operation

Exact authority and workflow must be verified from the backend.

17. User Management

Status: CURRENT

Relevant template:

templates/admin/users.html

Relevant query module:

database/user_queries.py

Purpose:

User/account management
User-related administrative functionality

Security-sensitive actions must be controlled by appropriate permissions.

18. Asset Management

Status: CURRENT

Relevant templates:

templates/admin/assets.html
templates/admin/asset_details.html

Relevant backend:

routers/asset.py
database/asset_queries.py

Capabilities include:

Asset records
Asset details
Asset management
19. Inventory Management

Status: CURRENT

Relevant template:

templates/admin/inventory.html

Purpose:

Inventory management
Stock visibility/operations
20. Maintenance Management

Status: CURRENT

Relevant template:

templates/admin/maintenance.html

Purpose:

Asset/inventory maintenance-related functionality
21. Asset Disposal

Status: CURRENT

Relevant template:

templates/admin/disposals.html

Purpose:

Asset disposal-related functionality
22. Stock Requests

Status: CURRENT

Relevant template:

templates/admin/stock_requests.html

Purpose:

Stock request management
Inventory workflow
23. Finance Reports

Status: CURRENT

Relevant template:

templates/admin/finance_reports.html

Purpose:

Financial reporting
Administrative financial analysis
24. General Reports

Status: CURRENT

Relevant templates:

templates/admin/reports.html
templates/admin/report_preview.html

Purpose:

Report generation
Report preview
Institutional data reporting
25. Principal Feature Map

Current Principal functionality is organized through:

routers/principal.py
database/principal_queries.py
ai/principal.py
templates/principal/

Current Principal templates:

templates/principal/
├── ai_assistant.html
├── concessions.html
├── dashboard.html
├── notice_approvals.html
├── principal_layout.html
├── results_approval.html
└── sensitive_complaints.html
26. Principal Dashboard

Status: CURRENT

File:

templates/principal/dashboard.html

Purpose:

Principal-level institutional overview
Executive statistics currently supported by the implementation

The existing dashboard should be upgraded rather than replaced blindly.

The future Executive Dashboard should build upon existing authoritative queries and data.

27. Principal Result Approval

Status: CURRENT

File:

templates/principal/results_approval.html

Purpose:

Review result-related approval requests
Approve/reject according to the existing workflow

This is an approval-sensitive operation.

Future AI access must use the same backend authorization and business rules.

28. Principal Fee Concession

Status: CURRENT

File:

templates/principal/concessions.html

Purpose:

Review/process fee concession requests

This is a financially sensitive operation.

Any future AI-driven execution must require appropriate validation and confirmation.

29. Principal Notice Approval

Status: CURRENT

File:

templates/principal/notice_approvals.html

Purpose:

Review and process notice approvals

The existing notice data remains authoritative.

30. Principal Sensitive Complaints

Status: CURRENT

File:

templates/principal/sensitive_complaints.html

Purpose:

Principal-level access to sensitive complaint information

Because complaints may contain confidential information, this module requires strong backend authorization.

31. Principal AI Assistant

Status: CURRENT

Files:

ai/principal.py
templates/principal/ai_assistant.html

Purpose:

Principal-oriented AI interaction
AI-assisted informational functionality

Important distinction:

Current Principal AI
        ≠
Future Principal Multi-Agent System

The future Multi-Agent architecture is a planned expansion.

32. HOD Feature Map

HOD functionality is represented through:

routers/hod.py
database/hod_queries.py
templates/hod/

Current templates:

templates/hod/
├── dashboard.html
├── hod_layout.html
├── leaves.html
└── marks_verification.html
33. HOD Dashboard

Status: CURRENT

File:

templates/hod/dashboard.html

Purpose:

Department-level overview
HOD dashboard

HOD data must remain department-scoped according to authorization.

34. HOD Leave Management

Status: CURRENT

File:

templates/hod/leaves.html

Purpose:

HOD-related leave functionality
35. HOD Marks Verification

Status: CURRENT

File:

templates/hod/marks_verification.html

Purpose:

Marks verification
Academic review at HOD level
36. Teacher Feature Map

Teacher functionality is organized through:

routers/teacher.py
database/teacher_queries.py
templates/teacher/

Current templates:

templates/teacher/
├── ai_tools.html
├── attendance.html
├── dashboard.html
├── leaves.html
├── marks.html
├── teacher_layout.html
└── timetable.html
37. Teacher Dashboard

Status: CURRENT

File:

templates/teacher/dashboard.html

Purpose:

Teacher overview
38. Teacher Attendance

Status: CURRENT

File:

templates/teacher/attendance.html

Purpose:

Attendance-related teacher operations
39. Teacher Marks

Status: CURRENT

File:

templates/teacher/marks.html

Purpose:

Marks-related academic operations
40. Teacher Timetable

Status: CURRENT

File:

templates/teacher/timetable.html

Purpose:

Teacher timetable visibility/operations
41. Teacher Leave

Status: CURRENT

File:

templates/teacher/leaves.html

Purpose:

Teacher leave-related functionality
42. Teacher AI Tools

Status: CURRENT

File:

templates/teacher/ai_tools.html

Backend AI area:

ai/teacher.py

Purpose:

Teacher-facing AI functionality
43. Student Feature Map

Student functionality is organized through:

routers/student.py
database/student_queries.py
templates/student/

Current templates:

templates/student/
├── attendance_report.html
├── career.html
├── complaints.html
├── dashboard.html
├── fees.html
├── marks.html
├── notices.html
├── placement.html
├── result.html
├── student_layout.html
└── timetable.html
44. Student Dashboard

Status: CURRENT

File:

templates/student/dashboard.html

Purpose:

Student overview
Student-facing information
45. Student Attendance Report

Status: CURRENT

File:

templates/student/attendance_report.html

Purpose:

Student attendance visibility
46. Student Fees

Status: CURRENT

File:

templates/student/fees.html

Purpose:

Student fee information
47. Student Marks

Status: CURRENT

File:

templates/student/marks.html

Purpose:

Student marks visibility
48. Student Result

Status: CURRENT

File:

templates/student/result.html

Purpose:

Student result visibility
49. Student Timetable

Status: CURRENT

File:

templates/student/timetable.html

Purpose:

Student timetable visibility
50. Student Notices

Status: CURRENT

File:

templates/student/notices.html

Purpose:

Student-facing institutional notices
51. Student Complaints

Status: CURRENT

File:

templates/student/complaints.html

Purpose:

Student complaint functionality
52. Student Career

Status: CURRENT

File:

templates/student/career.html

Purpose:

Career-related student functionality
53. Student Placement

Status: CURRENT

File:

templates/student/placement.html

Purpose:

Placement-related student functionality
54. Campus Operations Feature Map

Campus functionality is organized through:

routers/campus.py
database/campus_queries.py
templates/campus/

Current templates:

templates/campus/
├── dashboard.html
├── hostel_applications.html
├── hostel_rooms.html
├── library.html
├── transport.html
└── visitors.html
55. Campus Dashboard

Status: CURRENT

File:

templates/campus/dashboard.html

Purpose:

Campus operations overview
56. Hostel Applications

Status: CURRENT

File:

templates/campus/hostel_applications.html

Purpose:

Hostel application management
57. Hostel Rooms

Status: CURRENT

File:

templates/campus/hostel_rooms.html

Purpose:

Hostel room management/visibility
58. Library

Status: CURRENT

File:

templates/campus/library.html

Purpose:

Library-related campus operations
59. Transport

Status: CURRENT

File:

templates/campus/transport.html

Purpose:

Transport-related campus operations
60. Visitors

Status: CURRENT

File:

templates/campus/visitors.html

Purpose:

Visitor management/visibility
61. HR & Payroll Feature Map

HR functionality is organized through:

routers/hr.py
database/hr_queries.py
templates/hr/

Current templates:

templates/hr/
├── dashboard.html
├── employees.html
├── exits.html
├── payroll.html
├── salary_components.html
└── salary_revisions.html
62. HR Dashboard

Status: CURRENT

File:

templates/hr/dashboard.html

Purpose:

HR overview
63. Employee Management

Status: CURRENT

File:

templates/hr/employees.html

Purpose:

Employee management
64. Payroll

Status: CURRENT

File:

templates/hr/payroll.html

Purpose:

Payroll-related operations

Payroll data is sensitive and must be access-controlled.

65. Salary Components

Status: CURRENT

File:

templates/hr/salary_components.html

Purpose:

Salary component management
66. Salary Revisions

Status: CURRENT

File:

templates/hr/salary_revisions.html

Purpose:

Salary revision management
67. Employee Exits

Status: CURRENT

File:

templates/hr/exits.html

Purpose:

Employee exit-related functionality
68. Documents & Compliance Feature Map

Document functionality is organized through:

routers/docs.py
database/docs_queries.py
templates/docs/

Current templates:

templates/docs/
├── action_items.html
├── compliance.html
├── dashboard.html
├── meetings.html
└── repository.html
69. Document Repository

Status: CURRENT

File:

templates/docs/repository.html

Purpose:

Institutional document repository

Private files may be stored under:

private_uploads/docs/
70. Compliance Management

Status: CURRENT

File:

templates/docs/compliance.html

Purpose:

Compliance tracking/management

The exact workflow states must be taken from the implementation.

71. Meetings

Status: CURRENT

File:

templates/docs/meetings.html

Purpose:

Institutional meeting records
72. Action Items

Status: CURRENT

File:

templates/docs/action_items.html

Purpose:

Meeting/action-item tracking
73. Documents Dashboard

Status: CURRENT

File:

templates/docs/dashboard.html

Purpose:

Documents/compliance overview
74. Profile Feature

Status: CURRENT

Relevant files:

routers/profile.py
database/profile_queries.py
templates/profile.html

Purpose:

User profile management
Profile information

Profile functionality must not be used to bypass role-specific authorization.

75. Reporting Feature Map

Reporting functionality exists across the application.

Relevant utility:

utils/pdf_generator.py

Admin reporting templates include:

templates/admin/reports.html
templates/admin/report_preview.html
templates/admin/finance_reports.html

Reporting can aggregate information from multiple domains.

Sensitive reports must respect the user's authorization scope.

76. PDF Generation

Status: CURRENT

Relevant file:

utils/pdf_generator.py

Technology:

ReportLab

Purpose:

PDF/report generation
77. Data Visualization

Status: CURRENT SUPPORT

The project includes:

Matplotlib

This may support reporting/visualization functionality.

Visualization should always be based on authoritative application data.

78. AI Feature Map

Current AI modules:

ai/
├── career.py
├── principal.py
├── resume.py
└── teacher.py

Current AI capabilities are distributed across role/use-case areas.

79. Career AI

Status: CURRENT

File:

ai/career.py

Purpose:

Career-oriented AI functionality

The exact capabilities should be taken from the implementation.

80. Principal AI

Status: CURRENT**

File:

ai/principal.py

UI:

templates/principal/ai_assistant.html

Purpose:

Principal-specific AI functionality

Important:

Current Principal AI

is not equivalent to the planned:

Principal Multi-Agent Command System
81. Resume AI

Status: CURRENT

File:

ai/resume.py

Purpose:

Resume-related AI functionality
82. Teacher AI

Status: CURRENT

File:

ai/teacher.py

UI:

templates/teacher/ai_tools.html

Purpose:

Teacher-oriented AI tools
83. Current Feature Dependency Model

Major features are connected through shared institutional data.

Conceptually:

                    Users
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Students     Teachers     Admin
          │           │           │
          ├──────┬────┘           │
          ▼      ▼                ▼
      Academic  Departments    Management
          │
    ┌─────┼──────┐
    ▼     ▼      ▼
Attendance Marks Results
    │      │      │
    └──────┼──────┘
           ▼
       Principal
       Oversight

Additional domains connect through institutional records:

Students
   ├── Fees
   ├── Hostel
   ├── Library
   ├── Transport
   └── Complaints

The exact physical relationships must be verified from the database.

84. Principal Command Center — Planned Feature Map

The future Principal Command Center is planned as an executive layer on top of the existing ERP.

The current planned major areas are:

1. Executive Dashboard
2. AI Principal Assistant
3. Approval Center
4. Academic Oversight
5. Finance Oversight
6. HR & Payroll Overview
7. Campus Operations
8. Documents & Compliance
9. Meetings & Action Items
10. Notices & Events
11. Sensitive Complaints
12. Reports & Analytics
13. Notifications / Alerts
14. Audit / My Activity
15. My Profile

These represent the planned target structure, not a claim that every item is currently implemented.

85. Planned Module 1 — Executive Dashboard

Status: PLANNED / EXPANSION OF CURRENT DASHBOARD

The existing Principal dashboard should be upgraded into an executive command center.

Target functional areas:

1. Executive KPI Overview
2. Academic Health
3. Student & Faculty Overview
4. Department Performance
5. Financial Health
6. Approval & Pending Actions
7. Campus Operations Overview
8. Compliance & Document Health
9. Institutional Alerts
10. Today's Priorities
86. Executive KPI Overview

Status: PLANNED

Potential KPIs:

Students
Faculty
Departments
Attendance
Fee Collection
Outstanding Fees
Pending Approvals
Complaints

Rules:

Use authoritative existing data.
Do not hardcode values.
Do not create duplicate data stores.
KPI calculations must be traceable.
87. Academic Health

Status: PLANNED

Potential information:

Overall Attendance
Result Performance
Academic Session Status
Department Comparison
Pending Academic Activities
Trends

The system must not label something as:

Poor
Critical
At Risk

unless an approved rule exists.

88. Student & Faculty Overview

Status: PLANNED

Potential information:

Student Total
Student Distribution
Enrollment Trend
Faculty Strength
Faculty Distribution
Designation

Only information available in authoritative data should be displayed.

89. Department Performance

Status: PLANNED

Potential comparisons:

Students
Faculty
Attendance
Result Performance

The dashboard should allow drill-down into detailed Academic Oversight.

90. Financial Health

Status: PLANNED

Potential metrics:

Fee Demand
Collected
Outstanding
Concessions
Collection Rate
Trends

The existing fee system remains authoritative.

91. Approval & Pending Actions

Status: PLANNED / BUILDS ON CURRENT APPROVAL FEATURES

Potential approval areas:

Result Approvals
Fee Concessions
Notice Approvals
Other Authorized Requests

The target is a unified executive approval center.

92. Campus Operations Overview

Status: PLANNED

Potential summaries:

Assets
Inventory
Hostel
Transport
Library
Visitors

Only modules with actual underlying data should be included.

93. Compliance & Document Health

Status: PLANNED / BUILDS ON EXISTING DOCS MODULE

Potential states:

Not Started
In Progress
Under Review
Submitted
Verified / Closed

These labels must be validated against the actual institutional workflow before implementation.

Important:

Submitted ≠ Verified / Closed

unless the actual workflow defines them as equivalent.

94. Institutional Alerts

Status: PLANNED

Potential sources:

Pending Approvals
Compliance Review Due
Overdue Meeting Action
Low Inventory
Document Review Due

Alert severity must come from configured business rules.

95. Today's Priorities

Status: PLANNED

Potential sources:

Result Approvals
Fee Concessions
Compliance Actions
Meeting Action Items
Document Reviews
Operational Issues

The priority list must be generated from real institutional data.

96. Planned Module 2 — AI Principal Assistant

Status: PLANNED EXPANSION

The target is a text-only multilingual AI interface that allows the Principal to interact with authorized ERP functionality using natural language.

The AI should support:

Ask
Analyze
Summarize
Prepare
Recommend
Execute authorized actions
97. Planned Multi-Agent Architecture

Target structure:

Principal
    ↓
Principal Supervisor Agent
    ├── Academic Agent
    ├── Finance Agent
    ├── HR/Payroll Agent
    ├── Campus Operations Agent
    ├── Compliance & Document Agent
    ├── Grievance Agent
    └── Reporting Agent
             ↓
       Action Executor
             ↓
      Existing SGI Backend
             ↓
            MySQL

This is a future architecture.

98. Planned AI Agent Responsibilities
Academic Agent

Potential responsibilities:

Academic summaries
Attendance analysis
Result analysis
Department comparisons
Academic pending items
Finance Agent

Potential responsibilities:

Fee summaries
Collection analysis
Outstanding analysis
Concession information
Financial reports
HR / Payroll Agent

Potential responsibilities:

Faculty overview
Employee summaries
Payroll summaries
HR analytics

Sensitive data must remain authorization-controlled.

Campus Operations Agent

Potential responsibilities:

Hostel summary
Library summary
Transport summary
Visitor summary
Asset/inventory summary
Compliance & Document Agent

Potential responsibilities:

Document summaries
Compliance status
Upcoming reviews
Meeting/action items
Grievance Agent

Potential responsibilities:

Complaint summaries
Pending sensitive complaints
Complaint status analysis

Access must respect complaint sensitivity.

Reporting Agent

Potential responsibilities:

Executive reports
KPI summaries
Cross-domain analysis
PDF/report preparation
99. Planned AI Action Model

AI actions are divided conceptually into:

READ
PREPARE
EXECUTE
READ

Examples:

Show pending approvals.
Show attendance.
Show department performance.
PREPARE

Examples:

Prepare a report.
Draft a notice.
Prepare an approval summary.

No sensitive state change should occur.

EXECUTE

Examples:

Approve result.
Approve concession.
Publish notice.

Sensitive actions require:

Authorization
Validation
Confirmation
Transaction
Audit
100. Manual UI + AI Feature Parity

A critical planned architecture principle is:

Manual UI
      │
      ▼
Shared Business Logic
      ▲
      │
AI Tool

This means:

UI should not implement different business rules from AI.
AI should not bypass UI-level authorization.
Both should eventually call the same authorized backend operations.
101. Planned AI Tool Architecture

Preferred:

AI Agent
   ↓
Controlled Tool
   ↓
Authorized Backend Service
   ↓
Existing Query Layer
   ↓
MySQL

Prohibited:

AI Agent
   ↓
Arbitrary SQL
   ↓
MySQL
102. Planned Human-in-the-Loop

Sensitive operations should require explicit confirmation.

Example:

Principal:
"Approve all pending CSE Semester 5 results."

        ↓

AI:
Finds matching requests

        ↓

AI:
Shows impact and summary

        ↓

Principal:
Confirms

        ↓

Backend:
Revalidates authorization

        ↓

Backend:
Executes transaction

        ↓

Audit:
Records operation

The system must not simulate confirmation.

103. Planned Multilingual AI

Target languages include:

English
Hindi
Hinglish
Gujarati

Pipeline:

User Message
      ↓
Language Detection
      ↓
Intent Detection
      ↓
Structured Task
      ↓
Agent Routing
      ↓
Tool Execution
      ↓
Result
      ↓
Response in User Language

Institutional identifiers and statuses must not be mistranslated.

104. Planned AI Memory

AI may maintain conversation/task context.

However:

AI Memory ≠ Authorization

Memory must never be treated as proof of permission or approval.

105. Planned AI Security

Future AI must defend against:

Prompt Injection
Unauthorized Actions
Data Leakage
IDOR
Arbitrary SQL
Privilege Escalation
Fabricated Results
Tool Misuse

Institutional documents and database content must be treated as data, not system instructions.

106. Planned Approval Center

Status: PLANNED EXPANSION

Target:

Approval Center
├── Result Approvals
├── Fee Concessions
├── Notice Approvals
└── Other Authorized Requests

This should unify existing approval workflows without creating duplicate approval records unnecessarily.

107. Planned Academic Oversight

Status: PLANNED

Potential areas:

Attendance
Results
Department Performance
Academic Trends
Academic Pending Actions

Detailed academic workflows remain within their authoritative modules.

108. Planned Finance Oversight

Status: PLANNED

Potential areas:

Fee Collection
Outstanding
Concessions
Collection Trends
Financial Reports

The existing fee system remains authoritative.

109. Planned HR & Payroll Overview

Status: PLANNED

Potential areas:

Faculty Strength
Employee Overview
Payroll Summary
Salary Trends
HR Pending Items

The Principal should receive only the level of detail permitted by authorization.

110. Planned Campus Operations

Status: PLANNED**

Potential areas:

Hostel
Library
Transport
Visitors
Assets
Inventory
Maintenance

Existing operational modules remain authoritative.

111. Planned Documents & Compliance

Status: PLANNED EXPANSION

Potential areas:

Document Repository
Compliance Status
Document Reviews
Expiry/Review Alerts
Meetings
Action Items

The existing documents module remains the source of truth.

112. Planned Meetings & Action Items

Status: PLANNED EXPANSION

Potential Principal functionality:

View meetings
View decisions
Track action items
View overdue actions

Data should come from the existing documents/meeting system.

113. Planned Notices & Events

Status: PLANNED EXPANSION

Potential Principal functionality:

Review notices
Approve notices
View events
Monitor institutional communication

Existing notice records remain authoritative.

114. Planned Sensitive Complaints

Status: CURRENT + PLANNED EXPANSION

Current:

templates/principal/sensitive_complaints.html

Future enhancements may include:

Better filtering
Status visibility
Priority/urgency based on configured rules
AI-assisted summarization
Executive complaint analytics

AI must not expose sensitive complaint content beyond the user's authorization.

115. Planned Reports & Analytics

Status: PLANNED EXPANSION

Potential areas:

Institutional KPIs
Department comparisons
Academic analytics
Financial analytics
Operational analytics
Compliance analytics
Executive PDF reports

Reports must remain traceable to authoritative data.

116. Planned Notifications / Alerts

Status: PLANNED

Potential notifications:

Approval pending
Document review due
Compliance action due
Meeting action overdue
Operational alert

Severity must be based on configured business rules.

117. Planned Audit / My Activity

Status: PLANNED / VERIFY EXISTING AUDIT SUPPORT FIRST

Potential information:

Principal actions
Approval actions
AI actions
Report generation
Sensitive record access

Before creating a new audit mechanism, the repository must be audited for any existing authoritative audit system.

118. Planned Principal Profile

Status: CURRENT SUPPORT + PLANNED ENHANCEMENT

Existing profile functionality:

routers/profile.py
templates/profile.html

The Principal Command Center can expose profile information through the existing profile architecture.

119. Feature Ownership Matrix

High-level ownership:

Feature Domain	Admin	Principal	HOD	Teacher	Student
User Management	Yes	Scoped/Authorized	No	No	No
Departments	Yes	Oversight	Department Scope	No	View as applicable
Students	Yes	Oversight	Department Scope	Authorized Scope	Self
Teachers	Yes	Oversight	Department Scope	Self	No
Subjects	Yes	Oversight	Department Scope	Authorized	View
Timetable	Yes	Oversight	Department Scope	Own/Authorized	Own
Fees	Yes	Oversight/Approval	As Authorized	No	Own
Results	Existing Admin Capability	Approval/Oversight	Verification	Marks	Own
Attendance	Existing Admin Capability	Oversight	Department Scope	Entry/Management	Own
Complaints	Existing Admin Capability	Sensitive/Authorized	Authorized	Authorized	Own
HR/Payroll	Yes	Oversight	Authorized	No	No
Assets/Inventory	Yes	Oversight	As Authorized	No	No
Campus Operations	Yes	Oversight	As Authorized	No	Limited
Documents/Compliance	Yes	Oversight	As Authorized	No	No
Reports	Yes	Executive	Department	Authorized	Limited
AI	Available in selected areas	Principal AI	HOD-related as implemented	Teacher AI	Career/other AI

This table is a high-level conceptual map.

Actual permissions must be verified from the implemented authorization logic.

120. Feature Boundary Principle

A feature appearing in the Admin interface does not automatically mean:

Admin = unrestricted authority

Similarly:

Principal = unrestricted authority

is also incorrect.

Actual access must be determined through:

Role
+
Permission
+
Scope
+
Business Rules
+
Record State
121. Feature Reuse Principle

Before creating a new feature, search for an existing equivalent.

Example:

If the Principal needs:

Fee Collection Summary

do not create:

Principal Fee Ledger

Instead:

Existing Fee System
       ↓
Authorized Query
       ↓
Principal Summary
122. Feature Duplication to Avoid

The following duplicate systems should not be created:

Principal Student Management System
Principal Fee Ledger
Principal Result Database
Principal Payroll Database
AI Student Database
AI Approval Database
AI Asset Database

unless an actual new persistent entity is required and has been explicitly approved.

123. Feature Development Workflow

For every new feature:

1. Identify requirement
        ↓
2. Audit repository
        ↓
3. Search existing feature
        ↓
4. Search database
        ↓
5. Identify authoritative source
        ↓
6. Identify authorization boundary
        ↓
7. Design
        ↓
8. Implement
        ↓
9. Test
        ↓
10. Update documentation
124. Feature Testing Matrix

Each feature should be tested for:

Functional correctness
Authorization
Data scope
Validation
Error handling
Database integrity
Regression
UI behavior

For AI features additionally:

Intent accuracy
Tool selection
Authorization
Confirmation
Tool failure
Hallucination prevention
Prompt injection resistance
Multilingual response
125. Current Feature Inventory Summary

Current major application areas include:

Authentication
Administrator Portal
Principal Portal
HOD Portal
Teacher Portal
Student Portal
Profile Management
Fees
Academic / Results
Attendance
Departments
Subjects
Timetable
Complaints
Notices
HR / Payroll
Assets / Inventory
Campus Operations
Documents / Compliance
Meetings / Action Items
Reports / PDFs
AI Capabilities
Testing
126. Principal Current-State Summary

Current Principal functionality includes:

Principal Dashboard
Result Approval
Fee Concession
Notice Approval
Sensitive Complaints
Principal AI Assistant
Principal Layout

Primary implementation areas:

routers/principal.py
database/principal_queries.py
ai/principal.py
templates/principal/
127. Principal Target-State Summary

The planned Principal Command Center expands the current portal into:

Executive Dashboard
Approval Center
Academic Oversight
Finance Oversight
HR / Payroll Overview
Campus Operations
Documents / Compliance
Meetings / Action Items
Notices / Events
Sensitive Complaints
Reports / Analytics
Notifications / Alerts
Audit / My Activity
Profile
Multi-Agent AI
128. Planned Principal Module Count

The current target blueprint contains:

15 Major Modules

These are:

1. Executive Dashboard
2. AI Principal Assistant
3. Approval Center
4. Academic Oversight
5. Finance Oversight
6. HR & Payroll Overview
7. Campus Operations
8. Documents & Compliance
9. Meetings & Action Items
10. Notices & Events
11. Sensitive Complaints
12. Reports & Analytics
13. Notifications / Alerts
14. Audit / My Activity
15. My Profile

This is a target architecture and may change after repository/security/database audit.

129. Principal Executive Dashboard Functional Areas

The target Dashboard currently contains:

1. Executive KPI Overview
2. Academic Health
3. Student & Faculty Overview
4. Department Performance
5. Financial Health
6. Approval & Pending Actions
7. Campus Operations Overview
8. Compliance & Document Health
9. Institutional Alerts
10. Today's Priorities

These areas should use existing authoritative data.

130. Feature Status Discipline

Every future development document should clearly distinguish:

CURRENT

from:

PLANNED

and:

PROPOSED

For example:

Principal Result Approval
→ CURRENT

Principal Executive Dashboard expansion
→ PLANNED

Multi-Agent Principal AI
→ PLANNED

Autonomous unrestricted AI SQL
→ NOT ALLOWED
131. Feature Map and Database Relationship

Features must map to authoritative data.

Example:

Feature:
Principal Fee Overview

        ↓

Existing Fee Domain

        ↓

database/fee_queries.py

        ↓

MySQL

        ↓

Principal Dashboard

Not:

Feature
 ↓
New Principal Table
 ↓
Duplicate Data
132. Feature Map and Authorization Relationship

Every protected feature must have an authorization boundary.

Conceptually:

User
 ↓
Authentication
 ↓
Role
 ↓
Permission
 ↓
Scope
 ↓
Feature
 ↓
Data

The UI is not the authorization boundary.

133. Feature Map and AI Relationship

Future AI interaction should follow:

Natural Language
       ↓
Intent
       ↓
Agent
       ↓
Controlled Tool
       ↓
Authorized Backend Operation
       ↓
Existing Feature/Data

AI should not bypass the feature's normal security controls.

134. Feature Map Maintenance

When a feature is added:

Update:
04_FEATURE_MAP.md

When its architecture changes:

Update:
02_ARCHITECTURE.md

When its database changes:

Update:
03_DATABASE_SCHEMA.md

When its permissions change:

Update:
05_AUTH_AND_ROLES.md

When files are added/removed:

Update:
06_FILE_CATALOG.md

When baseline behavior changes:

Update:
07_VOLUME_1_BASELINE.md
135. Feature Development Rules

The following rules are mandatory for future feature work:

Do not duplicate existing functionality.
Do not duplicate authoritative data.
Do not bypass authorization.
Do not invent institutional policies.
Do not create database changes blindly.
Do not allow AI to bypass backend controls.
Do not treat UI visibility as security.
Do not treat AI output as authoritative data.
Do not mark planned functionality as implemented.
Do not break existing working modules.
Test every major feature.
Update documentation after implementation.
136. Final Feature Architecture

The current and future system can be summarized as:

                         SGI COMMAND CENTER
                                │
       ┌────────────────────────┼────────────────────────┐
       │                        │                        │
       ▼                        ▼                        ▼
   Operations              Academic                 Administration
       │                        │                        │
       ▼                        ▼                        ▼
Campus / HR / Assets      Students / Teachers      Users / Fees /
Documents                 Results / Attendance     Departments /
                                                    Reports
       │                        │                        │
       └────────────────────────┼────────────────────────┘
                                ▼
                        Executive Layer
                                │
                                ▼
                     Principal Command Center
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
       Manual UI          Analytics            AI Interface
            │                   │                   │
            └───────────────────┼───────────────────┘
                                ▼
                    Shared Authorized Backend
                                │
                                ▼
                              MySQL
137. Final Feature Principles

The SGI Command Center feature architecture must follow these principles:

Every feature must have a clear functional owner.
Every feature must respect role and permission boundaries.
Existing authoritative modules must be reused.
Principal features should provide executive oversight rather than duplicate operational systems.
AI should extend existing functionality rather than create parallel functionality.
Sensitive actions require backend authorization.
AI execution must use controlled tools/services.
Dashboard metrics must come from real institutional data.
Analytics must not invent institutional policy.
Current and planned features must remain clearly separated.
New features must be tested.
New features must be documented.
Database changes must be deliberate and reviewable.
The system must preserve existing working functionality.
The final authority for implemented behavior remains the actual source code and database.
138. Feature Map Status
Current Feature Areas
Authentication
Administrator
Principal
HOD
Teacher
Student
Profile
Academic
Attendance
Results
Fees
Departments
Subjects
Timetable
Complaints
Notices
HR / Payroll
Assets / Inventory
Campus Operations
Documents / Compliance
Meetings / Action Items
Reports / PDFs
AI
Testing
Principal Expansion
Executive Dashboard
Unified Approval Center
Academic Oversight
Finance Oversight
HR / Payroll Overview
Campus Operations Overview
Compliance Overview
Meetings / Action Items
Notices / Events
Sensitive Complaints
Reports / Analytics
Notifications
Audit / My Activity
Multilingual AI
Multi-Agent AI
Human-in-the-Loop
AI Tool Execution
139. Final Note

The Feature Map is a living document.

Whenever a feature is changed, added, removed, renamed, or moved to another architectural layer, this document should be updated.

The development process should remain:

Requirement
    ↓
Repository Audit
    ↓
Existing Feature Search
    ↓
Existing Database Search
    ↓
Authorization Review
    ↓
Feature Design
    ↓
Implementation
    ↓
Testing
    ↓
Documentation

The objective is to evolve SGI Command Center into a secure, maintainable, enterprise-grade college ERP without creating duplicate systems, bypassing authorization, or losing the integrity of existing institutional data.