# Plan and execution record

I split the development work into six focused sessions:

1. **Model and authentication** — SQLite schema, user model, password hashing, login form and route.
2. **Openings/applications CRUD** — Create/read/edit/delete for job openings and applications with stage tracking.
3. **Pipeline and interview permissions** — Stage advancement rules, rejection/reinstatement, assignment of interviewers, per-user application filtering.
4. **Search/bulk/export** — Filtering, sorting, pagination, bulk advance/reject, CSV export of pipeline data.
5. **Dashboard/alerts** — Pipeline overview dashboard, source reporting, stalled-application alerts with 10-day timeout, alert dismissal.
6. **Tests, documentation, and deployment packaging** — Unit tests, all doc files, Dockerfile, Render deployment, environment variables, troubleshooting guide.

## Estimated vs. intended allocation

| Area | Estimated | Intended |
| --- | --- | --- |
| Data model and routes | 3h | 3h |
| Core UI (HTML forms, tables) | 2h | 2h |
| Permissions and pipeline rules | 2h | 2h |
| Reporting and alerts | 2h | 2h |
| Tests, docs, and deployment | 3h | 4h (includes this documentation update) |

I kept the interface intentionally plain and cut stretch ideas, custom design-system work, scheduling integration, and self-service candidate access. The highest-value proof is correctness: the server owns permissions, filtering, stage moves, and timeline writes. All six core workflow rules (apply, advance, reject, reinstate, assign interviewer, add feedback) are implemented and tested.

## Key design decisions documented in `docs/decisions.md`

- Server-rendered FastAPI instead of SPA/API
- SQLite for the runnable demo (migrate to Postgres for production)
- Stage changes through one `advance()` helper
- Reject as terminal state with `rejected_from` preservation
- Append-only event table for immutable timeline
- Stage-keyed alert dismissals
- No optional features shipped after core requirements
