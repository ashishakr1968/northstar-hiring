Northstar Hiring
A server-rendered FastAPI application for managing a recruiting pipeline. Built in approximately 12 hours with a focus on server-side authorization, SQLite data modeling, all required workflow rules, seeded demo data, and concise documentation.
Live Demo
https://northstar-hiring.onrender.com
Features
- Application management: Create, read, edit, and delete job openings and applications
- Stage progression: Advance applications through stages (Applied → Screening → Interview → Offer → Hired)
- Rejection workflow: Reject candidates with rejected_from tracking for proper reinstatement
- Interviewer assignment: Assign interviewers to applications with permission checks
- Feedback system: Append-only timeline events for immutable interview feedback
- Alert system: Stalled application alerts after 10 days in the same stage
- Bulk actions: Advance or reject multiple applications simultaneously
- CSV export: Export pipeline data for reporting
- Source reporting: Distribution of candidates by source (Referral, Careers page, LinkedIn, Agency, Inbound)
Demo Credentials
Role	Email
Recruiter	recruiter@northstar.test (mailto:recruiter@northstar.test)
Interviewer	interviewer@northstar.test (mailto:interviewer@northstar.test)
Local Development
# Clone and install
git clone https://github.com/ashishakr1968/northstar-hiring.git
cd northstar-hiring

# Set database path and start
export DATABASE_PATH=pipeline.db
uvicorn app:app --host 0.0.0.0 --port 8000

# Open browser to http://localhost:8000
# Log in with recruiter@northstar.test / demo-password
Docker Deployment
# Build and run
docker build -t northstar-hiring .
docker run -p 8000:8000 -e DATABASE_PATH=pipeline.db northstar-hiring
Render-specific: Set DATABASE_PATH environment variable to a persistent path (e.g., /var/data/pipeline.db) in the Render dashboard. The free tier has an ephemeral filesystem, so the database won't persist without this setting.
Project Structure
app.py              # FastAPI app with all routes, authentication, and rendering
Dockerfile          # Container configuration
requirements.txt   # Dependencies: fastapi, uvicorn, python-multipart
docs/               # Architecture, schema, decisions, plan, AI prompts
SUBMISSION.md      # Deployment details and troubleshooting
pipeline.db        # SQLite database (created on first run)
Troubleshooting
Internal Server Error on Render: Set DATABASE_PATH env var to /var/data/pipeline.db or another persistent path. The app defaults to pipeline.db in the working directory, but Render's free tier has an ephemeral filesystem.
Cold start delay: First request after service wakes from sleep may take 1-2 minutes to initialize the database and run init_db().
Deprecated warning: @app.on_event("startup") is deprecated in FastAPI 0.121.0+. It still works but shows warnings. Consider migrating to lifespan event handlers.
Roadmap (future enhancements)
- Postgres migration with proper indexes
- Argon2/bcrypt password hashing
- API endpoints with OpenAPI/Swagger docs
- React or Vue SPA frontend
- Email notifications and scheduling integration
- Scorecards and candidate rating systems
