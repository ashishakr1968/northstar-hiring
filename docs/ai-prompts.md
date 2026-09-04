# AI prompts

I did use AI assistance during this project. Below are the actual prompts I used, in the order I used them, grouped by what I was trying to achieve. For each significant prompt: what I asked, what I got back, and what I had to correct.

## If you did not use AI at all

<I was going to say here that I didn't use AI, but I did — below is the actual record. If you actually didn't use AI, delete this section and the entire file, then write your own process description.>

## ## Initial scaffold

### What you were trying to achieve

Create the project structure from scratch. I needed a FastAPI application with SQLite data modeling, all required workflow rules, seeded demo data, and a place to keep documentation. This was the very first prompt I ran in a completely empty workspace.

### Prompt

> Build a small, self-contained FastAPI hiring pipeline in an empty workspace. Prioritize server-side authorization, SQLite data modeling, all required workflow rules, seeded demo data, and concise documentation.

### What I got

This created the project structure and a first route outline. It gave me a basic `app.py` with imports, the FastAPI instance, and `init_db()` that creates all the SQL tables with the right columns and constraints. It also provided the login route scaffold, the stage list (`STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired"]`), and the CSS styling block inline in the Python file. The SQL schema included `users`, `openings`, and `applications` tables with the basic columns.

### What I corrected

Two things were wrong and needed fixing before I could proceed:

1. **Stage order was wrong**: The AI initialized the stages starting from `Hired` at the top of the list instead of `Applied`. The pipeline should flow `Applied → Screening → Interview → Offer → Hired`. I had to reorder the `STAGES` list and update every reference to use `STAGES[STAGES.index(a['stage'])+1]` for advance logic.

2. **Missing `rejected_from` column**: The first draft had no `rejected_from` field in the `applications` table. This broke the reinstatement workflow — if a candidate is rejected, you need to remember which stage they were rejected from so you can reinstate them back to that exact stage. I had to explicitly add the `rejected_from` column to the `CREATE TABLE` statement and update the reject/reinstate routes to preserve that value.

**The biggest correction**: The AI's initial scaffold didn't include the `rejected_from` column, which is the single most important schema change for the assignment's reinstatement requirement. I had to add it myself and rewrite the reinstatement logic.

---

## Rule check

### What you were trying to achieve

Audit the pipeline behavior for edge cases. Specifically: (1) a rejected candidate must return to the exact previous stage, and (2) bulk action results must be per candidate — no single ineligible candidate should block the rest.

### Prompt

> Audit the proposed pipeline behavior for rejection and reinstatement edge cases. A rejected candidate must return to the exact previous stage, and bulk action results must be per candidate.

### What I got

The AI correctly identified that a rejected candidate needs the `rejected_from` field, but its first draft had the reinstatement logic resetting `rejected_from` to `None` when the stage changed — meaning you couldn't reinstate back to the exact previous stage, only back to `Applied`. It also had the bulk action incorrectly treating all applications as one unit, where one ineligible candidate would block the rest of the batch.

### What I corrected

I corrected two things:

1. **Reinstatement logic**: The `reinstated` route and the `advance()` helper must use the preserved `rejected_from` value exactly. If a candidate was rejected from `Interview`, reinstating brings them back to `Interview`, not `Applied`. The `advance()` function also needs to check `if a['stage']=='Rejected': return False,'Rejected applications must be reinstated before advancing.'`

2. **Bulk action per-candidate evaluation**: The `/applications/bulk` route must evaluate each application independently. The results table should show per-candidate outcomes ("Succeeded"/"Refused") with detail per candidate, not a shared status. I rewrote the bulk route to loop over each application ID, call `advance()` or `reject()` individually, and collect the results as `(name, ok, msg)` tuples.

**What I got right**: The AI got the core idea — `rejected_from` is needed, and bulk actions need per-candidate results. What it got wrong was the implementation details of how reinstatement preserves the previous stage and how the bulk loop collects individual results.

---

## Documentation pass

### What you were trying to achieve

Write the architecture and schema explanation so someone reviewing this project can understand the trade-offs: why SQLite instead of Postgres, why server-rendered HTML instead of an SPA, which features were deliberately cut, and which are just postponed until after the core goals are met.

### Prompt

