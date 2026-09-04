# Architecture

Northstar Hiring is a small server-rendered FastAPI application. A browser sends a form submission or page request to FastAPI; the route authenticates the signed cookie, authorizes the user role, applies business rules, reads/writes SQLite, and returns HTML or a CSV. There is no client-side data cache, so filtering, authorization, pagination, and sorting are all evaluated on the server.

## Moving pieces

- **Browser:** simple HTML forms and navigation; it never decides authorization or a legal stage change.
- **FastAPI application (`app.py`):** routes, authentication, role checks, pipeline rules, rendering, and CSV response.
- **SQLite:** durable relational data for users, openings, applications, panel assignments, append-only events, and alert dismissals.

## Representative request: advance an application

1. A recruiter submits `POST /applications/{id}/advance`.
2. The server resolves their cookie into a user and rejects anyone without the recruiter role.
3. It reads the current application in one transaction, calculates the immediate next item in the ordered stage list, and refuses terminal or rejected applications.
4. On success it updates the stage and stage timestamp, clears prior alert dismissals, and inserts a timeline event with the actor and old/new stages.
5. The server redirects to the application page, which reads the new state and timeline from SQLite.

## Deliberate omissions

I did not build public careers, scheduling, resume parsing, email delivery, or scorecards: none is needed to satisfy the ten core goals. Password hashing is intentionally minimal SHA-256 for a self-contained demo; production would use Argon2/bcrypt, CSRF protection, secure session storage, migrations, structured logging, and a managed Postgres database.
