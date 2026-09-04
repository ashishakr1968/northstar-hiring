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
