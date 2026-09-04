# Submission

- Repository: https://github.com/ashishakr1968/northstar-hiring
- Live application: Not deployed (runs locally with SQLite; see notes below).
- The local demo is seeded at first start.

## Demo credentials

| Role | Email | Password |
| --- | --- | --- |
| Recruiter | recruiter@northstar.test | `demo-password` |
| Interviewer | interviewer@northstar.test | `demo-password` |

The application uses SQLite locally. For a hosted deployment, mount persistent storage or swap the small data layer for managed Postgres. Free services may sleep after inactivity and can take a minute or more to wake.
