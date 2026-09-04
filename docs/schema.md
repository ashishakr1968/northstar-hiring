# Schema

| Table | Important columns and types |
| --- | --- |
| `users` | `id INTEGER PK`, `name TEXT NOT NULL`, `email TEXT UNIQUE NOT NULL`, `password_hash TEXT NOT NULL`, `role TEXT NOT NULL CHECK(role IN ('recruiter','interviewer'))` |
| `openings` | `id INTEGER PK`, `title TEXT NOT NULL`, `department TEXT NOT NULL`, `description TEXT NOT NULL`, `status TEXT NOT NULL CHECK(status IN ('open','archived'))`, `created_at TEXT`, `updated_at TEXT` |
| `applications` | `id INTEGER PK`, `opening_id INTEGER NOT NULL REFERENCES openings(id)`, `candidate_name TEXT NOT NULL`, `email TEXT NOT NULL`, `source TEXT NOT NULL`, `stage TEXT NOT NULL`, `rejected_from TEXT`, `applied_at TEXT NOT NULL`, `stage_changed_at TEXT NOT NULL`, `updated_at TEXT NOT NULL` |
| `assignments` | `application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE`, `user_id INTEGER NOT NULL REFERENCES users(id)`, `PRIMARY KEY(application_id, user_id)` |
| `events` | `id INTEGER PK`, `application_id INTEGER NOT NULL REFERENCES applications(id)`, `actor_id INTEGER REFERENCES users(id)`, `kind TEXT NOT NULL`, `detail TEXT NOT NULL`, `created_at TEXT NOT NULL` |
| `alert_dismissals` | `application_id INTEGER NOT NULL REFERENCES applications(id)`, `stage TEXT NOT NULL`, `dismissed_by INTEGER NOT NULL REFERENCES users(id)`, `PRIMARY KEY(application_id, stage)` |

## Relationships

- `openings → applications`: one-to-many (one opening has many applications)
- `applications → events`: one-to-many (one application has many timeline events)
- `applications ↔ users`: many-to-many through `assignments` (one application has many interviewers, one interviewer can be on many applications)
- `assignments` has a unique composite primary key preventing duplicate panel memberships
- Foreign keys prevent orphaned relationships (e.g., applications cannot exist without an opening)

## Denormalization and query optimization

`stage_changed_at` is stored directly on the `applications` table (derived from event timestamps) rather than computed from events. This denormalization makes the stalled-alert query efficient:

```sql
SELECT ... FROM applications a
WHERE a.stage != 'Rejected'
  AND datetime(a.stage_changed_at) < datetime('now', '-10 days')
  AND NOT EXISTS (
    SELECT 1 FROM alert_dismissals d
    WHERE d.application_id = a.id AND d.stage = a.stage
  )
ORDER BY a.stage_changed_at;
```

### Recommended indexes for production (Postgres migration)

- `applications(opening_id, stage, updated_at)` – supports filtering and dashboard lists
- `applications(stage_changed_at)` – supports stalled-alert queries
- `assignments(user_id)` – supports per-interviewer application views
- Consider moving analytics to a reporting store at 100× data volume

## Stage transition logic (enforced in application code)

| Current stage | Next stage | Notes |
| --- | --- | --- |
| Applied → Screening | Only via `advance()` |
| Screening → Interview | Only via `advance()` |
| Interview → Offer | Only via `advance()` |
| Offer → Hired | Only via `advance()` |
| Rejected → (any) | Requires reinstatement via `rejected_from` |
| Hired | Final state, no advance possible |

All role eligibility and legal stage transition sequencing are enforced in application code because they depend on the current application state. A production design could add database triggers as defense in depth.
