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
