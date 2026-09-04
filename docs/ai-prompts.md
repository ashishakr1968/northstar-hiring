# AI prompt record

## Initial scaffold

> Build a small, self-contained FastAPI hiring pipeline in an empty workspace.
> Prioritize server-side authorization, SQLite data modeling, all required
> workflow rules, seeded demo data, and concise documentation.

I started with this prompt to create the project structure and a first route
outline. It gave me a basic fastapp with a couple of routes and the SQLite
schema creations. From there I checked each requirement against the brief and
filled in the missing pieces: bulk result handling, alert dismissal, CSV
export, and the full set of form routes.

## Rule check

> Audit the proposed pipeline behavior for rejection and reinstatement edge
> cases. A rejected candidate must return to the exact previous stage, and
> bulk action results must be per candidate.

This was the first rule I audited, and it highlighted the biggest schema
change I needed to make. The first draft treated a rejected candidate as simply
inactive — no persisted prior-stage value. I had to add the `rejected_from`
column to the `applications` table and make rejection/reinstatement events
explicit. Getting this right meant the reinstate workflow actually works: a
candidate rejected from "Interview" can be reinstated back to "Interview",
not just blindly reset to "Applied".

I also checked that bulk actions produce per-candidate results, so advancing
or rejecting one application never blocks the others. Each application is
evaluated independently in the bulk loop, and the results are collected and
displayed as a table.

## Documentation pass

> Draft an architecture and schema explanation that makes trade-offs easy to
> defend in a hiring assignment; distinguish production hardening from
> deliberate demo scope.

I wrote the architecture and schema docs so someone reviewing this project
could quickly understand the trade-offs: why SQLite instead of Postgres, why
server-rendered HTML instead of an SPA, which features were deliberately cut,
and which are just postponed until after the core goals are met.

I verified the text against the implemented tables and routes, then removed
any claims about features that weren't actually implemented. It's easy to
overpromise in documentation, so I made sure every claim maps to a real
route or table column.

## Deployment troubleshooting

> What to do if the deployed app returns 500 Internal Server Error.

I've been there — you deploy to Render (or any Python host), hit the URL,
and get a 500 instead of the login page. After a few deployments I distilled
the common causes:

On Render's free tier, the most common culprit is the
`DATABASE_PATH` environment variable not being set. The app defaults to
`pipeline.db` in the current working directory, but Render's filesystem is
ephemeral — the database disappears between deploys or after the first sleep
cycle. The fix: set `DATABASE_PATH=/var/data/pipeline.db` (or any persistent
path) in the Render dashboard under Environment Variables.

Other causes that caught me out:

- The `@app.on_event("startup")` decorator is deprecated in FastAPI 0.121.0+
  (it still works, but you'll see deprecation warnings in the logs). Consider
  migrating to `lifespan` event handlers if you want clean logs.

- The service trying to bind to an unavailable port. Render provides a `$PORT`
  environment variable, and the Dockerfile uses `${PORT}`, but if the variable
  isn't passed through correctly the app can fail to start.

- First request after cold start taking 1–2 minutes to initialize the
  SQLite connection and run `init_db()`. This is normal — just give it a moment.

I added this troubleshooting section to `SUBMISSION.md` after encountering
these issues during my own Render deployment. If you're getting a 500 on
first load, check these three things before digging into stack traces.

## What I'd do differently next time

- Start with `lifespan` instead of `on_event` to avoid the deprecation
  warnings entirely.
- Set the database path env var locally too, so `export DATABASE_PATH=pipeline.db`
  becomes second nature and I won't forget it on Render.
- Write the AI prompts as I go, not after the fact. It's much easier to
  capture the reasoning while it's fresh than to retroactively explain why
  I made certain schema choices.