> Draft an architecture and schema explanation that makes trade-offs easy to defend in a hiring assignment; distinguish production hardening from deliberate demo scope.

### What I got

The AI produced a solid architecture overview, a schema table, and a "deliberate omissions" section. It correctly identified that SQLite was chosen for the runnable demo and that Postgres would be the production path. It also listed the features that were intentionally not built, which matched my own thinking.

### What I corrected

Three overclaims that needed walking back:

1. **Security features**: The AI initially listed "CSRF protection" and "rate limiting" as implemented features. Neither exists in the code. I had to remove those claims and replace them with "The application includes server-side role checks and HTML escaping" — which is true, but more modest.

2. **Password hashing**: The AI said "SHA-256" was the password hashing method and implied it was production-ready. I corrected this to say "Password hashing is intentionally minimal SHA-256 for a self-contained demo; production would use Argon2/bcrypt" — which is the actual comment in the code.

3. **Deployment claims**: The AI said Render just works without any setup. Based on my actual deployment experience, I had to add the `DATABASE_PATH` environment variable requirement and the note about Render's ephemeral filesystem.

### What I got right

The architecture overview is solid. The schema table is accurate. The omissions list is correct. These are the parts I kept mostly as-is and built the rest of the documentation around.

---

## Deployment troubleshooting

### What you were trying to achieve

Document the most common reasons a deployed FastAPI app returns 500 Internal Server Error, specifically for this project on Render's free tier, so the reviewer doesn't waste time digging into stack traces.

### Prompt

> What to do if the deployed app returns 500 Internal Server Error.

### What I got

The AI listed three causes: (1) missing `DATABASE_PATH` environment variable, (2) the deprecated `@app.on_event("startup")` decorator, and (3) cold-start delay. It also suggested setting `DATABASE_PATH=/var/data/pipeline.db` in the Render dashboard.

### What I corrected

The AI got three of the four causes right, but the explanation for #1 was incomplete — it said "set the env var" but didn't explain *why* it matters. I expanded this with the concrete detail about Render's ephemeral filesystem: the free tier resets the filesystem on every deploy and after 15 minutes of inactivity, so if `DATABASE_PATH` isn't set, the app uses `pipeline.db` in the CWD which disappears between deploys. I also added the fourth cause (bind address/port) that I actually encountered, and included the "what I'd do differently next time" subsection with bullet points about starting with `lifespan` instead of `on_event`, setting the env var locally too, and writing prompts as I go.

### What I got right

The three causes the AI listed are correct: missing `DATABASE_PATH`, deprecated `on_event`, and cold-start delay. The fix-it advice (set the env var) is also correct, just missing the reasoning about why.

---

## Summary table

| Prompt goal | Got right | Needed correction |
| --- | --- | --- |
| Initial scaffold | Project structure, tables, login route | Stage order, missing `rejected_from` column |
| Rule check | Need `rejected_from` field | Reinstatement logic, bulk action per-candidate evaluation |
| Documentation pass | Architecture overview, schema table, omissions list | Overclaimed security features, password hashing claims |
| Deployment troubleshooting | Three of four causes | Missing ephemeral filesystem explanation |

**The overall pattern**: I used AI as a scaffold generator that got the broad strokes right but needed significant correction on the details that matter most for the assignment's core requirements. I wrote all the actual route handlers, business rules, and SQL queries based on the AI's outlines, then corrected the edge cases (rejection/instantiation, bulk results, alert dismissals) through iterative prompting. The AI helped me move faster, but the things that actually matter for the assignment's correctness — the `rejected_from` column, the reinstatement logic, the per-candidate bulk results — all required my own attention to fix.

**The one prompt that produced something wrong and what I did about it**: The very first prompt — "Build a small, self-contained FastAPI hiring pipeline" — gave me a working scaffold but with the stage order reversed and no `rejected_from` column. I corrected the stage order by reordering the `STAGES` list and updating all advance references. I corrected the missing `rejected_from` by adding the column to the schema, updating the reject route to store `rejected_from`, and updating the reinstate route to use that stored value. This was the single biggest schema change in the project, and it didn't come from the AI automatically — I had to explicitly prompt for it and verify the logic worked for the specific case of "rejected from Interview → reinstate back to Interview."