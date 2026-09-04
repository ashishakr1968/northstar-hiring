# Schema

## Table by table

| Table | Columns and types |
| --- | --- |
| `users` | `id INTEGER PRIMARY KEY`, `name TEXT NOT NULL`, `email TEXT UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`, `role TEXT NOT NULL CHECK(role IN ('recruiter','interviewer'))` |
| `openings` | `id INTEGER PRIMARY KEY`, `title TEXT NOT NULL`, `department TEXT NOT NULL`, `description TEXT NOT NULL`, `status TEXT NOT NULL CHECK(status IN ('open','archived'))`, `created_at TEXT`, `updated_at TEXT` |
| `applications` | `id INTEGER PRIMARY KEY`, `opening_id INTEGER NOT NULL REFERENCES openings(id)`, `candidate_name TEXT NOT NULL`, `email TEXT NOT NULL`, `source TEXT NOT NULL`, `stage TEXT NOT NULL`, `rejected_from TEXT`, `applied_at TEXT NOT NULL`, `stage_changed_at TEXT NOT NULL`, `updated_at TEXT NOT NULL` |
| `assignments` | `application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE`, `user_id INTEGER NOT NULL REFERENCES users(id)`, `PRIMARY KEY(application_id, user_id)` |
| `events` | `id INTEGER PRIMARY KEY`, `application_id INTEGER NOT NULL REFERENCES applications(id)`, `actor_id INTEGER REFERENCES users(id)`, `kind TEXT NOT NULL`, `detail TEXT NOT NULL`, `created_at TEXT NOT NULL` |
| `alert_dismissals` | `application_id INTEGER NOT NULL REFERENCES applications(id)`, `stage TEXT NOT NULL`, `dismissed_by INTEGER NOT NULL REFERENCES users(id)`, `PRIMARY KEY(application_id, stage)` |

## Relationships

| Relationship | Type | Description |
| --- | --- | --- |
| `openings → applications` | One-to-many | One opening has many applications. The `openings.id` is referenced by `applications.opening_id`. An opening can be archived, but its applications are retained. |
| `applications → events` | One-to-many | One application has many timeline events (creation, stage changes, rejection, reinstatement, feedback). The `events.application_id` links back to `applications.id`. Events are append-only — they are never edited or deleted. |
| `applications ↔ users` | Many-to-many through `assignments` | One application can have many interviewers (panel members), and one interviewer can be on many applications. The `assignments` table is the junction table with a composite primary key `(application_id, user_id)`, which prevents the same user from being assigned to the same application twice. |
| `assignments.application_id → applications.id` | Referential integrity | Foreign key with `ON DELETE CASCADE` — if an application is deleted, its panel assignments are also deleted. |
| `assignments.user_id → users.id` | Referential integrity | Foreign key — if a user is deleted, their panel assignments are also deleted. |
| `alert_dismissals.application_id → applications.id` | Referential integrity | Foreign key — an alert dismissal cannot exist without its application. |
| `alert_dismissals.dismissed_by → users.id` | Referential integrity | Foreign key — a dismissal record tracks which user dismissed it. |

## Constraints: database vs application

### Enforced by the database (via SQL constraints, foreign keys, check constraints)

| Constraint | Table/Column | Why at the database level? |
| --- | --- | --- |
| **Primary keys** | All tables (`id INTEGER PRIMARY KEY`) | Guarantees entity identity; enforced by SQLite/Python regardless of application code. |
| **Foreign keys** | `applications.opening_id → openings.id`; `assignments.application_id → applications.id`; `assignments.user_id → users.id`; `events.application_id → applications.id`; `alert_dismissals.application_id → applications.id`; `alert_dismissals.dismissed_by → users.id` | Prevents orphaned rows. An application cannot exist without an opening. An assignment cannot reference a non-existent application or user. This is enforced by SQLite's foreign key machinery (activated via `PRAGMA foreign_keys = ON` in the `db()` context manager). |
| **Check constraints** | `users.role CHECK(role IN ('recruiter','interviewer'))`; `openings.status CHECK(status IN ('open','archived'))`; `applications.stage` — though the actual stage validation (legal transitions) is in application code | The `IN (...)` list is a simple yes/no that the database can check instantly. It's a narrow, binary validation that doesn't depend on application state. |
| **UNIQUE constraints** | `users.email UNIQUE` | Ensures no two users share an email address. Critical for authentication — two recruiters can't have the same email. |

### Enforced by application code (because they depend on runtime state)

