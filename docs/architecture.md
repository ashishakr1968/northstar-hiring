# Architecture

Northstar Hiring is a server-rendered FastAPI application that manages a recruiting pipeline. The system is designed around the principle of server-owned data: all authorization, filtering, pagination, and sorting decisions are made on the backend, never relying on client-side state.

## Overview

The application follows a request-response pattern where:
- **Browser:** Sends HTML forms and navigation requests. It has no JavaScript state persistence, no local caching of pipeline data, and no decision-making authority over authorization or stage transitions.
- **FastAPI application (`app.py`):** Contains all route handlers, authentication logic, role-based access control, pipeline business rules, HTML rendering with embedded CSS (inline in `app.py`), CSV export, and form processing. The app owns all data queries.
- **SQLite database:** Stores all persistent state — users, openings, applications, panel assignments, append-only timeline events, and alert dismissals. The schema is deliberately conventional and production-migration-friendly (conventional enough to move to Postgres with minimal changes).

## Moving pieces

- **Browser:** Simple HTML forms and navigation. Never decides authorization or a legal stage change.
- **FastAPI application (`app.py`):** Routes, authentication via signed cookies, role checks, pipeline rules, HTML rendering with embedded CSS, CSV export, and form processing.
- **SQLite:** Durable relational data for users, job openings, applications, panel assignments, append-only events (timeline), and alert dismissals. Schema is conventional enough to migrate to Postgres production.

## Request lifecycle example: advance an application

1. A recruiter submits `POST /applications/{id}/advance`.
2. The server resolves the user from the signed cookie and rejects anyone without the recruiter role (HTTP 401/403).
3. It reads the current application state in a single transaction, calculates the immediate next stage from the ordered stage list (`Applied → Screening → Interview → Offer → Hired`), and refuses terminal (Hired) or rejected applications.
4. On success: updates `stage` and `stage_changed_at`, clears prior alert dismissals for that application (movement resets the 10-day stall timer), inserts a timeline event with the actor and old/new stages, and issues a 303 redirect to the application page.
5. The redirected page reads the new state and timeline from SQLite and renders the HTML response with the updated stage badge and timeline.

## Deliberate omissions

The following are intentionally not built (they are outside the ten core goals scope):

| Category | Items |
| --- | --- |
| **Candidate-facing** | Public careers page, candidate self-service, resume parsing, document upload |
| **Communication** | Email delivery, notification system, SMS alerts |
| **Evaluation** | Scorecards, candidate rating systems, grading rubrics |
| **Scheduling** | Calendar integration, interview scheduling, availability polling |
| **Security (beyond auth)** | CSRF protection, secure session storage (beyond signed cookies), rate limiting, brute-force protection |
| **Infrastructure** | Database migrations, schema versioning, connection pooling, managed Postgres |
| **Observability** | Structured logging, application metrics, health checks, APM integration |
| **Frontend** | React/Vue SPA, custom design system, client-side routing, state management |

Production hardening would require: Argon2/bcrypt password hashing, managed Postgres database, API endpoints with OpenAPI/Swagger docs, React or Vue SPA with typed API client, enterprise-grade security headers, and comprehensive observability stack.

## HTML rendering approach

The app uses inline CSS within Python f-strings (the `CSS` multi-line string in `app.py`) rather than a separate template engine or static CSS file. This choice was made to:
- Keep the application self-contained (single file, no external assets)
- Avoid build steps or template compilation
- Simplify deployment (Docker copy only `app.py` and `requirements.txt`)
- Enable rapid iteration on UI changes

The trade-off is limited CSS maintainability for a demo-sized codebase. In production, this would be extracted to SCSS/CSS files and served statically.
