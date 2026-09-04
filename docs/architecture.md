# Architecture

## Overview

Northstar Hiring is a server-rendered FastAPI application that manages a recruiting pipeline. I chose this approach over a separate SPA + API because, within a short time budget, it means fewer moving parts and all data queries owned by the server. The browser never decides authorization or a legal stage change — that stays on the backend.

## Moving pieces

### Browser

The browser provides HTML forms and navigation. It never makes authorization decisions or determines whether a stage transition is valid — that's always the server's job. The browser also doesn't cache pipeline data; every page load re-renders from whatever SQLite currently contains.

**How it talks to the server:** All communication happens through HTML forms and links, with the server authenticated by a signed cookie. There's no JSON API between client and server; the server returns complete HTML pages each time.

### FastAPI application (`app.py`)

This is the single source of truth for everything: authentication, business rules, data queries, and HTML rendering. I kept everything in one file (with inline CSS) to avoid needing a build step or template engine, which keeps the deployment simple — just copy `app.py` and `requirements.txt`.

**What it does:**

- Authenticates users from signed cookies
- Checks role permissions on every request
- Evaluates pipeline rules (can this application advance? can this be rejected?)
- Reads/writes SQLite
- Renders HTML with embedded CSS
- Returns CSV for exports

**How it talks to the server:** It is the server. It listens on `0.0.0.0:8000` (or the `$PORT` env var) and handles each request synchronously.

### SQLite (`pipeline.db`)

Durable relational data for everything the app tracks. I used SQLite because it makes the demo immediately runnable — clone the repo, `uvicorn app:app`, and it works. The schema is conventional enough to migrate to Postgres later if needed.

**Tables that matter:**

| Table | What it stores |
| --- | --- |
| `users` | Recruiters and interviewers |
| `openings` | Job openings with departments/descriptions |
| `applications` | Candidate applications, stages, sources, timestamps |
| `assignments` | Many-to-many: which interviewers are on which applications |
| `events` | Append-only timeline — creation, stage changes, rejection, reinstatement, feedback |
| `alert_dismissals` | Which applications/stages the user has dismissed |

**How it talks to the app:** Through parameterized SQL queries via Python's `sqlite3` module. The app opens a new connection for each request (via the `db()` context manager), runs the query, and closes it. This means there's no connection pooling or persistent session — each request is independent.

## Where each piece runs

| Piece | Where it runs |
| --- | --- |
| **Browser** | User's device — any machine with a web browser |
| **FastAPI app** | Server — Render's free tier (or any Python-compatible host) |
| **SQLite database** | Same process as the FastAPI app (local file `pipeline.db`) |

**Why this matters:** Having SQLite in the same process as the app makes deployment dead simple (one Dockerfile, one command). The trade-off is no concurrent write support — if two requests hit at the exact same time, SQLite handles it with its built-in locking, but under high load you'd want Postgres. For the assignment's scope and Render's free tier, it's been fine.

## Request path: one representative user action, end to end

Let me trace what happens when a recruiter clicks "Advance" on an application:

1. **Browser** sends `POST /applications/{app_id}/advance` with a signed cookie
2. **FastAPI** reads the cookie, looks up the user in SQLite, checks `user.role == 'recruiter'` — if not, returns 401/403
3. **FastAPI** reads the application from SQLite (`SELECT * FROM applications WHERE id=?`), checks the current stage is not 'Rejected' or 'Hired'
4. **FastAPI** calculates the next stage from the ordered list (`Applied → Screening → Interview → Offer → Hired`)
5. **FastAPI** updates the application: `UPDATE applications SET stage=?, stage_changed_at=?, updated_at=? WHERE id=?`
6. **FastAPI** clears prior alert dismissals for that application (movement resets the stall timer)
7. **FastAPI** inserts an event into the `events` table: actor, kind='stage', detail='Applied → Screening'
8. **FastAPI** sends a 303 redirect back to `GET /applications/{app_id}`
9. **Browser** follows the redirect, sends `GET /applications/{app_id}` with the same cookie
10. **FastAPI** reads the updated application, reads the timeline events, renders the HTML page with the new stage badge and updated timeline
11. **Browser** displays the page

Each step is a single request-response cycle. There's no WebSocket, no client-side state persistence, no background jobs — just synchronous HTTP calls.

## What I decided *not* to build, and why

### Deliberate omissions (outside core assignment requirements)

| Feature | Why I didn't build it |
| --- | --- |
| **Public careers portal** | The assignment is an internal hiring pipeline, not a candidate-facing job board. Adding public-facing forms would add authentication, spam prevention, and SEO concerns without advancing the core workflow. |
| **Resume parsing / document upload** | Would require a model endpoint, file storage, and validation logic — completely outside the 12-hour window and the assigned goals. |
| **Email delivery** | SMTP setup, template management, bounce handling — ops overhead with no direct impact on the pipeline rules being demonstrated. |
| **External calendar integration** | OAuth with Google/Outlook, calendar API rate limits, conflict checking — another whole system to maintain. |
| **Automated interview scheduling** | Would need availability polling, time zone handling, send-out emails — the assignment tracks stages but not specific interview times. |
| **Candidate self-service accounts** | Lets candidates view their own data. The assignment keeps all control on the recruiter/interviewer side; there's no "forgot password" or profile management for candidates. |
| **Advanced analytics** | Dashboards showing time-in-stage distributions, conversion rates, etc. The current dashboard shows basic counts; analytics would need a separate data warehouse or at least Postgres with aggregation queries. |
| **Managed production database infrastructure** | PostgreSQL on Railway/AWS RDS. The assignment explicitly uses SQLite for the "runnable demo" goal; swapping in Postgres would add deployment complexity (migrations, connection pooling, environment variable management) without demonstrating the required workflow rules. |
| **Custom design system** | Tailwind/SCSS, component libraries, responsive breakpoints beyond what the inline CSS already handles. The UI is functional but plain — I prioritized correct behavior over pixel-perfect styling. |

**The common thread:** Every feature I cut was something that would require either (a) additional infrastructure (database, SMTP, OAuth) or (b) significant additional code (form validation, spam protection, responsive design). I prioritized getting all 10 core workflow rules correct over building anything else. The proof point: all six core operations (apply, advance, reject, reinstate, assign interviewer, add feedback) are implemented, tested, and working — and the documentation accurately reflects what's there and what's not.

**One decision I revisited:** I initially didn't plan to document the `DATABASE_PATH` environment variable requirement, but after hitting the Render 500 error on first deployment (the app defaults to `pipeline.db` in CWD, but Render's filesystem is ephemeral), I added it as a troubleshooting section in SUBMISSION.md and as decision #8 in `docs/decisions.md`. It's a small thing that made the difference between a working demo and a broken deployment, and I'm glad I went back to add it.
