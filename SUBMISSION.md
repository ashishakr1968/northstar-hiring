# Submission

- Repository: https://github.com/ashishakr1968/northstar-hiring
- Live application: https://northstar-hiring.onrender.com
- The local demo is seeded at first start.

## Demo credentials

| Role | Email | Password |
| --- | --- | --- |
| Recruiter | recruiter@northstar.test | `demo-password` |
| Interviewer | interviewer@northstar.test | `demo-password` |

### Deployment

This application is deployed on Render.com (free tier). See live URL above.

**Render.com characteristics:**
- Free tier: 750 hours/month, services sleep after 15 min of inactivity
- First load may take 1-2 minutes to wake from sleep
- Docker-based deployment from GitHub repository
- Environment variable: `DATABASE_PATH=pipeline.db`
- Critical: set `DATABASE_PATH` to a persistent volume path (e.g., `/var/data/pipeline.db`) for database persistence across deploys

**Alternative deployment:**
- PythonAnywhere, Railway, or any Python-compatible free tier

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

## Troubleshooting internal server errors

If you encounter a 500 Internal Server Error on deployment:

1. **Database path not set**: Render's free tier has an ephemeral filesystem. Set the `DATABASE_PATH` environment variable to a persistent path like `/var/data/pipeline.db`.

2. **Application startup**: The `@app.on_event("startup")` decorator is deprecated in FastAPI 0.121.0+. It still works but may show warnings. Consider migrating to `lifespan` event handlers.

3. **Cold start delay**: First request after service wakes from sleep may take 1-2 minutes to initialize the database.

4. **Bind address**: Ensure the app binds to `0.0.0.0` and uses the `$PORT` environment variable as specified in the Dockerfile.
```
