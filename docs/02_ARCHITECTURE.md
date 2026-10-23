# SGI Command Center — System Architecture

**Project:** SGI Command Center  
**Document:** 02_ARCHITECTURE.md  
**Document Type:** Current-State Technical Architecture  
**Status:** Baseline Architecture Documentation  
**Last Updated:** 2026-10-05

---

## 1. Document Purpose

This document describes the current technical architecture of the **SGI Command Center** application.

The purpose of this document is to provide a clear architectural reference for:

- Developers
- AI coding agents
- Database developers
- Backend developers
- Frontend developers
- Security reviewers
- System maintainers
- Future feature-development work

This document describes the architecture based on the current project structure and implemented application organization.

Future architectural improvements, including the planned Principal Multi-Agent AI system, are documented separately as proposed/future architecture and must not be treated as already implemented.

---

# 2. System Overview

SGI Command Center is a web-based **College/Campus Management ERP system** built using Python and FastAPI.

The system provides role-based access to different institutional functions for:

- Administrator
- Principal
- HOD
- Teacher
- Student

The application follows a layered web application architecture in which:

```text
User
   ↓
Browser / Web UI
   ↓
FastAPI Application
   ↓
Router Layer
   ↓
Authentication / Authorization
   ↓
Query / Database Layer
   ↓
MySQL Database

Additional application capabilities are integrated into this architecture, including:

FastAPI
├── Authentication
├── Role-based access
├── Role-specific routers
├── Database query modules
├── Jinja2 templates
├── Static assets
├── AI modules
├── PDF/report generation
├── File/document management
└── Automated tests
3. High-Level Architecture

The current system can be represented conceptually as:

                         ┌─────────────────────────┐
                         │        End User         │
                         │                         │
                         │ Admin / Principal /     │
                         │ HOD / Teacher / Student │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │       Web Browser       │
                         │                         │
                         │ HTML / CSS / JS         │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │       FastAPI App       │
                         │        main.py          │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
             ┌────────────┐   ┌────────────┐   ┌────────────┐
             │   Login /  │   │ Role-based │   │  Utility / │
             │    Auth    │   │   Routers  │   │    AI      │
             └────────────┘   └──────┬─────┘   └────────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │ Database Query Layer │
                          │                      │
                          │ *_queries.py         │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │        MySQL         │
                          │      Database        │
                          └──────────────────────┘
4. Application Entry Point

The primary application entry point is:

main.py

This file is responsible for the central FastAPI application setup and application-level routing/configuration.

The architecture should treat main.py as the application composition point rather than placing large amounts of business logic directly inside it.

The general responsibility separation is:

main.py
    ↓
Application initialization
    ↓
Router registration
    ↓
Request routing
    ↓
Role-specific router
5. Backend Framework

The backend framework is:

FastAPI

FastAPI provides:

HTTP request handling
Routing
Dependency support
Web application structure
API/web endpoint implementation
Integration with authentication and application services

The current application is primarily used as a server-rendered web application using Jinja2 templates, while FastAPI provides the backend routing and request-processing layer.

6. Server-Side Rendering

The project uses:

Jinja2

for server-rendered HTML pages.

Templates are organized under:

templates/

The architecture follows:

Browser Request
      ↓
FastAPI Router
      ↓
Database Query
      ↓
Python Data
      ↓
Jinja2 Template
      ↓
HTML Response
      ↓
Browser

For example:

Principal Dashboard Request
        ↓
routers/principal.py
        ↓
database/principal_queries.py
        ↓
templates/principal/dashboard.html
7. Router Architecture

The application separates major functional areas through FastAPI router modules.

Current router structure:

routers/
├── admin.py
├── asset.py
├── campus.py
├── docs.py
├── hod.py
├── hr.py
├── login.py
├── principal.py
├── profile.py
├── student.py
└── teacher.py

Each router represents a major application area.

Conceptually:

routers/
│
├── login.py
│      └── Authentication-related routes
│
├── admin.py
│      └── Administrator functionality
│
├── principal.py
│      └── Principal functionality
│
├── hod.py
│      └── HOD functionality
│
├── teacher.py
│      └── Teacher functionality
│
├── student.py
│      └── Student functionality
│
├── profile.py
│      └── Profile functionality
│
├── asset.py
│      └── Asset / inventory functionality
│
├── campus.py
│      └── Campus operations
│
├── hr.py
│      └── HR / payroll functionality
│
└── docs.py
       └── Documents / compliance functionality
8. Router Responsibility

Routers should primarily be responsible for:

Receiving HTTP requests
Reading request parameters/form data
Authentication/authorization checks
Calling the appropriate query/business functionality
Handling request-level validation
Selecting the correct template
Returning the appropriate response

Routers should not become a dumping ground for:

Large SQL statements
Complex database logic
Repeated business rules
AI reasoning
Unrelated functionality

Where existing query modules already contain the relevant database operation, the router should reuse them rather than duplicating the SQL.

9. Database Query Layer

Database-related logic is organized under:

database/

Current structure:

database/
├── admin_queries.py
├── asset_queries.py
├── campus_queries.py
├── connection.py
├── database.sql
├── docs_queries.py
├── fee_queries.py
├── hod_queries.py
├── hr_queries.py
├── principal_queries.py
├── profile_queries.py
├── student_queries.py
├── teacher_queries.py
└── user_queries.py

The architecture separates database operations from the presentation layer.

Typical flow:

Router
   ↓
Query Function
   ↓
MySQL Connection
   ↓
SQL Query
   ↓
Database
   ↓
Result
   ↓
Router
   ↓
Template
10. Database Connection Layer

Database connectivity is centralized through:

database/connection.py

This module is the database access foundation for the query modules.

The architecture should continue using the existing database connection approach instead of creating independent database connection mechanisms inside individual routers or templates.

New features should reuse the existing database infrastructure.

11. Database Schema Authority

The project contains:

database/database.sql

This file represents an important source for understanding the database schema.

However, when implementing or modifying database-dependent functionality, the actual database state should also be verified where necessary.

The following should never be assumed without verification:

Table names
Column names
Foreign-key relationships
Existing indexes
Existing constraints
Existing statuses
Existing data
Existing permissions

The authoritative source must be established before making schema-dependent changes.

12. Authentication Architecture

Authentication-related functionality is distributed across the existing authentication/session components.

Important files include:

routers/login.py
utils/auth.py
utils/session.py
utils/password.py

The application uses:

Authentication
Password hashing
Session/token handling
Role-based access concepts

The exact implementation details must remain aligned with the existing source code.

13. Password Security

Password-related functionality is handled through:

utils/password.py

Password handling should remain centralized rather than implementing password hashing manually inside individual routers.

Passwords must never be:

Stored in plaintext
Returned unnecessarily to templates
Exposed through logs
Included in AI prompts
Returned through unauthorized endpoints
14. Session Architecture

Session-related functionality is contained in:

utils/session.py

The session mechanism is used to maintain authenticated user context across requests.

A conceptual flow is:

Login
  ↓
Authentication
  ↓
Session / Token
  ↓
Authenticated Request
  ↓
User Identity
  ↓
Role / Permission Validation
  ↓
Requested Resource

Any new Principal functionality must preserve this authentication flow.

15. Role-Based Architecture

The current application contains the following primary roles:

Administrator
Principal
HOD
Teacher
Student

The architecture is role-aware.

Conceptually:

Authenticated User
        ↓
       Role
        ↓
 ┌──────┼────────┬─────────┬─────────┐
 ↓      ↓        ↓         ↓         ↓
Admin Principal HOD     Teacher   Student

Each role has its own functional area and access boundaries.

16. Administrator Architecture

Administrator functionality is primarily implemented through:

routers/admin.py
database/admin_queries.py
templates/admin/

The Admin portal currently contains functionality across areas such as:

Dashboard
Departments
Students
Teachers
Subjects
Timetable
Fees
Notices
Complaints
Users
Results
Reports
Assets
Inventory
Maintenance
Revaluation
Stock requests
Finance reports

The Admin portal should not automatically be treated as having unrestricted academic authority.

Authorization must be based on the actual implemented permissions and business rules.

17. Principal Architecture

Principal functionality is implemented through:

routers/principal.py
database/principal_queries.py
ai/principal.py
templates/principal/

Current Principal templates include:

templates/principal/
├── ai_assistant.html
├── concessions.html
├── dashboard.html
├── notice_approvals.html
├── principal_layout.html
├── results_approval.html
└── sensitive_complaints.html

The current Principal architecture provides a role-specific executive portal rather than simply exposing the complete Admin interface.

Current Principal functionality includes areas such as:

Principal dashboard
Principal AI assistant
Result approval
Fee concession processing
Notice approval
Sensitive complaints

The exact available operations must always be verified from the current router/query/template implementation before extending the system.

18. HOD Architecture

HOD functionality is organized under:

routers/hod.py
database/hod_queries.py
templates/hod/

Current templates include:

templates/hod/
├── dashboard.html
├── hod_layout.html
├── leaves.html
└── marks_verification.html

The HOD architecture represents department-level academic/administrative functionality.

HOD operations must remain appropriately scoped to the department and permissions available to the authenticated HOD.

19. Teacher Architecture

Teacher functionality is organized under:

routers/teacher.py
database/teacher_queries.py
templates/teacher/

Current templates include:

templates/teacher/
├── ai_tools.html
├── attendance.html
├── dashboard.html
├── leaves.html
├── marks.html
├── teacher_layout.html
└── timetable.html

The Teacher portal handles teacher-facing academic operations such as:

Attendance
Marks
Timetable
Leaves
AI tools
Dashboard

Teacher functionality must remain within the teacher's authorized academic scope.

20. Student Architecture

Student functionality is organized under:

routers/student.py
database/student_queries.py
templates/student/

Current templates include:

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

Student functionality includes areas such as:

Dashboard
Attendance
Fees
Marks
Results
Notices
Timetable
Complaints
Career
Placement

Students should only access their own authorized information.

21. Profile Architecture

Profile functionality is handled through:

routers/profile.py
database/profile_queries.py
templates/profile.html

Profile operations should remain separate from role-specific business modules where appropriate.

The profile system is responsible for user-facing profile information and should not be used as a shortcut for modifying unrelated institutional records.

22. Asset and Inventory Architecture

Asset-related functionality is implemented through:

routers/asset.py
database/asset_queries.py
templates/admin/

Relevant templates include:

assets.html
asset_details.html
inventory.html
disposals.html
maintenance.html
stock_requests.html

The architecture supports asset/inventory management while keeping those records in their existing authoritative storage.

Future dashboards should consume these records instead of creating duplicate asset databases.

23. Campus Operations Architecture

Campus operations are implemented through:

routers/campus.py
database/campus_queries.py
templates/campus/

Current templates include:

templates/campus/
├── dashboard.html
├── hostel_applications.html
├── hostel_rooms.html
├── library.html
├── transport.html
└── visitors.html

This represents operational areas such as:

Hostel
Library
Transport
Visitors
Campus dashboard

Principal-level dashboards may summarize these areas, but detailed operational management should remain in the appropriate existing module.

24. HR and Payroll Architecture

HR functionality is implemented through:

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

This architecture provides HR/payroll functionality.

Principal-level views should consume authorized summaries from the existing HR/payroll system instead of creating a second payroll ledger.

25. Documents and Compliance Architecture

Document and compliance functionality is implemented through:

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

The system includes institutional document and compliance-oriented functionality.

Private document storage is currently represented by:

private_uploads/docs/

Current files include:

aicte_2023.pdf
policy_2024.pdf

These files should be treated as institutional data and not automatically as trusted executable instructions.

26. Static Asset Architecture

Static application assets are stored under:

static/

Current structure:

static/
├── css/
│   └── style.css
├── images/
└── uploads/

Static assets include:

CSS
Images
Uploaded/generated assets
QR codes
Other frontend resources

The frontend should use the existing static asset structure rather than introducing unrelated parallel static directories.

27. File Upload Architecture

The project currently contains:

static/uploads/

and:

private_uploads/docs/

These locations serve different purposes.

Conceptually:

Public/static-accessible assets
        ↓
static/uploads/

Private institutional documents
        ↓
private_uploads/docs/

Sensitive institutional files should not be exposed merely by placing them inside a public static directory.

Any future file-upload functionality must consider:

Authentication
Authorization
File type validation
File size limits
Safe filenames
Path traversal protection
Access control
Storage location
Download authorization
Audit requirements
28. AI Architecture — Current State

The current repository contains AI modules:

ai/
├── career.py
├── principal.py
├── resume.py
└── teacher.py

The existing Principal AI implementation is:

ai/principal.py

and its UI is:

templates/principal/ai_assistant.html

The current AI functionality should be considered a role-specific AI capability.

It should not automatically be interpreted as a complete autonomous multi-agent architecture.

29. AI Architecture — Important Boundary

The future Principal AI system must not bypass the application's authorization architecture.

The intended future model is:

Principal
   ↓
Principal AI Interface
   ↓
Intent / Task Understanding
   ↓
Authorization
   ↓
Controlled Tool
   ↓
Existing SGI Backend
   ↓
Database

The AI must not become:

Principal
   ↓
LLM
   ↓
Arbitrary SQL
   ↓
Database

The second architecture is explicitly prohibited for the planned enterprise implementation.

30. Planned Principal Multi-Agent Architecture

The following is future architecture, not a claim about the current implementation.

The planned Principal Command Center may use:

                    Principal
                        │
                        ▼
              Principal Supervisor
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
 Academic Agent    Finance Agent     HR Agent
       │                │                │
       ├────────────────┼────────────────┤
       │                │                │
       ▼                ▼                ▼
 Campus Agent     Compliance Agent   Grievance Agent
                        │
                        ▼
                 Reporting Agent
                        │
                        ▼
                 Action Executor
                        │
                        ▼
               Existing SGI Backend
                        │
                        ▼
                     MySQL

This architecture should only be implemented after the current repository and authorization model have been audited.

31. LangGraph / LangChain / CrewAI Strategy

The planned AI architecture may use:

LangGraph

Primary orchestration framework for:

State management
Agent routing
Workflow execution
Human-in-the-loop
Retry handling
Persistence
Multi-agent graphs
Subgraphs
LangChain

Used where appropriate for:

LLM abstraction
Structured outputs
Tool calling
Prompt construction
Retrieval
Model integration
CrewAI

May be used selectively if a concrete requirement justifies it.

The project should not unnecessarily implement the same workflow using multiple agent frameworks.

The final framework choice must be based on actual requirements and implementation simplicity.

32. AI Action Security Model

Future AI operations should be categorized into three levels.

READ

Examples:

Show today's attendance.
Show pending approvals.
Show department performance.

These are informational operations, subject to normal authorization.

PREPARE

Examples:

Prepare a report.
Draft a notice.
Prepare a summary of pending approvals.
Generate a proposed action.

The system prepares the result without committing a sensitive state change.

EXECUTE

Examples:

Approve result.
Approve fee concession.
Publish notice.
Change an institutional record.

Sensitive execution should require:

Authentication
      ↓
Role verification
      ↓
Permission verification
      ↓
Scope verification
      ↓
Target validation
      ↓
Business-rule validation
      ↓
Explicit confirmation
      ↓
Transaction
      ↓
Audit
33. Human-in-the-Loop Architecture

For sensitive Principal actions, the future AI system should support human confirmation.

Example:

Principal:
"Approve all pending CSE Semester 5 results."

        ↓

AI identifies matching records

        ↓

AI presents:
- Number of records
- Department
- Semester
- Current status
- Expected impact

        ↓

Principal confirms

        ↓

Backend validates authorization

        ↓

Authorized action executes

        ↓

Audit record generated

The AI must never assume confirmation merely because the user issued the original request.

34. Business Logic Reuse Principle

The existing system already contains domain-specific database/query functionality.

Future modules must reuse existing authoritative logic whenever possible.

Preferred:

New UI
   ↓
Existing authorized backend operation
   ↓
Existing database/query layer

Not preferred:

New UI
   ↓
New duplicate SQL
   ↓
New duplicate business rules
   ↓
Same database

This principle prevents:

Data inconsistency
Different business rules
Duplicate maintenance
Security gaps
Conflicting results
35. Data Authority Principle

Each institutional domain should maintain a clear authoritative source.

Examples:

Student data
     ↓
Existing student system

Fee data
     ↓
Existing fee system

Payroll
     ↓
Existing HR/payroll system

Assets
     ↓
Existing asset/inventory system

Documents
     ↓
Existing document system

Academic results
     ↓
Existing academic/result system

Executive dashboards should aggregate from these systems.

They should not create parallel copies of the authoritative records.

36. Executive Dashboard Architecture

The planned Principal Executive Dashboard should follow:

Existing authoritative modules
            ↓
Reusable queries/services
            ↓
Executive aggregation layer
            ↓
KPI / Analytics / Alert calculations
            ↓
Principal Dashboard

The dashboard should provide executive visibility rather than replacing the detailed operational modules.

Potential dashboard domains include:

Academic Health
Student & Faculty
Department Performance
Financial Health
Approvals
Campus Operations
Compliance
Institutional Alerts
Today's Priorities

These are part of the planned Principal Command Center expansion and should not be interpreted as proof that all are currently implemented.

37. Reporting Architecture

The project contains:

utils/pdf_generator.py

and uses:

ReportLab
Matplotlib

for reporting/visualization-related functionality.

Reports should be generated from authoritative database data.

Report generation should not introduce a second data-storage mechanism.

Where a report contains sensitive information, authorization must be evaluated before generation/download.

38. Grade / Academic Utility Architecture

The project contains:

utils/grade.py

Academic calculations and grading-related logic should remain centralized where the current implementation already provides such utilities.

New modules should reuse existing grading logic rather than implementing slightly different grading calculations.

39. Environment Configuration

The project contains:

config.py
.env

Configuration should be centralized rather than hardcoded throughout the application.

Sensitive configuration values such as:

Database credentials
API keys
Secret values
Environment-specific configuration

should not be hardcoded into source code.

The .env file must be treated as sensitive configuration and should not be committed publicly.

40. Dependency Architecture

The project contains:

requirements.txt

This is the dependency declaration for the application environment.

Before introducing a new dependency, developers should verify:

Whether the capability already exists.
Whether an existing dependency can provide it.
Whether the new package is compatible with the current Python/runtime environment.
Whether it creates unnecessary architectural complexity.
Whether it introduces security or maintenance concerns.
41. Testing Architecture

The project contains a dedicated:

test/

directory.

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

Testing is therefore organized around important functional domains.

Any major architectural change should include appropriate regression testing.

42. Testing Strategy for Future Development

Future feature development should test at multiple levels.

Functional Testing

Verify that:

Valid input
    ↓
Expected business operation
    ↓
Expected result
Authorization Testing

Verify that:

Authorized user
    ↓
Allowed operation

and:

Unauthorized user
    ↓
Operation denied
Scope Testing

Verify that users cannot access records outside their permitted scope.

Regression Testing

Existing functionality must continue working after changes.

Database Testing

Verify:

Constraints
Relationships
Transactions
Updates
Inserts
Deletes
Error handling
43. Security Architecture

Security is a cross-cutting architectural concern.

The system must protect:

Authentication
Authorization
Database
Files
Reports
AI operations
Sessions
Sensitive institutional data

Important security principles include:

Authentication

Every protected operation must require a valid authenticated user.

Authorization

Authentication alone is insufficient.

The application must determine whether the authenticated user is authorized to perform the requested operation.

IDOR Protection

Object IDs supplied by the user must not automatically grant access.

Example:

/student/profile?id=100

must not mean that any authenticated student can view student 100.

Authorization must validate ownership/scope.

44. SQL Security

Database operations should use parameterized SQL.

Preferred:

SQL query
+
bound parameters

Avoid constructing SQL through unsafe string concatenation with user-controlled input.

AI-generated text must never be inserted directly into SQL.

45. Transaction Safety

Operations that modify multiple related records should use appropriate transaction handling.

Conceptually:

BEGIN
   ↓
Validate
   ↓
Operation 1
   ↓
Operation 2
   ↓
Operation 3
   ↓
COMMIT

If a critical operation fails:

ROLLBACK

This is particularly important for future approval workflows and other state-changing operations.

46. Audit Architecture

Auditability is especially important for an ERP system.

Sensitive operations should eventually have auditable information such as:

Who
What
When
Which record
Previous state
New state
Reason / remarks
Result

The existing repository must be audited before introducing or extending an audit mechanism to determine whether an authoritative audit system already exists.

A new audit table must not be created blindly if an equivalent system already exists.

47. Approval Architecture

The application contains approval-oriented Principal functionality.

Examples include:

Result Approval
Fee Concession
Notice Approval

Approval workflows should follow explicit state transitions.

Conceptually:

Pending
   ↓
Review
   ↓
Approve / Reject

The exact statuses must be taken from the current implementation/database and must not be invented.

48. Documents and Trust Boundary

Documents stored by the institution must be considered data, not executable instructions.

This is particularly important for future AI systems.

For example, if an uploaded document contains text such as:

Ignore previous instructions...

the AI system must treat that text as document content rather than as a system instruction.

The future AI architecture must maintain a clear trust boundary between:

System instructions
Application rules
User instructions
Institutional data
Uploaded documents
Database content
49. AI Prompt-Injection Protection

Future AI agents must assume that database records, uploaded documents, notices, complaints, and other external content may contain untrusted text.

The architecture should therefore follow:

LLM
 ↓
Interpret data
 ↓
Never treat data as system authority
 ↓
Tool authorization
 ↓
Backend validation

An LLM must not be able to elevate its own permissions through text found in institutional data.

50. AI Memory Architecture

Future AI memory may be used for conversational/task context.

However:

AI Memory ≠ Authorization

A remembered statement such as:

"Principal approved this earlier."

must never independently authorize a future sensitive operation.

Authorization must always be determined by the current backend security context and current operation state.

51. Multilingual AI Architecture

The planned Principal AI interface is intended to support natural-language interaction in multiple languages, including:

English
Hindi
Hinglish
Gujarati

The conceptual pipeline is:

User Message
      ↓
Language Detection
      ↓
Intent Understanding
      ↓
Structured Task
      ↓
Authorization
      ↓
Tool / Agent
      ↓
Backend Operation
      ↓
Result
      ↓
Response in User Language

The multilingual layer must not modify important institutional identifiers or statuses incorrectly.

52. Frontend Architecture

The frontend consists primarily of:

Jinja2 HTML templates
CSS
JavaScript
Static assets

The project uses reusable role-specific layouts.

Examples:

templates/admin/admin_layout.html
templates/principal/principal_layout.html
templates/hod/hod_layout.html
templates/student/student_layout.html
templates/teacher/teacher_layout.html

This provides a foundation for role-specific UI consistency.

53. Principal UI Architecture

The current Principal UI is based on:

templates/principal/principal_layout.html

with role-specific pages such as:

dashboard.html
results_approval.html
concessions.html
notice_approvals.html
sensitive_complaints.html
ai_assistant.html

The planned Principal Command Center should extend this architecture instead of creating an unrelated second Principal application.

54. Navigation Architecture

Navigation should reflect the user's authorized role and functionality.

For the Principal, future navigation may include:

Executive Dashboard
AI Principal Assistant
Approval Center
Academic Oversight
Finance Oversight
HR & Payroll
Campus Operations
Documents & Compliance
Meetings & Action Items
Notices & Events
Sensitive Complaints
Reports & Analytics
Notifications
Audit / My Activity
Profile

This is a proposed future navigation structure.

The exact navigation must be implemented only after current routes, permissions, and business capabilities are verified.

55. Separation of Operational and Executive Layers

A key architectural principle for the Principal Command Center is:

Operational Layer
        ↓
Detailed records and transactions

Executive Layer
        ↓
Summaries, decisions, approvals, analytics

For example:

Fee Management
        ↓
Detailed student fee records
        ↓
Principal Financial Health
        ↓
Collection / outstanding summary

Similarly:

Academic System
        ↓
Detailed marks/results
        ↓
Principal Academic Health
        ↓
Institution-level performance summary

The Principal dashboard should not duplicate operational workflows unnecessarily.

56. Current vs Future Architecture

It is important to distinguish implemented functionality from planned functionality.

Current Architecture

Currently present in the repository:

FastAPI
Jinja2
MySQL
Role-specific routers
Role-specific templates
Database query modules
Authentication/session utilities
AI modules
PDF/report utilities
Testing
Document management
Campus operations
HR/payroll
Asset/inventory
Planned Architecture

Future development may introduce:

Principal Command Center
Executive analytics layer
Unified Approval Center
Expanded Principal oversight
Multi-agent AI
LangGraph orchestration
Tool-based AI actions
Human-in-the-loop
Multilingual AI
Advanced auditability
AI-driven priorities

These future capabilities must not be represented as already implemented until they actually exist in the repository.

57. Architecture Change Rules

Any future developer or AI coding agent modifying this project must follow these rules.

Rule 1 — Audit First

Inspect the repository before modifying architecture.

Rule 2 — Reuse Existing Systems

Search for existing:

Routes
Queries
Templates
Utilities
Models
Tables
Permissions
Services

before creating new ones.

Rule 3 — No Duplicate Authority

Do not create parallel sources of truth for:

Students
Teachers
Fees
Payroll
Assets
Results
Documents
Complaints
Campus operations
Rule 4 — Backend Authorization

Never rely only on frontend visibility.

Rule 5 — No Blind Database Changes

Database migrations must be reviewed before execution.

Rule 6 — Preserve Existing Functionality

Existing working modules must not be broken while adding new features.

Rule 7 — Test Before Completion

New functionality must be tested and regression-tested.

Rule 8 — Separate Current and Future Architecture

Do not document planned functionality as if it already exists.

58. Database Migration Principle

Database changes should be:

Additive where possible
Reviewable
Reversible
Tested
Explicitly documented

Avoid destructive operations such as:

DROP TABLE
DROP COLUMN
Mass DELETE
Data overwrite

unless explicitly approved and safely migrated.

Before a migration:

Inspect current schema
        ↓
Design migration
        ↓
Review SQL
        ↓
Backup/rollback strategy
        ↓
Apply migration
        ↓
Verify
59. Error Handling Architecture

Errors should be handled at the appropriate layer.

Conceptually:

Request
   ↓
Validation
   ↓
Authorization
   ↓
Business operation
   ↓
Database
   ↓
Error handling
   ↓
User-safe response

Sensitive internal details such as:

SQL statements
Database credentials
Stack traces
Secrets
Internal file paths

should not be exposed unnecessarily to end users.

60. Logging Principle

Application logs should provide enough information for troubleshooting without exposing sensitive institutional data.

Avoid logging:

Passwords
Authentication tokens
Secrets
Sensitive personal data
Private document contents

Future AI execution logs should similarly avoid storing unnecessary sensitive prompt/context information.

61. Scalability Considerations

The current architecture is organized around modular routers and database query modules.

As the system grows, the following architectural improvements may become appropriate:

Router
   ↓
Service / Business Layer
   ↓
Repository / Query Layer
   ↓
Database

This should only be introduced where it provides a real architectural benefit.

Existing working code should not be unnecessarily rewritten simply to introduce additional abstraction layers.

62. Recommended Future Service Layer

For larger workflows, a service layer may eventually provide cleaner separation:

Router
   ↓
Service
   ↓
Query / Repository
   ↓
Database

For example:

routers/principal.py
        ↓
PrincipalApprovalService
        ↓
principal_queries.py
        ↓
MySQL

This is particularly useful for AI tools because:

Manual UI
   ↓
Service

AI Tool
   ↓
Same Service

This prevents AI and UI from implementing different business rules.

This is a future architectural direction and must be based on an actual repository audit before implementation.

63. AI Tool Architecture — Future

The preferred future design is:

AI Agent
   ↓
Tool
   ↓
Authorized Service
   ↓
Existing Query Layer
   ↓
Database

Not:

AI Agent
   ↓
Raw SQL Generator
   ↓
Database

Every sensitive tool should enforce authorization independently of the LLM.

64. Example Future AI Tool

A future tool might conceptually look like:

approve_result(request_id)

The tool itself should verify:

Authenticated user
+
Principal role
+
Required permission
+
Request scope
+
Current request status
+
Business rules
+
Confirmation state

Only after successful validation should the operation modify the database.

65. Architecture for Principal Executive Analytics

The future executive analytics system should follow:

Authoritative Data
       ↓
Validated Query
       ↓
Aggregation
       ↓
KPI Calculation
       ↓
Visualization
       ↓
Executive Decision

Analytics should not silently infer institutional policy.

For example:

Attendance = 58%

is a data point.

It should not automatically become:

"Critical attendance"

unless an approved institutional threshold/rule exists.

66. Alert Architecture

Future alerts should be based on explicit rules.

Conceptually:

Database State
      ↓
Configured Rule
      ↓
Alert Evaluation
      ↓
Alert

Not:

Database State
      ↓
LLM Guess
      ↓
"Critical"

Severity levels must be based on defined rules or actual workflow states.

67. Today's Priorities Architecture

The planned Principal dashboard may include:

Today's Priorities

The priority list should be generated from real actionable data.

Potential sources:

Pending approvals
Compliance actions
Meeting action items
Document reviews
Operational issues
Other authorized pending work

The AI may later explain why an item appears in the priority list, but the underlying facts must come from authoritative application data.

68. Architecture for Executive Drill-Down

Executive dashboard cards should eventually support drill-down.

Example:

Department Performance
        ↓
CSE
        ↓
Academic Oversight
        ↓
Attendance / Results / Faculty

Another example:

Compliance Alert
        ↓
Document
        ↓
Document Repository
        ↓
Review / Action

Another:

Pending Result Approval
        ↓
Approval Center
        ↓
Request Details
        ↓
Approve / Reject

The dashboard should act as an entry point into existing authorized workflows.

69. Architectural Anti-Patterns

The following patterns should be avoided.

Anti-pattern 1 — Duplicate Database

Creating a second student/fee/result database for the Principal dashboard.

Anti-pattern 2 — UI-only Security

Hiding buttons without enforcing backend authorization.

Anti-pattern 3 — AI Authority

Allowing the LLM to decide whether a user is authorized.

Anti-pattern 4 — Raw AI SQL

Allowing an LLM to execute arbitrary generated SQL.

Anti-pattern 5 — Duplicate Business Logic

Implementing separate approval rules for UI and AI.

Anti-pattern 6 — Blind Migration

Changing the database without schema verification and rollback planning.

Anti-pattern 7 — Invented Institutional Policy

Creating arbitrary attendance, compliance, severity, or approval rules without an authoritative source.

Anti-pattern 8 — Treating AI Output as Fact

Using model-generated statements as if they were database facts.

70. Source-of-Truth Hierarchy

For development decisions, the following hierarchy should be used:

1. Current source code
        ↓
2. Current database schema/state
        ↓
3. Existing implemented business rules
        ↓
4. Existing project documentation
        ↓
5. Approved feature requirements
        ↓
6. Architectural recommendations

If documentation conflicts with actual source code, the discrepancy should be identified and resolved rather than silently assuming one is correct.

71. Documentation Architecture

The project documentation is organized under:

docs/

Current documentation files:

01_PROJECT_OVERVIEW.md
02_ARCHITECTURE.md
03_DATABASE_SCHEMA.md
04_FEATURE_MAP.md
05_AUTH_AND_ROLES.md
06_FILE_CATALOG.md
07_VOLUME_1_BASELINE.md

Each document should have a distinct responsibility.

The documentation set should collectively provide:

Project Overview
       ↓
Architecture
       ↓
Database
       ↓
Feature Map
       ↓
Authentication / Roles
       ↓
File Catalog
       ↓
Baseline
72. Documentation Maintenance Rule

Whenever a major architectural change is implemented, the relevant documentation must be updated.

Examples:

New Router

Update:

02_ARCHITECTURE.md
06_FILE_CATALOG.md
New Database Table

Update:

03_DATABASE_SCHEMA.md
New Role Permission

Update:

05_AUTH_AND_ROLES.md
New Feature

Update:

04_FEATURE_MAP.md
Major Baseline Change

Update:

07_VOLUME_1_BASELINE.md
73. Current Architectural Summary

The current SGI Command Center architecture can be summarized as:

                    SGI COMMAND CENTER
                           │
                           ▼
                     FastAPI App
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
 Authentication       Role Routers        Utilities
        │                  │                  │
        │          ┌───────┼────────┐         │
        │          │       │        │         │
        │          ▼       ▼        ▼         │
        │        Admin Principal HOD/Teacher/ │
        │                         Student      │
        │                                     │
        └──────────────────┬──────────────────┘
                           │
                           ▼
                  Database Query Layer
                           │
                           ▼
                         MySQL

Supporting systems:

AI
Reports
PDF generation
Documents
Campus Operations
HR/Payroll
Assets/Inventory
Testing
Static Frontend
74. Target Architectural Direction

The long-term architecture for the Principal Command Center should evolve toward:

                         Principal
                            │
                            ▼
                  Principal Command Center
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ▼                 ▼                 ▼
       Manual UI        AI Interface      Analytics
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
                            ▼
                   Shared Authorized
                   Business Services
                            │
                            ▼
                    Existing SGI Data
                            │
                            ▼
                         MySQL

This architecture ensures that manual and AI-driven operations follow the same authorization and business rules.

75. Final Architectural Principles

The SGI Command Center architecture must preserve the following principles:

Existing authoritative systems must be reused.
Authentication and authorization are mandatory backend concerns.
Role boundaries must be preserved.
Principal is an executive oversight role, not a duplicate Admin role.
AI is an interface/orchestration layer, not an authority bypass.
AI must not receive unrestricted database access.
Sensitive AI actions require explicit authorization and confirmation.
Manual UI and AI should eventually use the same business services.
Institutional data must remain the source of truth.
No institutional policy should be invented without an authoritative requirement.
Database changes must be controlled, reviewed, and reversible where possible.
Security must be enforced on the backend.
Sensitive documents and institutional information require controlled access.
Analytics must distinguish facts from interpretation.
Current implementation and future architecture must never be confused.
Existing working functionality must be preserved during expansion.
Every major architectural change should be tested and documented.
76. Architecture Status
Current
FastAPI
Jinja2
MySQL
Role-based application structure
Role-specific routers
Role-specific templates
Database query modules
Authentication/session utilities
AI modules
PDF/report generation
Campus operations
HR/payroll
Asset/inventory
Document/compliance functionality
Automated tests
Under Planned Principal Expansion
Executive Dashboard
Unified Approval Center
Academic Oversight
Financial Oversight
HR/Payroll Oversight
Campus Operations Overview
Compliance Overview
Executive Reporting
Institutional Alerts
Principal Multi-Agent AI
LangGraph orchestration
LangChain tools
Human-in-the-loop
Multilingual interaction
AI action auditing
Shared UI/AI business services

The planned components must be implemented incrementally after repository, database, authorization, and business-rule verification.

77. Final Note

This document is the architectural baseline for the SGI Command Center project.

It should be used as a reference during future development, but it must not override the actual source code or database.

Whenever a future change is proposed:

Inspect
   ↓
Verify
   ↓
Design
   ↓
Review
   ↓
Implement
   ↓
Test
   ↓
Document

The goal is to evolve SGI Command Center into a secure, maintainable, enterprise-grade college ERP while preserving the existing application's authoritative data, role boundaries, business rules, and working functionality.