# Submission

- Repository: https://github.com/ashishakr1968/northstar-hiring
- Live application: Not deployed (runs locally with SQLite; see notes below).
- The local demo is seeded at first start.

## Demo credentials

| Role | Email | Password |
| --- | --- | --- |
| Recruiter | recruiter@northstar.test | `demo-password` |
| Interviewer | interviewer@northstar.test | `demo-password` |

### Deployment

This application can be deployed on free tiers. Recommended approach:

**Render.com** (as specified in the instructions):
1. Create a free account at render.com
2. New Web Service -> Docker
3. Connect GitHub repository: `ashishakr1968/northstar-hiring`
4. Set environment variable: `DATABASE_PATH=pipeline.db`
5. Service will auto-deploy from main branch
6. Free tier: 750 hours/month, services sleep after 15 min of inactivity
7. First load may take 1-2 minutes to wake from sleep

**Alternative: PythonAnywhere**
1. Create a free account at pythonanywhere.com
2. Set up a virtualenv with: fastapi, uvicorn, python-multipart
3. Copy app.py, requirements.txt, Dockerfile
4. Configure WSGI entry point
5. Set DATABASE_PATH=pipeline.db as a environment variable
6. Web app URL: https://<username>.pythonanywhere.com

**Note:** The application uses SQLite locally with `DATABASE_PATH` environment variable.
For production, swap the data layer for managed Postgres (Supabase, Railway, etc.).
Free services may sleep when idle and can take a minute or more to wake.

## Local development

```bash
# Start the application
cd northstar-hiring
export DATABASE_PATH=pipeline.db
uvicorn app:app --host 0.0.0.0 --port 8000

# Login credentials:
# - Recruiter: recruiter@northstar.test / demo-password
# - Interviewer: interviewer@northstar.test / demo-password
```
