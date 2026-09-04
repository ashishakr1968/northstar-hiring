# Plan and Execution Record

I initially planned to complete the project in around 12 hours, but I ended up spending about 16 hours in total. The extra time mainly went into testing, documentation, and deployment troubleshooting. I divided the work into six main sessions and tried to build the project in an order where the basic data and workflow rules were working before moving on to reporting, alerts, and deployment.

## How I Broke the Work Into Sessions

1. **Data model and authentication** — I set up the SQLite database, user model, password hashing, login form, and authentication. I also added seed data for the recruiter and interviewer accounts, job openings, and applications so I could test the application while building it.

2. **Openings and applications** — I added the basic functionality for creating, viewing, editing, and deleting job openings and applications. Applications also got their stage information so I could start testing the hiring pipeline.

3. **Pipeline and permissions** — I implemented the stage transition rules, rejection and reinstatement, interviewer assignments, and role-based access. I also added the `advance()` helper so that stage changes use the same rules for individual and bulk actions.

4. **Search, bulk actions, and export** — I added server-side search, filtering, sorting, and pagination. I also added bulk advance/reject actions and CSV export for the pipeline data.

5. **Dashboard and alerts** — I worked on the dashboard, reporting, and stalled-application alerts. This included the pipeline metrics, source reporting, applications by opening and stage, weekly application volume, and alert dismissal.

6. **Testing, documentation, and deployment** — I finished the tests and documentation, prepared the Docker setup, and deployed the application. I also added the `DATABASE_PATH` environment variable and spent time troubleshooting deployment issues.

## Why I Used This Order

I wanted the database and authentication to be working before building the rest of the application because all the other features depend on them. I then worked on the pipeline rules before the dashboard so that the dashboard would be based on the correct application states.

After the main workflow was working, I added search, bulk actions, export, reporting, and alerts. Testing and documentation came towards the end because it was easier to check and document the final implementation once the application was working end-to-end.

## Estimated vs. Actual Time

| Area | Estimated | Actual |
| --- | ---: | ---: |
| Data model and routes | 3h | 3h |
| Core UI (HTML forms, tables) | 2h | 2h |
| Permissions and pipeline rules | 2h | 3h |
| Reporting and alerts | 2h | 2h |
| Tests, documentation, and deployment | 3h | 6h |
| **Total** | **12h** | **16h** |

The original estimate was around 12 hours, but the project took about 16 hours in total. The main difference was the final testing, documentation, and deployment work. I spent more time than expected checking the application after deployment and fixing configuration issues. I also spent additional time making sure the documentation matched the final implementation.

## What I Cut When I Ran Short on Time

I decided to focus on the required features rather than adding extra functionality. Some of the features I considered but did not implement were:

- **Public careers portal:** This would have added a separate candidate-facing part of the application that was not required for the assignment.

- **Resume parsing and document upload:** This would require additional file handling, storage, and validation.

- **Email notifications:** Setting up SMTP, email templates, and delivery handling would have taken time without directly improving the required workflow.

- **External calendar integration:** Integrating Google or Outlook calendars would add OAuth and external API dependencies.

- **Automated interview scheduling:** This would require handling availability, time zones, conflicts, and notifications.

- **Candidate self-service accounts:** Candidate accounts and password-reset functionality were outside the scope of the assignment.

- **Advanced analytics:** I kept the dashboard focused on the required metrics instead of adding more detailed conversion and time-in-stage analysis.

- **Managed production database:** I kept SQLite for the runnable demo because it makes the project easier to set up and review.

- **Custom design system:** I focused on making the interface functional and responsive rather than spending a large part of the available time on visual design.

The main idea was to make sure the required workflow was working before adding optional features. Given the time limit, I felt this was a better use of the available time.

## If I Had Another 12 Hours

If I had another 12 hours, I would mainly use it to improve the parts that were kept simple for the demo. I would consider moving the database to PostgreSQL, improving the password-hashing setup, adding email notifications for important stage changes, improving the UI and design, and adding more tests around permissions, bulk actions, and edge cases.

I would also spend more time on deployment and production configuration so that the application would be easier to operate outside the assignment environment.
