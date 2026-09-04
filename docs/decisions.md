# Decisions

1. **Server-rendered FastAPI instead of a separate SPA/API.** I chose fewer moving parts and server-owned queries under a short time budget. A React client was rejected because it would duplicate state/query work without improving a workflow app.
2. **SQLite for the runnable demo.** It makes a clean clone usable immediately. I rejected requiring an account or managed database for review; the schema remains conventional enough to move to Postgres.
3. **Stage changes through one helper.** `advance()` is used for both individual and bulk actions, avoiding two subtly different transition rules. Direct arbitrary stage editing was rejected.
4. **Reject is a separate terminal state with `rejected_from`.** This preserves the exact reinstatement location. Resetting to Applied would be simpler but destroys meaningful pipeline history.
5. **Append-only event table for timeline and feedback.** I rejected editable feedback records because the brief requires history that cannot be rewritten. Corrections should be a new event, not an alteration.
6. **Stage-keyed alert dismissals.** My first thought was one dismissal flag per application, but that would suppress future alerts after a move. I reversed it: a dismissal belongs to the application and current stage, and movement clears old dismissals.
7. **No optional feature.** I chose to stop after the required surface so that core behavior and documentation stay explainable.
