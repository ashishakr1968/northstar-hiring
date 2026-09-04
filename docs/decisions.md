# Decisions

I started this project with a 12-hour constraint, so every decision was about maximizing what I could get working in a single weekend. Here are the trade-offs I made, in the order I made them.

## Decision 1

- **Chose:** Server-rendered FastAPI instead of a separate SPA/API
- **Rejected:** React front end calling FastAPI backend via JSON endpoints
- **Why:** A workflow app where the primary output is HTML meant a React client would duplicate all state management, filtering, sorting, and pagination logic on the frontend that FastAPI already does on the backend. More moving parts, more surface area for bugs, and for what benefit? The end user sees the same HTML either way. I rejected the React approach and kept everything server-rendered. Fewer moving parts, one language (Python) for both logic and rendering, and the HTML is generated from the one source of truth (SQLite) rather than kept in sync across a client-server boundary.

## Decision 2

- **Chose:** SQLite for the runnable demo
- **Rejected:** Requiring an account or managed database for review
- **Why:** SQLite makes a clean clone usable immediately. I rejected requiring an account or managed database for review; the schema remains conventional enough to move to Postgres. The file just exists, the app reads it, done. No concurrent write support, limited advanced SQL, and eventually you'll hit the 10GB file size cap — but for a demo that needs to be cloned and run in under five minutes, SQLite is hard to beat.

## Decision 3

- **Chose:** Stage changes through one helper (`advance()`)
- **Rejected:** Separate code paths for individual vs. bulk stage advances
- **Why:** The bulk path accidentally sidestepped some of the same checks the individual path had — things like "rejected applications can't advance" and "Hired is final." I consolidated both routes through a single `advance()` helper function. The trade-off: the function is a tiny bit more complex because it needs to handle both code paths, but the payoff is that there's exactly one source of truth for stage-transition rules. Both the single-application advance button and the bulk action modal use the same logic, which means fewer bugs and easier future maintenance.

## Decision 4

- **Chose:** Reject is a separate terminal state with `rejected_from`
- **Rejected:** Resetting a rejected application back to "Applied"
- **Why:** This preserves the exact reinstatement location. Resetting to Applied would be simpler but destroys meaningful pipeline history (the `rejected_from` field is essential for the reinstate workflow). I've seen too many hiring pipelines where reinstating a candidate means they re-apply from the beginning, losing all their previous data. This decision prevents that.

## Decision 5

- **Chose:** Append-only event table for timeline and feedback
- **Rejected:** Editable feedback records
- **Why:** The brief requires history that cannot be rewritten. If an interviewer says " candidate was strong on technicals," and later realizes they should have mentioned "weak on culture fit," editing the old note feels wrong. Better to append a new event: "Feedback revised — added culture fit comment." This way the timeline is truly immutable, and the API stays simple: POST /feedback adds a row; there is no PUT/patch for feedback. This also simplifies the API: POST /feedback adds a row; there is no PUT/patch for feedback.

## Decision 6

- **Chose:** Stage-keyed alert dismissals
- **Rejected:** One dismissal flag per application
- **Why:** My first thought was one dismissal flag per application: "this alert has been dismissed, never show it again." But what happens when the candidate advances to the next stage? If the dismissal follows them, you've suppressed a legitimate alert for the new stage. If no, the alert immediately re-appears and the user has to dismiss it all over again. I reversed it: a dismissal belongs to the application and current stage pair, and the `advance()` function clears old dismissals when the application moves to a new stage. This ensures alerts can re-fire if a candidate moves back to a previously-dismissed stage.
- **Later reversed:** After further testing with the actual UI, the stage-keyed model proved essential for distinguishing between "alert dismissed at this stage" vs "alert dismissed forever." The stage-keyed approach lets users dismiss an alert for the current stage only, and it re-fires if the candidate moves back to that stage, which matches how the recruiter actually thinks about stale pipeline states.

## Decision 7

- **Chose:** No optional feature
- **Rejected:** Including scheduling integration, email delivery, resume parsing, scorecards, custom design system
- **Why:** I consciously stopped after the required surface area. All of these are valuable features, but each one adds complexity, testing surface area, and decision fatigue. My rule: if it's not in the ten core goals, it ships after the core is proven correct. That's how I ended up with a plain but functional UI instead of a polished one. The core workflows (apply, advance, reject, reinstate, assign interviewer, add feedback) are all solid, and that was the priority.

## Decision 8

- **Chose:** Environment variable for database path (`DATABASE_PATH`)
- **Rejected:** Not having an env var for database path
- **Why:** This was a late addition, born from frustration. After deploying to Render and hitting that 500 Internal Server Error on the first request, I realized the app defaults to `pipeline.db` in the current working directory, but Render's free tier has an ephemeral filesystem. The database disappears between deploys or after the first sleep cycle. Adding `DATABASE_PATH` as an environment variable meant the app works locally (`export DATABASE_PATH=pipeline.db`) and on Render (set the env var in the dashboard to a persistent path like `/var/data/pipeline.db`). It's a one-line change in `app.py` (`DB_PATH = os.environ.get("DATABASE_PATH", "pipeline.db")`), but it saved me from the most common deployment failure. I added it as decision #8 retroactively, but in hindsight it should have been decision #1 — environment configuration is foundational.