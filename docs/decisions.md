# Decisions

I started this project with a 12-hour constraint, so every decision was about maximizing what I could get working in a single weekend. Here are the trade-offs I made, in the order I made them.

## 1. Server-rendered FastAPI instead of a separate SPA/API

I toyed with the idea of a React front end calling a FastAPI backend via JSON endpoints. The appeal was "learn something new" and having a modern codebase. But the reality: a workflow app where the primary output is HTML meant a React client would duplicate all the state management, filtering, sorting, and pagination logic on the frontend that FastAPI already does on the backend. More moving parts, more surface area for bugs, and for what benefit? The end user sees the same HTML either way. I rejected the React approach and kept everything server-rendered. Fewer moving parts, one language (Python) for both logic and rendering, and the HTML is generated from the one source of truth (SQLite) rather than kept in sync across a client-server boundary.

## 2. SQLite for the runnable demo

I needed something that just works out of the box without requiring the reviewer to create an account, provision a database, or run migrations. SQLite fit the bill: the file just exists, the app reads it, done. I also knew the schema is conventional enough to migrate to Postgres later — the `docs/schema.md` file even lists the indexes and constraints you'd want to translate. The downside is obvious: no concurrent write support, limited advanced SQL, and eventually you'll hit the 10GB file size cap. But for a demo that needs to be cloned and run in under five minutes? SQLite is hard to beat.

## 3. Stage changes through one helper (`advance()`)

I initially had separate code paths for individual vs. bulk stage advances. The bulk path accidentally sidestepped some of the same checks the individual path had — things like "rejected applications can't advance" and "Hired is final." I consolidated both routes through a single `advance()` helper function. The trade-off: the function is a tiny bit more complex because it needs to handle both code paths, but the payoff is that there's exactly one source of truth for stage-transition rules. Both the single-application advance button and the bulk action modal use the same logic, which means fewer bugs and easier future maintenance.

## 4. Reject is a separate terminal state with `rejected_from`

This was the biggest schema decision. I considered just resetting a rejected application back to "Applied" — much simpler code. But that destroys the pipeline history: you lose track of where the candidate was rejected from, and the reinstate workflow becomes ambiguous. Adding a `rejected_from` column means "this candidate was rejected from Interview stage, so reinstating brings them back to Interview." It adds one column and a few lines of if/else, but it makes the reinstate workflow actually work correctly. I've seen too many hiring pipelines where reinstating a candidate means they re-apply from the beginning, losing all their previous data. This decision prevents that.

## 5. Append-only event table for timeline and feedback

I toyed with editable feedback records — let the user go in and patch their feedback note. But the brief requires history that cannot be rewritten. If an interviewer says " candidate was strong on technicals," and later realizes they should have mentioned "weak on culture fit," editing the old note feels wrong. Better to append a new event: "Feedback revised — added culture fit comment." This way the timeline is truly immutable, and the API stays simple: POST /feedback adds a row, there's no PUT or PATCH for existing feedback. The append-only approach also means the timeline page can just read events in order and never worry about concurrency conflicts on feedback records.

## 6. Stage-keyed alert dismissals

My first thought was one dismissal flag per application: "this alert has been dismissed, never show it again." But what happens when the candidate advances to the next stage? Does the dismissal follow them? If yes, you've suppressed a legitimate alert for the new stage. If no, the alert immediately re-appears and the user has to dismiss it all over again.

I reversed the model: a dismissal belongs to the application and its current stage pair. When `advance()` moves an application to a new stage, it clears old dismissals for the previous stage. This means:
- If a candidate was in "Interview" and the alert was dismissed, advancing to "Offer" clears that dismissal.
- If the candidate later moves back to "Interview" (unlikely but possible), the alert re-appears fresh, and the user can dismiss it again for the new context.

It's a subtle behavioral difference, but it makes the alerts actually useful rather than just a dismiss-and-forget mechanism.

## 7. No optional feature

I consciously stopped after the required surface area. Scheduling integration, email delivery, resume parsing, scorecards, a custom design system — all of these are valuable features, but each one adds complexity, testing surface area, and decision fatigue. My rule: if it's not in the ten core goals, it ships after the core is proven correct. That's how I ended up with a plain but functional UI instead of a polished one. The core workflows (apply, advance, reject, reinstate, assign interviewer, add feedback) are all solid, and that was the priority.

## 8. Environment variable for database path (`DATABASE_PATH`)

This was a late addition, born from frustration. After deploying to Render and hitting that 500 Internal Server Error on the first request, I realized the app defaults to `pipeline.db` in the current working directory, but Render's free tier has an ephemeral filesystem. The database disappears between deploys or after the first sleep cycle. Adding `DATABASE_PATH` as an environment variable meant the app works locally (`export DATABASE_PATH=pipeline.db`) and on Render (set the env var in the dashboard to a persistent path like `/var/data/pipeline.db`). It's a one-line change in `app.py` (`DB_PATH = os.environ.get("DATABASE_PATH", "pipeline.db")`), but it saved me from the most common deployment failure. I added it as decision #8 retroactively, but in hindsight it should have been decision #1 — environment configuration is foundational.

These aren't earth-shattering decisions, but each one came from a real problem I encountered while building this within the time constraint. The common thread: pick the simplest thing that could work, and document the trade-offs so future me (or anyone reviewing the code) knows why things are the way they are.
