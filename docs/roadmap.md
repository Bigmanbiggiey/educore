# Development Roadmap

## Overview

EduCore will be developed in progressive phases that build upon one another.
The roadmap follows the platform's layered architecture, ensuring core
infrastructure is completed before business modules, curriculum plugins, and
enterprise capabilities.

Each phase delivers a functional milestone while maintaining clean architectural
boundaries and minimizing technical debt.

---

# Current Status

| Phase | Status |
|--------|--------|
| Phase 1 – Platform Foundation | ✅ Complete |
| Phase 2 – Core Academic Engine | ✅ Complete |
| Phase 3 – Curriculum Plugin Framework | ✅ Complete (framework + all five plugins — CBC, 8-4-4, British, TVET, University; Plugin SDK testing/version-compatibility tooling deliberately deferred) |
| Phase 4 – Finance | ✅ Complete (Stage 1 core billing/manual payments, Stage 2 live M-Pesa STK Push/callback, Stage 3 Payroll/ExpenseRecord) |
| Phase 5 – Communication | ✅ Complete (Stage 1 communication app core, Stage 2 real SMS via Africa's Talking, Stage 3 real Email via SMTP/SES; Push deliberately deferred, no provider named and no mobile client yet) |
| Phase 6 – Operations | ✅ Complete (library, inventory, clinic, documents) |
| Phase 7 – Campus Services | ✅ Complete (transport, hostel) |
| Phase 8 – Analytics & Reporting | ⏳ Planned |
| Phase 9 – AI Platform | ⏳ Planned |
| Phase 10 – Enterprise Platform | ⏳ Planned |

---

# Phase 1 — Platform Foundation

This phase establishes the technical foundation upon which every other module
depends.

### Objectives

- Authentication & Authorization
- Institution Management
- Multi-tenancy
- User Management
- Role-Based Access Control (RBAC)
- Dashboard Shell
- Notification Engine
- Audit Logging
- API Foundation
- Project Infrastructure

### Deliverables

#### Authentication

- User Registration
- Login
- JWT Authentication
- Password Reset
- Session Management

#### Institution Management

- Institution Creation
- Tenant Provisioning
- Domain Mapping
- Academic Calendar Settings
- Branding Settings

#### Multi-tenancy

- Tenant Resolution
- Tenant Isolation
- Shared Database Strategy
- Dedicated Database Support
- Request Middleware

#### Permissions

- Roles
- Permissions
- Institution Membership
- Permission Middleware

#### Notifications

- Email Engine
- SMS Engine
- Push Notification Framework
- Notification Templates

#### Platform Services

- Audit Logs
- Error Handling
- Logging
- Health Checks
- API Versioning

### Milestone

A fully operational SaaS platform capable of hosting multiple schools securely.

---

# Phase 2 — Core Academic Engine

This phase introduces curriculum-independent academic functionality shared by
every institution regardless of curriculum.

### Objectives

- Student Management
- Staff Management
- Parent Portal
- Academic Structure
- Timetables
- Attendance
- Admissions

### Deliverables

#### Student Management

- Student Profiles
- Enrollment
- Guardian Relationships
- Student Transfers
- Student Status Tracking

#### Staff

- Teacher Profiles
- Employee Records
- Department Assignment

#### Parents

- Parent Profiles
- Student Linking
- Parent Portal

#### Academic Structure

- Academic Years
- Terms
- Classes
- Streams
- Subject Catalog

#### Timetables

- Class Timetable
- Teacher Timetable
- Clash Detection

#### Attendance

- Student Attendance
- Staff Attendance
- Attendance Reports

#### Admissions

- Applications
- Admission Workflow
- Student Conversion

### Milestone

Schools can fully manage their academic structure before curriculum-specific
features are introduced.

---

# Phase 3 — Curriculum Plugin Framework

One of EduCore's flagship features.

Instead of hardcoding academic logic, EduCore provides a plugin architecture
that allows multiple curricula to coexist without changing the platform.

## Framework

### Curriculum Engine

- Curriculum Registry
- Plugin Loader
- Curriculum Resolver
- Academic Contracts

### Assessment Framework

- Assessment Engine
- Grading Engine
- Report Engine
- Transcript Engine
- Academic Progression Engine

### Plugin SDK

- Plugin Interface
- Validation
- Testing Framework
- Version Compatibility

## Official Curriculum Plugins

### CBC

- Learning Areas
- Competencies
- Core Values
- Pertinent & Contemporary Issues (PCIs)
- Projects
- Continuous Assessment
- Performance Levels
- CBC Report Cards

### 8-4-4

- Subjects
- CATs
- Midterms
- End Terms
- Ranking
- Mean Grades
- KCPE/KCSE Integration

### British Curriculum

- EYFS
- Key Stages
- Year Groups
- IGCSE
- A-Level
- Coursework
- Predicted Grades

### TVET

- Courses
- Competency Units
- Workshops
- Practical Exams
- Industrial Attachment
- Certification

### University

- Faculties
- Schools
- Departments
- Programmes
- Units
- Course Registration
- GPA & CGPA
- Dissertation
- Graduation

### Milestone

EduCore supports multiple education systems through interchangeable curriculum
plugins without modifying the core platform.

---

# Phase 4 — Finance

Complete financial management for institutions.

### Deliverables

- Fee Structures
- Invoicing
- Student Billing
- Installment Plans
- Scholarships
- M-Pesa Integration
- Bank Payments
- Cash Payments
- Receipts
- Financial Reports
- Payroll
- Expense Tracking

### Milestone

Schools can fully manage their financial operations.

---

# Phase 5 — Communication

Centralized communication platform connecting administrators, teachers, parents,
and students.

### Deliverables

- SMS
- Email
- Push Notifications
- Circulars
- Announcements
- Internal Messaging
- Parent Communication
- Notification Scheduling
- Message Templates

### Milestone

Real-time communication across the institution.

---

# Phase 6 — Operations

Administrative modules supporting day-to-day institutional operations.

## Library

- Book Catalog
- Borrowing
- Returns
- Reservations
- Fines

## Inventory

- Assets
- Suppliers
- Stock
- Stock Movement
- Procurement

## Clinic

- Student Medical Records
- Clinic Visits
- Medication
- Health Reports

## Documents

- File Management
- Student Documents
- Staff Documents
- Generated Reports
- Secure Storage

### Milestone

Administrative departments become fully digitized.

---

# Phase 7 — Campus Services

Modules for managing campus facilities and student welfare.

## Transport

- Vehicles
- Drivers
- Routes
- Stops
- Student Allocation

## Hostel

- Hostels
- Rooms
- Bed Allocation
- Occupancy Reports

### Milestone

Complete campus management capabilities.

---

# Phase 8 — Analytics & Reporting

Business intelligence and institutional insights.

### Dashboards

- Administrator Dashboard
- Principal Dashboard
- Teacher Dashboard
- Parent Dashboard
- Student Dashboard

### Reports

- Academic Reports
- Attendance Reports
- Financial Reports
- Operational Reports

### Analytics

- Student Performance Trends
- Attendance Trends
- Fee Collection Analytics
- Enrollment Statistics
- Resource Utilization

### Exports

- PDF
- Excel
- CSV

### Milestone

Institution leadership gains actionable insights through analytics and reporting.

---

# Phase 9 — AI Platform

AI-powered tools to improve teaching, administration, and student outcomes.

### AI Gateway

- Provider Abstraction
- Model Configuration
- AI Services

### AI Features

- Lesson Plan Generation
- Exam Generation
- Automatic Report Comments
- Student Performance Prediction
- Attendance Risk Detection
- Academic Assistant
- Administrative Assistant

### Future Expansion

- AI Tutor
- Parent Assistant
- Student Study Assistant
- Intelligent Search

### Milestone

AI becomes a native capability across EduCore.

---

# Phase 10 — Enterprise Platform

Capabilities for large-scale deployments and commercial SaaS operations.

### White-labeling

- Custom Branding
- Custom Themes
- Custom Logos

### Billing

- Subscription Management
- Plan Management
- Invoicing
- Payment Gateway Integration

### Deployment

- Shared Infrastructure
- Dedicated Infrastructure
- Dedicated Database Deployments
- Regional Hosting

### Marketplace

- Curriculum Plugins
- Third-party Integrations
- Extensions

### Enterprise Features

- Custom Domains
- SSO
- Backup & Disaster Recovery
- Monitoring
- Audit Compliance
- API Integrations

### Milestone

EduCore becomes a production-ready enterprise SaaS platform capable of serving
thousands of institutions across multiple regions.

---

# Long-Term Vision

After completing all ten phases, EduCore will provide:

- Multi-tenant SaaS architecture
- Multiple curriculum support
- Complete School ERP functionality
- AI-assisted education management
- Enterprise-grade scalability
- White-label deployments
- Plugin ecosystem
- Regional and international expansion

The roadmap is iterative rather than strictly linear. While each phase has a
primary focus, enhancements, maintenance, and optimization will continue across
previous phases throughout the project's lifecycle.