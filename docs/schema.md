# Schema

## Tables

| Table | Main columns | Purpose |
| --- | --- | --- |
| `users` | `id`, `name`, `email`, `password_hash`, `role` | Stores recruiter and interviewer accounts. |
| `openings` | `id`, `title`, `department`, `description`, `status`, `created_at`, `updated_at` | Stores job openings and whether they are open or archived. |
| `applications` | `id`, `opening_id`, `candidate_name`, `email`, `source`, `stage`, `rejected_from`, `applied_at`, `stage_changed_at`, `updated_at` | Stores candidates and their current position in the hiring pipeline. |
| `assignments` | `application_id`, `user_id` | Connects applications with interviewers. |
| `events` | `id`, `application_id`, `actor_id`, `kind`, `detail`, `created_at` | Stores the application timeline, including stage changes, rejection, reinstatement, and feedback. |
| `alert_dismissals` | `application_id`, `stage`, `dismissed_by` | Stores which stalled alerts have been dismissed for a particular application and stage. |

## Relationships

| Relationship | Type | Description |
| --- | --- | --- |
| `openings → applications` | One-to-many | One opening can have multiple applications. Applications keep their opening reference even if the opening is archived. |
| `applications → events` | One-to-many | An application can have multiple timeline events. Events are append-only. |
| `applications ↔ users` | Many-to-many | An application can have multiple interviewers, and an interviewer can be assigned to multiple applications. The `assignments` table handles this relationship. |
| `assignments.application_id → applications.id` | Foreign key | Ensures an assignment belongs to an existing application. Assignments are removed when the application is deleted. |
| `assignments.user_id → users.id` | Foreign key | Ensures an assignment refers to an existing user. |
| `events.application_id → applications.id` | Foreign key | Ensures every event belongs to an existing application. |
| `alert_dismissals.application_id → applications.id` | Foreign key | Ensures an alert dismissal belongs to an existing application. |
| `alert_dismissals.dismissed_by → users.id` | Foreign key | Records which user dismissed the alert. |

## Database Constraints vs Application Rules

I kept simple data validation in the database and the more complicated workflow rules in the application code.

### Enforced by the database

| Constraint | Example | Reason |
| --- | --- | --- |
| **Primary keys** | `id INTEGER PRIMARY KEY` | Gives each record a unique identifier. |
| **Foreign keys** | `applications.opening_id → openings.id` | Prevents records from referencing missing data. |
| **Unique email** | `users.email UNIQUE` | Prevents duplicate user accounts with the same email. |
| **Role check** | `users.role IN ('recruiter','interviewer')` | Makes sure only valid roles can be stored. |
| **Opening status check** | `openings.status IN ('open','archived')` | Keeps the opening status to the supported values. |
| **Required fields** | `NOT NULL` columns | Prevents important fields from being empty. |

SQLite foreign-key checking is enabled when the database connection is created.

### Enforced by application code

| Rule | Where it is handled | Reason |
| --- | --- | --- |
| **Stage transitions** | `advance()` in `app.py` | The allowed next stage depends on the application's current stage. |
| **Rejection** | Reject route and application logic | Rejection is only allowed from the appropriate pipeline stages. |
| **Reinstatement** | Reinstate route | The candidate needs to return to the stage stored in `rejected_from`. |
| **Source validation** | Application code using `SOURCE_OPTIONS` | The allowed source values are defined by the application. |
| **Role-based permissions** | `require()` and application access checks | What a recruiter or interviewer can do depends on the logged-in user. |
| **Interviewer assignment access** | Application-level checks | Interviewers should only see applications assigned to them. |

I used this split because database constraints are useful for basic data integrity, while rules such as stage transitions and permissions depend on the current application state and the logged-in user.

## Denormalisation

The main value I store directly on the `applications` table is `stage_changed_at`.

This could technically be calculated from the `events` table by finding the most recent stage-change event. I decided to store it directly because it is used for the stalled-application alerts.

For example, the application can directly check how long the candidate has been in the current stage without first searching through the event history.

The trade-off is that when a stage changes, the application needs to update `stage_changed_at` as well as create the corresponding event. I keep both operations together in the stage-transition logic so they stay consistent.

## What Would Become a Problem at 100× the Current Data?

The application is designed for the size of the assignment, but there are a few areas that would need improvement at much larger scale.

1. **Stalled-alert queries:** The application would need proper indexes on fields such as `stage_changed_at` to keep alert checks fast.

2. **Application search and pagination:** Large `OFFSET` values can become slower as the number of applications increases. A larger production system could use cursor/seek-based pagination instead.

3. **Events:** The events table will keep growing because history and feedback are append-only. For a much larger system, I would consider limiting timeline queries and adding appropriate indexes.

4. **Assignments:** Queries based on `user_id` would benefit from an index if the number of assignments became large.

5. **SQLite:** At significantly higher traffic, SQLite would eventually become a limitation, particularly for concurrent writes. I would move the application to PostgreSQL for a production-scale version.

For this assignment, I kept the schema simple and used SQLite because it makes the application easy to run and review. The tables are structured so that the database could be migrated to PostgreSQL later if needed.
