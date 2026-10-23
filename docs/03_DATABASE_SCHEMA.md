# SGI Command Center — Database Schema

**Project:** SGI Command Center  
**Document:** 03_DATABASE_SCHEMA.md  
**Document Type:** Current-State Database Architecture & Schema Reference  
**Status:** Baseline Documentation  
**Last Updated:** 2026-10-05

---

## 1. Document Purpose

This document describes the database architecture of the SGI Command Center application.

The project uses **MySQL** as its primary relational database.

The purpose of this document is to provide a centralized reference for:

- Database organization
- Database access architecture
- Existing query modules
- Schema ownership
- Major functional data domains
- Relationships between institutional data
- Database security principles
- Future Principal Command Center integration
- Future AI integration boundaries

This document must be treated as a **current-state documentation baseline**.

The actual database schema and source code remain authoritative.

If this document conflicts with the actual database schema, the discrepancy must be investigated rather than silently assuming that this document is correct.

---

# 2. Database Technology

The current application uses:

```text
Database Engine:
MySQL

Python database interaction is organized through the project's database layer.

The repository contains:

database/

with a centralized connection module:

database/connection.py

and domain-specific query modules.

3. Database Architecture

The current database architecture can be represented as:

                         SGI Command Center
                                │
                                ▼
                         FastAPI Routers
                                │
                                ▼
                       Database Query Layer
                                │
                                ▼
                     database/connection.py
                                │
                                ▼
                              MySQL
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
        Student Domain    Academic Domain    Finance Domain
              │                 │                 │
              ├─────────────────┼─────────────────┤
              │                 │                 │
              ▼                 ▼                 ▼
        HR / Payroll      Campus Operations   Documents
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                                ▼
                       Institutional Data

The exact physical relationships between all tables must be verified against the current database schema.

4. Database Source File

The repository contains:

database/database.sql

This file is a primary source for understanding the database definition.

It should be reviewed whenever:

A new feature is implemented
A table is added
A column is added
A relationship is modified
A constraint is changed
A query is created
A Principal dashboard KPI is introduced
An AI tool needs access to institutional data
5. Database Query Layer

The project separates database operations into domain-specific modules.

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

This organization provides domain-level separation for database operations.

6. Query Module Responsibilities

Each query module should primarily contain database operations relevant to its domain.

Conceptually:

admin_queries.py
    ↓
Administrator-related database operations

principal_queries.py
    ↓
Principal-related database operations

student_queries.py
    ↓
Student-related database operations

teacher_queries.py
    ↓
Teacher-related database operations

hod_queries.py
    ↓
HOD-related database operations

fee_queries.py
    ↓
Fee-related database operations

hr_queries.py
    ↓
HR / payroll database operations

asset_queries.py
    ↓
Asset / inventory operations

campus_queries.py
    ↓
Campus operations

docs_queries.py
    ↓
Documents / compliance operations

profile_queries.py
    ↓
Profile operations

user_queries.py
    ↓
User/account operations

The actual SQL contained in each module should always be treated as the implementation authority.

7. Database Connection

The centralized database connection module is:

database/connection.py

The architecture should use this existing connection mechanism instead of introducing unrelated database connection code inside individual features.

Preferred pattern:

Router
   ↓
Query Module
   ↓
Existing Connection Layer
   ↓
MySQL

Avoid:

Router A
   ↓
Custom DB connection

Router B
   ↓
Different DB connection

AI Agent
   ↓
Separate DB connection

unless a specific architectural requirement has been verified and approved.

8. Major Data Domains

The current application contains multiple institutional data domains.

At a high level:

1. Users & Authentication
2. Students
3. Teachers
4. Departments
5. Subjects
6. Academic / Results
7. Attendance
8. Fees
9. HR / Payroll
10. Assets / Inventory
11. Campus Operations
12. Documents / Compliance
13. Notices
14. Complaints
15. Reports
16. Profile Data

The exact table names and columns for each domain must be verified from:

database/database.sql

and the active database where necessary.

9. User / Account Data Domain

User/account data is handled through:

database/user_queries.py

and authentication-related functionality is implemented through:

utils/auth.py
utils/session.py
utils/password.py

The user domain is responsible for application identity and access-related information.

Conceptually:

User
 │
 ├── Authentication
 ├── Role
 ├── Profile
 └── Authorized Application Access

The exact table structure must be taken from the current schema.

10. Role Data

The application currently recognizes these primary roles:

Administrator
Principal
HOD
Teacher
Student

Role information is part of the application's authorization model.

The database must not be interpreted as granting authority merely because a role value exists.

Effective authorization may depend on:

Role
+
Permission
+
Scope
+
Business Rules
+
Current Record State
11. Student Data Domain

Student-related operations are handled through:

database/student_queries.py

The Student portal contains functionality such as:

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

Student information may therefore participate in multiple relational domains.

Conceptually:

Student
   │
   ├── Academic Records
   ├── Attendance
   ├── Fees
   ├── Results
   ├── Timetable
   ├── Complaints
   └── Other Student Services

The actual foreign-key relationships must be verified against the schema.

12. Faculty / Teacher Data Domain

Teacher-related operations are handled through:

database/teacher_queries.py

Teacher functionality includes areas such as:

Attendance
Marks
Timetable
Leaves
AI Tools
Dashboard

Conceptually:

Teacher
   │
   ├── Department
   ├── Subjects
   ├── Attendance
   ├── Marks
   ├── Timetable
   └── Leave Records

The exact relationships must be verified from the database schema.

13. Department Data Domain

Department-related information is used across several modules.

Departments may participate in:

Students
Teachers
Subjects
Academic performance
Attendance
Results
Reports
Principal analytics

Conceptually:

Department
     │
 ┌───┼─────────────┐
 ▼   ▼             ▼
Students Teachers Subjects
     │   │             │
     └───┼─────────────┘
         ▼
   Academic Analytics

The actual schema must determine the authoritative department relationships.

14. Subject Data Domain

The Admin portal contains subject-management functionality.

Subject-related information can participate in:

Departments
Teachers
Students
Timetable
Marks
Results

The exact table names, columns, keys, and relationships must be obtained from the current schema.

No new subject master should be introduced if an authoritative subject structure already exists.

15. Academic Data Domain

The application contains academic functionality across:

Students
Teachers
HOD
Principal
Admin

Academic data may include:

Subjects
Marks
Results
Attendance
Academic sessions
Departments
Semester information

The exact database representation must be verified from:

database/database.sql

Academic authority must remain separated from purely administrative authority.

16. Result Data

The current application includes result-related functionality.

Principal-related result operations are represented by:

templates/principal/results_approval.html

and:

database/principal_queries.py

The result data model must be treated as an existing authoritative academic data source.

A future Principal dashboard should summarize result information rather than create a parallel result system.

17. Attendance Data

Attendance is used by academic-facing modules.

Attendance-related information may be associated with:

Student
Teacher
Subject
Department
Academic period

The exact database design must be taken from the actual schema.

For Principal analytics:

Attendance Records
        ↓
Validated Query
        ↓
Institution-level Aggregation
        ↓
Principal Dashboard

The dashboard should not maintain a second attendance ledger.

18. Fee Data Domain

Fee functionality is handled through:

database/fee_queries.py

The Admin portal contains fee-related functionality, while the Student portal also exposes fee information.

Principal functionality includes fee concession processing:

templates/principal/concessions.html

The fee system should remain the authoritative source for:

Fee demand
Fee collection
Outstanding amount
Concessions
Fee-related status

Exact field names and calculations must be taken from the existing schema and query implementation.

19. Fee Concession Architecture

Fee concessions are an approval-sensitive workflow.

Conceptually:

Student / Fee Request
        ↓
Concession Request
        ↓
Principal Review
        ↓
Approve / Reject
        ↓
Authoritative Fee Data

A future AI tool for concession approval must not directly update arbitrary fee fields.

It should invoke the authorized backend operation after validation.

20. HR / Payroll Data Domain

HR/payroll functionality is handled through:

database/hr_queries.py

and:

templates/hr/

The HR module currently includes areas such as:

Employees
Payroll
Salary Components
Salary Revisions
Exits
HR Dashboard

Payroll data is sensitive institutional information.

Principal-level analytics should use authorized aggregate information.

The Principal dashboard must not duplicate the payroll database.

21. Asset and Inventory Data Domain

Asset and inventory operations are handled through:

database/asset_queries.py

Relevant functionality includes:

Assets
Asset Details
Inventory
Maintenance
Disposals
Stock Requests

Conceptually:

Asset
  │
  ├── Inventory
  ├── Maintenance
  ├── Disposal
  └── Stock Requests

Exact relationships must be verified from the actual database.

22. Campus Operations Data Domain

Campus-related data is handled through:

database/campus_queries.py

Current campus operations include:

Hostel
Library
Transport
Visitors
Campus Dashboard

Conceptually:

Campus Operations
       │
 ┌─────┼──────────────┐
 ▼     ▼              ▼
Hostel Library     Transport
       │
       ▼
    Visitors

The exact table structure must be verified from the schema.

23. Hostel Data

Hostel-related functionality is exposed through:

templates/campus/hostel_applications.html
templates/campus/hostel_rooms.html

Hostel information may involve:

Applications
Rooms
Allocations
Student associations

Only fields and relationships that actually exist in the current schema should be documented as implemented.

24. Library Data

Library functionality is exposed through:

templates/campus/library.html

The exact library schema should be verified from:

database/database.sql
database/campus_queries.py

Future Principal summaries may use library data if the underlying authoritative records support the requested KPI.

25. Transport Data

Transport functionality is exposed through:

templates/campus/transport.html

The exact transport tables and relationships must be taken from the current database schema.

No assumptions should be made about:

Routes
Vehicles
Drivers
Fees
Student allocations

unless they are present in the actual implementation.

26. Visitor Data

Visitor functionality is exposed through:

templates/campus/visitors.html

Visitor records may contain sensitive information.

Access to visitor information should therefore remain authorization-controlled.

Future Principal dashboards should expose only the level of detail required for the intended executive function.

27. Document Data Domain

Document/compliance functionality is handled through:

database/docs_queries.py

and:

templates/docs/

Current document-related areas include:

Repository
Compliance
Meetings
Action Items
Dashboard

Institutional documents are stored separately from normal application data where applicable.

28. Private Document Storage

The project contains:

private_uploads/docs/

with current files such as:

aicte_2023.pdf
policy_2024.pdf

Private documents should not automatically be exposed through public static routes.

A document download should be subject to:

Authentication
+
Authorization
+
Document access policy
29. Compliance Data Domain

Compliance functionality is represented through:

templates/docs/compliance.html

The system may track institutional compliance-related records.

For future Principal dashboards, compliance status should be taken from actual workflow states.

Do not invent states such as:

Critical
Failed
Healthy

unless those states exist in the authoritative implementation or are explicitly defined as approved business rules.

30. Meetings and Action Items

The document management area contains:

templates/docs/meetings.html
templates/docs/action_items.html

These records may support future Principal executive workflows.

Conceptually:

Meeting
   ↓
Decision / Action
   ↓
Action Item
   ↓
Responsible Person
   ↓
Status
   ↓
Completion

The exact data model must be verified from the database schema.

31. Notice Data Domain

The application includes notice functionality.

Principal-specific notice approval is represented by:

templates/principal/notice_approvals.html

The notice workflow should use the existing authoritative notice data.

A future Principal AI tool must not create a separate notice repository.

32. Complaint Data Domain

Complaint functionality exists across role-specific areas.

The Principal portal includes:

templates/principal/sensitive_complaints.html

Complaints can contain sensitive personal and institutional information.

Database access must therefore respect:

Role
Permission
Scope
Sensitivity

The exact complaint schema must be verified from the current database.

33. Reports Data Domain

Reports may aggregate information from multiple institutional domains.

Conceptually:

Students
Teachers
Attendance
Results
Fees
HR
Assets
Campus
Documents
       ↓
    Queries
       ↓
    Aggregation
       ↓
    Report

Reports should not create independent copies of institutional data unless there is an explicit architectural requirement.

34. Database Relationships

The application is relational and therefore multiple domains are expected to be connected through identifiers and relationships.

Common conceptual relationships include:

Department
    │
    ├── Students
    ├── Teachers
    └── Subjects

and:

Student
    │
    ├── Attendance
    ├── Marks
    ├── Results
    ├── Fees
    └── Complaints

and:

Teacher
    │
    ├── Subjects
    ├── Attendance
    ├── Marks
    └── Timetable

These diagrams describe conceptual relationships only.

The actual foreign keys and cardinalities must be verified from the database schema.

35. Primary Keys

Every relational table should have a clear record identifier according to the actual schema.

Primary keys provide:

Record identity
Relationship targets
Update/delete targeting
Query filtering
Referential integrity

Developers must not assume an ID column name without checking the schema.

For example, the system may use different naming conventions across existing tables.

36. Foreign Keys

Foreign keys establish relationships between related institutional records.

Examples conceptually include:

Student → Department
Teacher → Department
Subject → Department
Result → Student
Attendance → Student
Fee → Student

The exact relationships must be taken from:

database/database.sql

and verified against the live schema when necessary.

37. Referential Integrity

Database relationships should preserve referential integrity.

Before changing or deleting a parent record, developers must understand its dependent records.

For example:

Department
    ↓
Students
Teachers
Subjects

Deleting a department may affect multiple dependent datasets.

Therefore destructive operations must never be introduced casually.

38. Status Fields

Many institutional workflows use state/status values.

Examples conceptually include:

Pending
Approved
Rejected
Completed

However, these values must not be assumed to be universal across all modules.

Every feature must use the status vocabulary already defined by its authoritative implementation.

39. Database Security

Database security must include:

Parameterized SQL
Controlled credentials
Least-privilege database access where practical
Secure connection configuration
Input validation
Authorization before data access
Transaction safety
Controlled migrations

Database credentials must never be exposed through:

Templates
API responses
Logs
AI responses
Client-side JavaScript
40. IDOR Protection

Database identifiers must not be treated as authorization.

Example:

/student?id=25

does not mean:

Authenticated user → automatically authorized for student 25

The backend must verify that the requested record belongs to the user's permitted scope.

This is especially important for:

Students
Complaints
Fees
Documents
HR records
Payroll
Results
Visitor records
41. SQL Injection Protection

All user-controlled values used in database queries must be parameterized.

Avoid:

"SELECT * FROM students WHERE id = " + user_id

Prefer the project's existing parameterized query approach.

AI-generated natural language must never be concatenated directly into SQL.

42. AI Database Boundary

The future Principal AI system must not receive unrestricted database access.

Incorrect:

User
 ↓
LLM
 ↓
Generated SQL
 ↓
MySQL

Preferred:

User
 ↓
Principal AI
 ↓
Approved Tool
 ↓
Authorized Query / Service
 ↓
MySQL

This ensures that the backend remains responsible for:

Authorization
Validation
Scope
Business rules
Database integrity
43. AI Read Operations

A future AI read tool should be narrowly scoped.

Example:

get_pending_result_approvals()

is preferable to:

execute_sql(query)

The tool should return only the data required for the operation.

44. AI Write Operations

Write operations require additional controls.

Conceptually:

AI Request
   ↓
Identify intended action
   ↓
Validate target
   ↓
Check role
   ↓
Check permission
   ↓
Check scope
   ↓
Check business rules
   ↓
Confirm if required
   ↓
Execute transaction
   ↓
Audit

The LLM itself should never be trusted as the final authority.

45. Principal Database Architecture

Current Principal database functionality is primarily represented by:

database/principal_queries.py

Current Principal functionality includes areas such as:

Dashboard
Result Approval
Fee Concessions
Notice Approval
Sensitive Complaints

Future Principal Command Center development should extend the existing Principal data-access architecture.

46. Principal Executive Dashboard Data Flow

The planned dashboard should follow:

                 MySQL
                   │
       ┌───────────┼────────────┐
       │           │            │
       ▼           ▼            ▼
    Academic     Finance     Operations
       │           │            │
       └───────────┼────────────┘
                   ▼
          Validated Aggregations
                   │
                   ▼
          Principal Dashboard

The dashboard should not persist duplicate KPI records unless there is a specific caching architecture approved for that purpose.

47. KPI Architecture

Potential Principal KPIs include:

Students
Faculty
Departments
Attendance
Fee Collection
Outstanding Fees
Pending Approvals
Complaints

Before implementing any KPI, verify:

Source table
Source fields
Calculation
Filters
Date/session scope
Authorization
Existing query availability

A KPI must not be fabricated when its source data is unavailable.

48. Financial KPI Principle

Financial dashboard metrics should be derived from the authoritative fee system.

Potential conceptual calculations:

Collection Rate
=
Collected Amount / Total Demand × 100

However, the exact calculation must match the application's actual fee model.

For example, if the existing system defines demand differently, the dashboard must use that definition.

49. Academic KPI Principle

Academic metrics should be calculated from authoritative academic data.

Examples:

Average marks
Result performance
Attendance percentage
Department comparison

The application must not introduce arbitrary thresholds or interpretations without an approved rule.

50. Compliance KPI Principle

Compliance analytics must distinguish between different workflow states.

For example:

Submitted

must not automatically be interpreted as:

Verified / Closed

unless the application's actual workflow explicitly defines that equivalence.

This distinction is important for executive reporting.

51. Data Aggregation Principle

Executive analytics should aggregate data without modifying the source records.

Preferred:

Source Data
   ↓
SELECT / Aggregate
   ↓
Dashboard

Not:

Source Data
   ↓
Copy to Principal Table
   ↓
Dashboard

unless an explicit caching/materialized-view strategy has been designed and approved.

52. Transaction Architecture

Transactions are required when multiple related database modifications must succeed or fail together.

Conceptually:

BEGIN
  ↓
Validate
  ↓
Modify record A
  ↓
Modify record B
  ↓
Create audit record
  ↓
COMMIT

If any required operation fails:

ROLLBACK

This is particularly important for future:

Approvals
Rejections
Financial workflows
Academic workflows
Multi-record operations
53. Database Migration Rules

All schema modifications must follow:

Inspect
   ↓
Design
   ↓
Review
   ↓
Backup / rollback plan
   ↓
Migration
   ↓
Verification

Avoid unapproved:

DROP TABLE
DROP COLUMN
TRUNCATE
Mass DELETE
Irreversible transformations
54. Additive Migration Principle

Where possible, migrations should be additive.

Examples:

ADD TABLE
ADD COLUMN
ADD INDEX
ADD CONSTRAINT

before considering destructive changes.

If a destructive change is genuinely required, it must include:

Impact analysis
Backup strategy
Rollback strategy
Data migration strategy
Testing
Explicit approval
55. Database Documentation Requirements

Whenever a new database table is introduced, document:

Table name
Purpose
Primary key
Columns
Data types
Nullable fields
Default values
Indexes
Foreign keys
Constraints
Status values
Relationships
Owning module

This information should be reflected in this document after the implementation is verified.

56. Schema Change Governance

A future AI coding agent must not create a table simply because it appears convenient.

Before creating a new table, it must answer:

Does the required data already exist?

If yes:

Reuse existing data.

If no:

Determine whether a new authoritative entity is genuinely required.

Then:

Design
Review
Approve
Migrate
Test
Document
57. Duplicate Data Prevention

The following duplicate systems must be avoided:

Principal Student Table
Principal Fee Table
Principal Result Table
AI Student Table
AI Approval Table
AI Payroll Table

when equivalent authoritative records already exist.

The Principal layer should aggregate from existing systems.

58. Reporting and PDF Data Flow

The reporting architecture can be represented as:

MySQL
  ↓
Query Layer
  ↓
Validated Data
  ↓
Report Generator
  ↓
PDF / Visualization

Relevant utility:

utils/pdf_generator.py

Reports must respect the same authorization rules as the underlying data.

59. Database and File Relationship

Some institutional entities may reference uploaded files.

Conceptually:

Database Record
      ↓
Document / File Reference
      ↓
Private or Public Storage

File access must not rely only on knowing a filename.

The application must verify authorization before returning sensitive files.

60. Backup and Recovery Considerations

Database backup and recovery should be treated as an operational requirement for production deployment.

A proper production strategy should address:

Full backups
Incremental backups where appropriate
Retention
Restore testing
Recovery objectives
Failure handling

The exact production backup policy is not established by this document unless explicitly implemented elsewhere.

Therefore no specific backup schedule should be assumed.

61. Performance Considerations

As the ERP grows, database performance should be monitored.

Potential optimization areas include:

Indexes
Query design
Pagination
Aggregation
Connection handling
N+1 query prevention
Report generation
Dashboard KPI queries

Optimization should be based on actual query behavior rather than premature assumptions.

62. Dashboard Query Optimization

The future Principal dashboard may require multiple KPIs.

Avoid executing unnecessarily large independent queries for every dashboard component.

Potential architecture:

Principal Dashboard Request
        ↓
Required KPI Queries
        ↓
Validated Aggregations
        ↓
Single Dashboard Response

The actual optimization approach should be selected after profiling the current database/query performance.

63. Pagination

Large datasets should not be loaded completely when the UI only requires a page.

This is especially relevant for:

Students
Teachers
Complaints
Documents
Visitors
Assets
Inventory
Results
Reports

Pagination should use safe, parameterized query logic.

64. Date and Time Data

Date/time filtering must use the actual database field types and application conventions.

For analytics such as:

Today's priorities
Monthly collection
Academic session
Attendance trend
Document review dates

the implementation must verify:

Date columns
Timezone assumptions
Academic session boundaries
Existing application conventions

Do not assume that the calendar year and academic year are interchangeable.

65. Academic Session Scope

Academic analytics may need to distinguish:

Calendar Year

from:

Academic Session

The correct scope must be determined from the application's actual data model.

A Principal KPI should not mix records from unrelated academic sessions without an explicit requirement.

66. Data Consistency

A dashboard number must be traceable to the underlying source data.

For example:

Principal Dashboard
   ↓
Students = 2,500

should be explainable through the underlying query/data source.

The system should avoid hardcoded KPI values.

67. Data Validation

Before displaying aggregated data, validate:

Null values
Duplicate records
Invalid statuses
Unexpected negative amounts
Missing relationships
Date anomalies

The exact validation rules depend on the relevant domain.

AI should not silently "fix" database data without an explicit authorized operation.

68. Sensitive Data Domains

Particularly sensitive domains include:

Passwords
User credentials
Student personal data
Complaints
Payroll
Financial records
Private documents
Visitor records
Academic results

These should receive appropriate authorization and access restrictions.

69. Least-Privilege Principle

Database access and application operations should follow least privilege.

A user should receive only the access required for their role and authorized responsibilities.

Likewise, a future AI tool should receive only the minimum backend capability required to perform its intended task.

70. Database Authority and AI

The database remains the source of truth.

If AI says:

"There are 12 pending approvals."

the application should obtain that fact from the database/query layer.

The AI must not invent the number.

If the database query fails, the AI should report that the data could not be retrieved rather than fabricate a result.

71. AI Data Interpretation

AI may:

Summarize
Explain
Compare
Generate natural-language reports
Identify patterns from retrieved data
Route tasks

AI must not silently alter:

Database facts
Institutional statuses
Approval states
Financial amounts
Academic results

unless an authorized backend operation explicitly performs that modification.

72. Data Scope in Principal AI

The Principal has institution-wide oversight only where the backend permissions permit it.

The AI must not assume:

Principal = unrestricted database access

Instead:

Principal
   ↓
Permission
   ↓
Data Scope
   ↓
Allowed Query
73. Data Scope in HOD AI

Similarly, any future HOD AI capability must respect department scope.

Conceptually:

HOD
 ↓
Department Scope
 ↓
Authorized Academic Data

The same principle applies to:

Teacher
Student
Administrator

based on their actual permissions.

74. Database and Authorization Separation

A database query answering:

SELECT ...

does not automatically mean that every application user is authorized to receive its result.

Authorization must happen at the application/business layer.

Conceptually:

User
 ↓
Authorization
 ↓
Allowed Query
 ↓
Database

not:

User
 ↓
Database Query
75. Current Database Architecture Status

The current project has:

MySQL
database/connection.py
database/database.sql
Domain-specific query modules
Role-specific query modules

The database supports the current ERP functional areas.

However, the complete table-by-table schema should always be verified directly from the current database/database.sql and, when required, the active database.

This document deliberately does not invent table definitions that have not been verified.

76. Future Principal Command Center Database Strategy

The Principal Command Center should preferably consume existing data.

Conceptually:

Existing Database
        │
 ┌──────┼──────────┬──────────────┐
 ▼      ▼          ▼              ▼
Academic Finance   HR        Campus/Docs
 │      │          │              │
 └──────┴──────────┴──────────────┘
                │
                ▼
       Principal Analytics
                │
                ▼
        Principal Dashboard

New Principal-specific tables should only be introduced when the Principal workflow creates genuinely new persistent entities, such as:

Approval workflow records
AI execution/audit records
Explicit task records
Other approved domain entities

Even then, existing schema must be checked first.

77. Future AI Audit Data

If the future AI architecture requires persistent execution auditing, the design may eventually store information such as:

AI Request
User
Role
Intent
Tool
Target
Action Level
Confirmation
Execution Result
Timestamp
Audit Reference

This is a proposed future capability.

It must not be implemented as a duplicate of an existing audit system if one already exists.

78. Database Change Checklist

Before changing the database:

[ ] Inspect database/database.sql
[ ] Inspect relevant query module
[ ] Search for existing table/entity
[ ] Search for existing columns
[ ] Verify foreign keys
[ ] Verify indexes
[ ] Verify constraints
[ ] Verify current status values
[ ] Determine data migration requirements
[ ] Prepare rollback strategy
[ ] Review SQL
[ ] Test
[ ] Update documentation
79. New Feature Database Checklist

For every new feature:

[ ] Does required data already exist?
[ ] Can existing queries be reused?
[ ] Is a new table genuinely required?
[ ] Is a new column genuinely required?
[ ] What is the source of truth?
[ ] Who owns the data?
[ ] Who can read it?
[ ] Who can modify it?
[ ] What is the lifecycle?
[ ] What relationships exist?
[ ] What audit requirements exist?
80. Principal Dashboard Database Checklist

Before implementing a Principal KPI:

[ ] Identify authoritative source
[ ] Verify table
[ ] Verify column
[ ] Verify relationship
[ ] Verify calculation
[ ] Verify date/session scope
[ ] Verify permissions
[ ] Verify data quality
[ ] Verify existing query
[ ] Avoid duplicate storage
81. Database Documentation Rules

This document should be updated whenever verified database architecture changes.

Updates are required for:

New tables
Removed tables
New relationships
Changed columns
New constraints
New indexes
New authoritative data domains
Major migration changes

Documentation should reflect the actual implementation rather than intended architecture alone.

82. Important Distinction: Conceptual vs Physical Schema

This document contains two types of information.

Physical schema information

Information directly verified from:

database/database.sql

or the active database.

Conceptual architecture

High-level relationships used to explain the system.

For example:

Student → Fees

may be conceptually correct, but the actual physical relationship must be verified from the database.

AI coding agents must not convert conceptual diagrams into assumed SQL structures without verification.

83. Database Source-of-Truth Hierarchy

For database work, use this priority:

1. Current live database schema
        ↓
2. database/database.sql
        ↓
3. Current query modules
        ↓
4. Current router/business logic
        ↓
5. Project documentation
        ↓
6. Feature requirements
        ↓
7. Architectural proposal

If two sources disagree, investigate the discrepancy.

Do not silently overwrite one interpretation with another.

84. Final Database Architecture

The current database architecture can be summarized as:

                    SGI COMMAND CENTER
                            │
                            ▼
                         FastAPI
                            │
                            ▼
                    Application Routers
                            │
                            ▼
                    Query / DB Layer
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
       database/connection.py    Domain Queries
                 │                     │
                 └──────────┬──────────┘
                            ▼
                           MySQL
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
       ▼                    ▼                    ▼
   Academic             Finance              HR
       │                    │                    │
       ▼                    ▼                    ▼
   Students             Fees                Payroll
       │
       ├──────── Attendance
       ├──────── Marks
       ├──────── Results
       └──────── Complaints

       Additional domains:
       Assets / Inventory
       Campus Operations
       Documents / Compliance
       Notices
       Profiles
       Users
85. Final Database Principles

The SGI Command Center database architecture must preserve these principles:

MySQL remains the primary relational database.
Existing authoritative tables must be reused.
Database connections should use the existing connection architecture.
Domain-specific query modules should remain organized by responsibility.
Parameterized SQL must be used for user-controlled values.
Authentication does not replace authorization.
Record IDs do not automatically grant access.
Sensitive domains require controlled access.
AI must never receive unrestricted SQL/database authority.
AI tools should access data through controlled backend operations.
Executive dashboards should aggregate existing authoritative data.
Duplicate institutional ledgers must not be created.
Database changes must be reviewed before execution.
Destructive migrations require explicit approval.
Transactions must be used for multi-step critical operations.
Reports must respect source-data authorization.
Private documents must remain access-controlled.
KPI calculations must be traceable to authoritative data.
Institutional policy must not be invented through database logic.
Documentation must be updated when the verified schema changes.
86. Database Status
Current
Database Engine:
MySQL

Connection Layer:
database/connection.py

Schema Reference:
database/database.sql

Query Modules:
Domain-specific *_queries.py files

Primary Data Domains:
Users
Students
Teachers
Departments
Subjects
Academic
Attendance
Results
Fees
HR / Payroll
Assets / Inventory
Campus Operations
Documents / Compliance
Notices
Complaints
Profiles
Reports
Future Direction
Principal Executive Analytics
Unified approval data where genuinely required
AI execution/audit records where required
Controlled AI data-access tools
Shared business-service layer
Advanced analytics/caching only where justified

All future database additions must first verify that the required entity or capability does not already exist.

87. Final Note

The SGI Command Center database is the authoritative foundation for the ERP.

The application, dashboards, reports, and future AI systems must consume and operate against this authoritative data rather than creating competing sources of truth.

The correct development workflow is:

Inspect Existing Schema
        ↓
Understand Relationships
        ↓
Identify Existing Data
        ↓
Reuse Existing Query / Business Logic
        ↓
Design Only What Is Missing
        ↓
Review Migration
        ↓
Implement
        ↓
Test
        ↓
Verify Data Integrity
        ↓
Update Documentation

This approach is mandatory for safe expansion of the SGI Command Center, particularly for the upcoming Principal Command Center and its planned AI-powered capabilities.