| Constraint | Table/Column | Why at the application level? |
| --- | --- | --- |
| **Legal stage transitions** | `applications.stage` progression: `Applied → Screening → Interview → Offer → Hired`; Rejected requires reinstatement before advancing | These rules depend on the current state of the application. Whether a candidate can advance from `Interview` to `Offer` is a question of "what stage is this application in right now?" — that's a runtime question, not a static schema constraint. The `advance()` helper function in `app.py` encodes these rules, and every route that changes stage calls it. |
| **Rejection/reinstatement logic** | `applications.rejected_from`; `applications.stage = 'Rejected'` | The `rejected_from` column stores which stage the candidate was rejected from. The reinstatement route uses this value to return the candidate to the exact previous stage. This logic is entirely in `app.py` (`/applications/{app_id}/reject` and `/applications/{app_id}/reinstate`) because it involves business rules about candidate experience, not just data validity. |
| **Source eligibility** | `applications.source` must be one of `SOURCE_OPTIONS` | The list of valid sources (`Referral`, `Careers page`, `LinkedIn`, `Agency`, `Inbound`) is defined in code and could change. The `source` column has a `NOT NULL` constraint, but the valid values list is managed in application code. |
| **Role-based access** | `users.role` (recruiter vs interviewer) | The `role` column is stored in the database, but the business rules about what a recruiter vs interviewer can do are all in `app.py` route handlers (`require(request, role)`, `app_for_user()`, etc.). The database just stores the label. |

**The line I drew**: If a constraint is a simple data validity check (unique email, valid status list, foreign key reference) that doesn't change based on application state, I put it in the database. If the constraint is a business rule that answers "what is allowed given the current state?" — stage transitions, rejection reinstatement, role permissions — I put it in application code. The trade-off is that the database can't prevent a bad state transition, but the application code can validate and give a meaningful error message instead of a raw SQL constraint violation.

## What I deliberately denormalised

The principal denormalisation in this schema is **`stage_changed_at` stored directly on the `applications` table**, derived from event timestamps rather than computed from the `events` table on every query.

**Why**: The stalled-alert query is the single most common and time-sensitive query in the app:

```sql
SELECT ... FROM applications a
WHERE a.stage != 'Rejected'
  AND datetime(a.stage_changed_at) < datetime('now', '-10 days')
  AND NOT EXISTS (
    SELECT 1 FROM alert_dismissals d
    WHERE d.application_id = a.id AND d.stage = a.stage
  )
```

If I had to compute `stage_changed_at` from the `events` table every time — e.g., `SELECT MAX(created_at) FROM events WHERE application_id = ? AND kind = 'stage'` — the dashboard and alerts page would need a correlated subquery or a join on potentially many event rows per application. By storing the timestamp directly on the application row, the query is a single-table scan with an index, which is orders of magnitude faster.

**The trade-off**: Inserting/updating an application requires two operations instead of one — update the application row AND insert an event row. The `advance()` helper does both in a single `db()` context manager transaction:

```python
con.execute("UPDATE applications SET stage=?, stage_changed_at=?, updated_at=? WHERE id=?", (...))
con.execute("INSERT INTO events(application_id,actor_id,kind,detail,created_at) VALUES(?,?,?,?,?)", (...))
```

I accepted this trade-off because (a) writes are far less frequent than reads (the dashboard is refreshed on every page load, but applications are advanced/rejected far less often), and (b) the code lives in one place (`advance()`), so there's exactly one source of truth for how `stage_changed_at` gets set.

## What would break first if this had 100× the data?

If I scaled this to 100x the current data volume (roughly 10,000+ applications, hundreds of interviewers, years of timeline events), the first things to suffer would be:

1. **The stalled-alert dashboard page** — even with the `stage_changed_at` denormalisation, the alert query scans the `applications` table. At 100x volume, that's thousands of rows being checked for the 10-day threshold. Without a proper index on `stage_changed_at`, every page load would slow noticeably. (I've recommended that index in the schema doc: `applications(stage_changed_at)`.)

2. **The applications list / search page** — the `applications` table is joined with `openings` and filtered by stage, source, search query, and pagination. At 100x volume, the `SELECT ... LIMIT 20 OFFSET ?` pattern would become slow, especially if the `OFFSET` gets large (page 10+). A production system would use seek-based pagination (`WHERE id > last_seen_id`) or move the analytics to a reporting store.

3. **The events timeline** — the `events` table grows linearly with each application interaction (stage change, rejection, reinstatement, feedback). At 100x volume, the timeline page for a single application could have hundreds of events. The current template just iterates over them, which is fine, but the `GET /applications/{app_id}` route fetches *all* events for that application with no limit. I've already limited the main applications list to 20 per page, but the timeline has no such guard.

4. **The assignments many-to-many table** — at 100x volume, the `assignments` table could grow large if many interviewers are assigned to many applications. The composite primary key `(application_id, user_id)` prevents duplicates, but queries like "which applications is this interviewer on?" (`SELECT * FROM assignments WHERE user_id = ?`) would need an index on `user_id` to stay fast. I've recommended that index in the schema doc: `assignments(user_id)`.

**The blunt instrument**: At 100x volume, SQLite would start to show its age — it doesn't support concurrent writes well, and the single-file database becomes a bottleneck. The schema is deliberately conventional enough to migrate to Postgres, where you'd get: proper concurrent write support, index-only queries, connection pooling, and the ability to partition the `events` table by date range. But for the assignment's scope and Render's free tier, SQLite is the pragmatic choice, and the denormalisations I've made (especially `stage_changed_at`) are tuned to the most common read patterns.