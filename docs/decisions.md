# Decisions

1. **Server-rendered FastAPI instead of a separate SPA/API.** I chose fewer moving parts and server-owned queries under a short time budget. A React client was rejected because it would duplicate state/query work without improving a workflow app where the primary output is HTML, not JSON.

2. **SQLite for the runnable demo.** It makes a clean clone usable immediately. I rejected requiring an account or managed database for review; the schema remains conventional enough to move to Postgres (and the schema doc shows the migration path with recommended indexes).

3. **Stage changes through one helper.** `advance()` is used for both individual and bulk actions, avoiding two subtly different transition rules. Direct arbitrary stage editing was rejected because it would bypass business rules and alert dismissal logic.

4. **Reject is a separate terminal state with `rejected_from`.** This preserves the exact reinstatement location. Resetting to Applied would be simpler but destroys meaningful pipeline history (the `rejected_from` field is essential for the reinstate workflow).

5. **Append-only event table for timeline and feedback.** I rejected editable feedback records because the brief requires history that cannot be rewritten. Corrections should be a new event, not an alteration of an existing one. This also simplifies the API: POST /feedback adds a row; there is no PUT/patch for feedback.

6. **Stage-keyed alert dismissals.** My first thought was one dismissal flag per application, but that would suppress future alerts after a stage move. I reversed it: a dismissal belongs to the application and current stage pair, and the `advance()` function clears old dismissals when the application moves to a new stage. This ensures alerts can re-fire if a candidate moves back to a previously-dismissed stage.

7. **No optional feature.** I chose to stop after the required surface so that core behavior and documentation stay explainable. Stretch ideas (scheduling, email, resume parsing, scorecards, custom design system) were intentionally deferred.

8. **Environment variable for database path.** Added `DATABASE_PATH` env var support so the app works locally (`pipeline.db`) and on Render (set to `/var/data/pipeline.db` or a persistent volume path). This was a late addition that avoided the most common deployment failure (500 error on first Render request).
