# Northstar Hiring

Northstar Hiring is a server-rendered FastAPI application for managing jobs, candidates, interviews, feedback, and hiring-stage transitions using SQLite.

**Live Demo:** https://northstar-hiring.onrender.com/login

## Features

* Create, edit, and delete jobs and applications
* Move candidates through `Applied → Screening → Interview → Offer → Hired`
* Reject and reinstate candidates using `rejected_from` tracking
* Assign interviewers with server-side permission checks
* Store interview feedback as append-only timeline events
* Flag applications stalled for 10+ days
* Bulk advance/reject applications
* Export pipeline data as CSV
* View candidate distribution by source

## Tech Stack

* Python
* FastAPI
* Uvicorn
* SQLite
* Server-rendered HTML
* Docker
* Render

## Run Locally

```bash
git clone https://github.com/ashishakr1968/northstar-hiring.git
cd northstar-hiring

pip install -r requirements.txt

export DATABASE_PATH=pipeline.db
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

### Demo Login

| Role        | Email                        |
| ----------- | ---------------------------- |
| Recruiter   | `recruiter@northstar.test`   |
| Interviewer | `interviewer@northstar.test` |

Password: `demo-password`

## Docker

```bash
docker build -t northstar-hiring .
docker run -p 8000:8000 -e DATABASE_PATH=pipeline.db northstar-hiring
```

## Project Structure

```text
app.py            # FastAPI application, routes, auth, and rendering
Dockerfile        # Docker configuration
requirements.txt  # Python dependencies
docs/             # Architecture and design notes
SUBMISSION.md     # Deployment and troubleshooting notes
pipeline.db       # SQLite database
```

## Known Limitations

* SQLite is intended for the current small-scale deployment.
* Render requires persistent storage for the SQLite database.
* Authentication and passwords are suitable for the demo, not production.
* Email notifications, scheduling, and candidate scorecards are not implemented.
