# Schema

| Table | Important columns and types |
| --- | --- |
| `users` | `id INTEGER PK`, `name TEXT`, `email TEXT UNIQUE`, `password_hash TEXT`, `role TEXT CHECK` |
| `openings` | `id INTEGER PK`, `title TEXT`, `department TEXT`, `description TEXT`, `status TEXT CHECK`, timestamps |
| `applications` | `id INTEGER PK`, `opening_id INTEGER FK`, candidate details, `stage TEXT`, `rejected_from TEXT`, applied/stage/update timestamps |
| `assignments` | `application_id INTEGER FK`, `user_id INTEGER FK`, composite primary key |
| `events` | `id INTEGER PK`, `application_id INTEGER FK`, optional `actor_id INTEGER FK`, `kind TEXT`, `detail TEXT`, `created_at TEXT` |
| `alert_dismissals` | `application_id INTEGER FK`, `stage TEXT`, `dismissed_by INTEGER FK`, composite primary key |

`openings → applications` and `applications → events` are one-to-many. `applications ↔ users` is many-to-many through `assignments`. The assignment table's unique composite key prevents duplicate panel memberships. Foreign keys prevent orphaned relationships. Role eligibility and legal stage transition sequencing are enforced in application code, because they depend on the current application state; a production design could add triggers as defense in depth.

`stage_changed_at` is deliberately stored on the application even though events could derive it. This denormalization makes the stalled-alert query cheap and clear. At 100× data, the first risk is broad list/dashboard scans: add indexes on `applications(opening_id, stage, updated_at)`, `applications(stage_changed_at)`, `assignments(user_id)`, and move analytics to rollups or a reporting store.
