# Plan and execution record

I split the development work into six focused sessions over roughly 12 hours total. The ordering was intentional: I wanted to get the data model and authentication working first, because every later view depends on the same truth. If I had built the dashboard UI before the pipeline rules were solid, I would have had to rewrite half the HTML templates once the stage logic was correct.

## How I broke the work into sessions

1. **Model and authentication** — SQLite schema, user model, password hashing, login form and route. This was the foundation. I needed the user table, the login route, and the signed-cookie authentication system before anything else could work. I also seeded the demo data (recruiter/interviewer users, job openings, one application in "Applied" stage) so I could actually test the app while building on top of it.

2. **Openings/applications CRUD** — Create/read/edit/delete for job openings and applications with stage tracking. Once I had users and auth, I needed the core CRUD: openings (with title, department, description, status), and applications (candidate name, email, source, stage). This gave me something to look at in the browser — a list of applications, a way to add new ones.

3. **Pipeline and interview permissions** — Stage advancement rules, rejection/reinstatement, assignment of interviewers, per-user application filtering. This is where the business rules live. I built the `advance()` helper, the reject/reinstate routes, the assignments many-to-many table, and the per-user filtering that makes the dashboard show different things for recruiters vs interviewers. I also verified all six core workflow rules work: apply, advance, reject, reinstate, assign interviewer, add feedback.

4. **Search/bulk/export** — Filtering, sorting, pagination, bulk advance/reject, CSV export of pipeline data. I added the filter sidebar on the applications page (search by name/email, select opening, select stage, select source), the 20-per-page pagination, the bulk action buttons (advance/reject selected), and the CSV export endpoint. This session also gave me the source-of-hire reporting charts.

5. **Dashboard/alerts** — Pipeline overview dashboard, source reporting, stalled-application alerts with 10-day timeout, alert dismissal. I built the dashboard page that shows metrics (open positions, active applications, interviews scheduled this week, hires this month), the source chip grid, the applications-by-opening and applications-by-stage tables, the weekly application volume chart, and the stalled-alert alerts that appear when a candidate has been in the same stage for 10 days. I also built the dismiss-alert functionality.

6. **Tests, documentation, and deployment packaging** — Unit tests, all doc files, Dockerfile, Render deployment, environment variables, troubleshooting guide. I wrote the two pytest tests for advance/reject, updated all the markdown docs (architecture, schema, decisions, plan, AI prompts), fixed the Dockerfile, added the `DATABASE_PATH` environment variable requirement, and wrote the troubleshooting section for Render 500 errors.

## What order did I build in, and why that order

I deliberately ordered the sessions so that irreversible data rules came before dashboard polish. The data model and authentication had to be first because every later view depends on the same truth — if the schema was wrong, every page would show wrong data. The pipeline rules (advance, reject, reinstate) had to come before the dashboard, because the dashboard reads the pipeline state. The search/bulk/export and dashboard/alerts sessions could be somewhat independent, but I still wanted the pipeline rules solid first so the search and filters were operating on correct data. The tests/docs/deployment session was last because it needs the app to be working end-to-end, and because documenting the trade-offs and deployment quirks (like the `DATABASE_PATH` env var) benefits from having actually deployed and hit the bugs.

## Estimated vs. intended allocation

| Area | Estimated | Intended |
| --- | --- | --- |
| Data model and routes | 3h | 3h |
| Core UI (HTML forms, tables) | 2h | 2h |
| Permissions and pipeline rules | 2h | 2h |
| Reporting and alerts | 2h | 2h |
| Tests, docs, and deployment | 3h | 4h (includes this documentation update) |

The estimates were mostly on the mark. The one area that ran long was the documentation and deployment packaging — not because the code was hard, but because I kept running into the Render deployment issues (ephemeral filesystem, `DATABASE_PATH` env var, `@app.on_event("startup")` deprecation) and had to add troubleshooting sections to both `SUBMISSION.md` and the docs. I also ended up writing the AI prompt record and the decisions log, which I hadn't initially planned to write this formally. The actual code time was very close to the estimates, but the documentation and deployment packaging ate into the buffer I had planned.

## What did I cut when I ran short

I consciously decided not to build anything outside the ten core goals, but there were specific features I'm glad I cut:

- **Public careers portal**: A candidate-facing job board with application tracking for applicants who aren't in the system. The assignment is an internal hiring pipeline, not a public job board, and adding this would require authentication, spam prevention, and SEO concerns.

- **Resume parsing / document upload**: Would require a model endpoint, file storage, and validation logic — completely outside the 12-hour window and the assigned goals.

- **Email delivery**: SMTP setup, template management, bounce handling — ops overhead with no direct impact on the pipeline rules being demonstrated.

- **External calendar integration**: OAuth with Google/Outlook, calendar API rate limits, conflict checking — another whole system to maintain.

- **Automated interview scheduling**: Would need availability polling, time zone handling, send-out emails — the assignment tracks stages but not specific interview times.

- **Candidate self-service accounts**: Lets candidates view their own data, "forgot password" flows, profile management for candidates. The assignment keeps all control on the recruiter/interviewer side.

- **Advanced analytics**: Dashboards showing time-in-stage distributions, conversion rates, etc. The current dashboard shows basic counts; analytics would need a separate data warehouse or at least Postgres with aggregation queries.

- **Managed production database infrastructure**: PostgreSQL on Railway/AWS RDS. The assignment explicitly uses SQLite for the "runnable demo" goal; swapping in Postgres would add deployment complexity (migrations, connection pooling, environment variable management) without demonstrating the required workflow rules.

- **Custom design system**: Tailwind/SCSS, component libraries, responsive breakpoints beyond what the inline CSS already handles. The UI is functional but plain — I prioritized correct behavior over pixel-perfect staging.

**The common thread**: Every feature I cut was something that would require either (a) additional infrastructure (database, SMTP, OAuth) or (b) significant additional code (form validation, spam protection, responsive design). I prioritized getting all 10 core workflow rules correct over building anything else. The proof point: all six core workflow rules (apply, advance, reject, reinstate, assign interviewer, add feedback) are implemented and tested, and the documentation accurately reflects what's there and what's not.

If I had another 12 hours, the things I'd add are: Postgres migration with proper indexes, Argon2/bcrypt password hashing, API endpoints with OpenAPI/Swagger docs, email notification triggers for stage changes, scheduling/calendar integration, and a custom design system with better typography and spacing. But for the assignment's constraints, cutting everything outside the core goals was the right call.