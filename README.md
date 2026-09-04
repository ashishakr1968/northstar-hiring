# Hiring Pipeline

A server-rendered hiring pipeline built for Assignment 03. It uses FastAPI and SQLite so it can run with no external services.

## Run locally

```bash
python3 -m pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. The database is created and seeded automatically.

Demo accounts:

| Role | Email | Password |
| --- | --- | --- |
| Recruiter | recruiter@northstar.test | `demo-password` |
| Interviewer | interviewer@northstar.test | `demo-password` |

## Test

```bash
python3 -m unittest discover -s tests
```

See `SUBMISSION.md` for deployment notes and `docs/` for the project record.
