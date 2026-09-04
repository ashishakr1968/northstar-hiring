# Architecture

## Overview

Northstar Hiring is a small server-rendered hiring pipeline application built with FastAPI and SQLite.

The application follows a simple request-response architecture. A browser sends a page request or form submission to the FastAPI server. The server authenticates the user, checks their role, validates the requested operation, applies the relevant business rules, reads or updates SQLite, and returns HTML or a CSV response.

The application keeps the important business rules on the server. The browser is responsible mainly for displaying information and submitting forms.

## Main Components

### Browser

The browser provides:

- HTML forms
- Candidate and opening views
- Navigation
- Search and filtering controls
- Pipeline actions
- Interviewer feedback forms
- Dashboard and alert views
- CSV export access

The browser does not determine whether a user is authorized to perform an operation or whether a stage transition is valid.

### FastAPI Application

The main application is contained in `app.py`.

It is responsible for:

- Authentication
- Session handling
- Role-based access control
- Candidate and opening CRUD operations
- Pipeline transition rules
- Rejection and reinstatement
- Interviewer assignments
- Interviewer feedback
- Candidate history
- Bulk operations
- Search, filtering, sorting, and pagination
- Dashboard metrics
- Stalled candidate alerts
- CSV export
- HTML rendering

Keeping these responsibilities in one application makes the project easy to run and review within the scope of the assignment.

### SQLite

SQLite stores the application data locally.

The main tables are:

- `users`
- `sessions`
- `openings`
- `applications`
- `assignments`
- `events`
- `alert_dismissals`

Foreign keys are enabled and indexes are created for commonly queried fields.

## Authentication and Authorization

Authentication uses a database-backed session.

Passwords are not stored in plaintext. The application uses PBKDF2-HMAC-SHA256 with a random salt for password hashing.

After successful login, a random session token is generated. Only its SHA-256 hash is stored in the database. The browser receives the session token through an HTTP-only cookie.

Role checks are performed on the server. The two supported roles are:

- Recruiter
- Interviewer

Recruiters can manage openings and applications and perform pipeline operations.

Interviewers can access applications assigned to them and provide interview feedback. They cannot access recruiter-only operations.

## Pipeline Rules

The normal pipeline is:

`Applied → Screening → Interview → Offer → Hired`

The application does not allow arbitrary stage editing.

A normal advancement moves an application only to the immediate next stage. Terminal or rejected applications cannot be advanced through the normal advancement route.

Rejection is represented separately using the `Rejected` stage and the `rejected_from` field.

When a candidate is rejected, the stage from which they were rejected is preserved. Reinstatement uses that value to return the candidate to the exact previous stage.

## History

Important application changes are recorded in the append-only `events` table.

Events can record:

- Application creation
- Stage changes
- Rejection
- Reinstatement
- Other relevant workflow activity
- Interviewer feedback

Existing events are treated as historical records rather than editable application state.

This allows a reviewer to inspect how a candidate moved through the pipeline.

## Stalled Alerts

Stalled alerts are calculated from the candidate's current stage and `stage_changed_at`.

The thresholds are:

- Screening: more than 10 days
- Interview: more than 10 days
- Offer: more than 14 days

Alert dismissal is stored against both the application and its stage.

When an application changes stage, previous dismissal records are cleared. This means that a candidate can be dismissed at one stage and still receive a new alert if they later become stalled at another stage.

## Search and Listing

Candidate search, filtering, sorting, and pagination are performed on the server.

The browser sends the selected parameters to the application, and SQLite performs the relevant filtering and ordering before the result is rendered.

This avoids depending on client-side filtering of the complete dataset.

## Security Measures

The application includes:

- Password hashing using PBKDF2-HMAC-SHA256
- Random session tokens
- Database-backed sessions
- HTTP-only session cookies
- SameSite cookie protection
- CSRF tokens for state-changing forms
- Server-side role checks
- Server-side validation of pipeline transitions
- HTML escaping of user-controlled values
- SQLite parameterized queries
- Foreign-key enforcement

The implementation is intentionally small and self-contained for the assignment.

## Deployment

The application can run locally with SQLite and is packaged with a Dockerfile for deployment.

The deployed demonstration uses Render. The application does not require a separate database service for the basic demonstration.

For a production system, persistent managed database storage would be preferable.

## Deliberate Scope

The project focuses on the requirements of the assignment.

The following features were intentionally not implemented:

- Public careers portal
- Resume parsing
- Email delivery
- External calendar integration
- Automated interview scheduling
- Candidate self-service accounts
- Advanced analytics
- Managed production database infrastructure

These features were outside the core assignment requirements and would add complexity without improving the demonstration of the required workflow rules.
