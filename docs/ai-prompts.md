# AI prompt record

## Initial scaffold

> Build a small, self-contained FastAPI hiring pipeline in an empty workspace. Prioritize server-side authorization, SQLite data modeling, all required workflow rules, seeded demo data, and concise documentation.

This created the structure and a first route outline. I then checked each requirement against the brief and filled in the missing bulk result, alert dismissal, CSV, and documentation behaviors.

## Rule check

> Audit the proposed pipeline behavior for rejection and reinstatement edge cases. A rejected candidate must return to the exact previous stage, and bulk action results must be per candidate.

The first draft incorrectly treated a rejected candidate as simply inactive and had no persisted prior-stage value. I changed the schema to include `rejected_from` and made rejection/reinstatement events explicit.

## Documentation pass

> Draft an architecture and schema explanation that makes trade-offs easy to defend in a hiring assignment; distinguish production hardening from deliberate demo scope.

I verified the text against the implemented tables and routes, then removed claims about features that were not implemented.

## Deployment troubleshooting

> What to do if the deployed app returns 500 Internal Server Error.

On Render.com free tier, the most common cause is the `DATABASE_PATH` environment variable not being set, causing the app to use a local `pipeline.db` in the ephemeral filesystem. Set `DATABASE_PATH=/var/data/pipeline.db` in the Render dashboard environment variables. Other causes include:

- The `@app.on_event("startup")` decorator being deprecated in FastAPI 0.121.0+ (still works, shows warnings)
- The service trying to bind to an unavailable port (ensure `$PORT` env var is respected)
- First request after cold start taking 1-2 minutes to initialize the SQLite connection

I added a troubleshooting section to `SUBMISSION.md` documenting these issues and their resolutions.
