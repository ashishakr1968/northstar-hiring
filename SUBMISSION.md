# Submission

- Repository: https://github.com/ashishakr1968/northstar-hiring
- Live application: https://northstar-hiring.onrender.com
- The local demo is seeded at first start.

## Demo credentials

| Role | Email | Password |
| --- | --- | --- |
| Recruiter | recruiter@northstar.test | `demo-password` |
| Interviewer | interviewer@northstar.test | `demo-password` |

### Deployment

This application is deployed on Render.com (free tier). See live URL above.

**Render.com characteristics:**
- Free tier: 750 hours/month, services sleep after 15 min of inactivity
- First load may take 1-2 minutes to wake from sleep
- Docker-based deployment from GitHub repository
- Environment variable: `DATABASE_PATH=pipeline.db`
- Critical: set `DATABASE_PATH` to a persistent volume path (e.g., `/var/data/pipeline.db`) for database persistence across deploys

**Alternative deployment:**
- PythonAnywhere, Railway, or any Python-compatible free tier

## Local development

```bash
# Start the application
cd northstar-hiring
export DATABASE_PATH=pipeline.db
uvicorn app:app --host 0.0.0.0 --port 8000

# Login credentials:
# - Recruiter: recruiter@northstar.test / demo-password
# - Interviewer: interviewer@northstar.test / demo-password
```

## Troubleshooting internal server errors

If you encounter a 500 Internal Server Error on deployment:

1. **Database path not set**: Render's free tier has an ephemeral filesystem. Set the `DATABASE_PATH` environment variable to a persistent path like `/var/data/pipeline.db`.

2. **Application startup**: The `@app.on_event("startup")` decorator is deprecated in FastAPI 0.121.0+. It still works but may show warnings. Consider migrating to `lifespan` event handlers.

3. **Cold start delay**: First request after service wakes from sleep may take 1-2 minutes to initialize the database.

4. **Bind address**: Ensure the app binds to `0.0.0.0` and uses the `$PORT` environment variable as specified in the Dockerfile.

## Goals checklist

Mark each honestly. Partial is fine — say what is partial.

| # | Goal | Status | Notes |
|---|------|--------|-------|
| 1 | Apply with candidate name, email, source, and opening selection | Done | Full CRUD with seeded demo data |
| 2 | Advance applications through stages (Applied → Screening → Interview → Offer → Hired) | Done | Single `advance()` helper handles both individual and bulk actions |
| 3 | Reject applications to a terminal "Rejected" stage | Done | Includes `rejected_from` field for proper reinstatement |
| 4 | Reinstate rejected applications back to their previous stage | Done | Stage-keyed alert dismissals clear on advance |
| 5 | Assign interviewers to applications | Done | Per-user filtering via assignments table with many-to-many relationship |
| 6 | Add immutable feedback/timeline entries | Done | Append-only event table, no editable feedback records |
| 7 | Search/filter/sort/paginate applications list | Done | Server-side filtering, sorting, pagination with 20-per-page |
| 8 | Bulk advance/reject multiple applications | Done | Per-candidate evaluation, no blocking of ineligible candidates |
| 9 | Export pipeline to CSV | Done | CSV export of open pipeline with candidate, opening, stage, source |
| 10 | Dashboard with statistics and stalled alerts | Done | Source reporting, per-opening stats, 10-day stall alerts with dismissal |

## How much time did you actually spend?

Around 16 hours across multiple sessions, covering model/auth, CRUD, pipeline rules, search/bulk/export, dashboard/alerts, tests/docs, and deployment packaging.

## What would you do next, with another 12 hours?

- Migrate SQLite to Postgres with proper indexes for concurrent write support
- Add Argon2/bcrypt password hashing instead of SHA-256
- Add API endpoints with OpenAPI/Swagger documentation
- Add email notification triggers for stage changes
- Add scheduling/calendar integration for interview slots
- Add a custom design system with better typography and spacing

## What are you least happy with in this codebase, and why?

The inline CSS embedded in Python f-strings (the `CSS` multi-line string in `app.py`) works for a demo but is hard to maintain at scale. I'd extract it to separate CSS files and use a proper template engine like Jinja2 with HTML templates. Also, the database path handling could be more robust — the `DATABASE_PATH` env var works but the fallback to `pipeline.db` in CWD causes the Render 500 error on first deployment if the env var isn't set, which the troubleshooting section in SUBMISSION.md now documents.

All 10 core requirements are met. The most significant trade-off was choosing SQLite + server-rendered HTML over a managed database + SPA, which keeps the app immediately runnable (`git clone && uvicorn app:app`) at the cost of not scaling to concurrent writes or providing a JSON API.
```
