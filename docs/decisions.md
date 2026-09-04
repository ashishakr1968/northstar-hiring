# Decisions

I had around 12 hours for the project, so I focused on keeping the implementation simple and making sure the main requirements worked correctly. These are the main decisions I made while building it.

## Decision 1

- **Chose:** Server-rendered FastAPI
- **Rejected:** React frontend with a separate API
- **Why:** I decided not to add a separate React application because most of the required functionality could be handled directly by FastAPI. Search, filtering, sorting, pagination, and workflow actions are handled on the server. Using server-rendered HTML also meant fewer separate components to set up and maintain, which was useful given the time limit.

## Decision 2

- **Chose:** SQLite
- **Rejected:** A managed database such as PostgreSQL
- **Why:** I wanted the project to be easy to clone and run without requiring another service or account. SQLite was enough for the size of the demo and made the setup much simpler. The tables and relationships are kept fairly conventional, so moving to PostgreSQL later would still be possible if the application needed to scale.

## Decision 3

- **Chose:** One helper function for stage transitions
- **Rejected:** Separate logic for single and bulk actions
- **Why:** I initially had some transition checks in different places, which made it easier for the bulk actions to behave differently from the individual action. I changed this so both paths use the same `advance()` function. This keeps the stage-transition rules in one place and makes it harder for one workflow to accidentally bypass a rule.

## Decision 4

- **Chose:** Keep rejection as a separate state using `rejected_from`
- **Rejected:** Moving rejected candidates back to `Applied`
- **Why:** A rejected candidate needs to be reinstated to the stage where they were rejected. If I simply changed the stage back to `Applied`, that information would be lost. The `rejected_from` field stores the previous stage so reinstatement can return the candidate to the correct place in the pipeline.

## Decision 5

- **Chose:** Append-only events for history and feedback
- **Rejected:** Allowing existing feedback to be edited
- **Why:** The assignment requires the history to be immutable. Instead of changing an existing feedback entry, a new entry can be added. This keeps the previous record intact and gives a clearer timeline of what happened. There is no update operation for existing feedback.

## Decision 6

- **Chose:** Stage-specific alert dismissals
- **Rejected:** One permanent dismissal flag per application
- **Why:** I did not want dismissing an alert to hide future alerts for the candidate. For example, if an application is in Screening and the recruiter dismisses its stalled alert, that dismissal should not prevent an alert from appearing when the application later reaches Interview. The dismissal is therefore tied to the application and its stage. When the stage changes, the old dismissal is cleared.

## Decision 7

- **Chose:** Focus only on the required features
- **Rejected:** Adding optional features such as email notifications, resume parsing, scheduling integrations, or scorecards
- **Why:** With the time available, I decided it was more important to make the required workflows reliable than to add extra features. I focused on the main actions such as advancing candidates, rejecting and reinstating them, assigning interviewers, adding feedback, and managing the pipeline.

## Decision 8

- **Chose:** Use `DATABASE_PATH` as an environment variable
- **Rejected:** Hard-coding the database location
- **Why:** I added this after testing the application deployment. The default database file works well locally, but deployment environments can have different filesystem behaviour. Using `DATABASE_PATH` allows the database location to be changed without modifying the code. Locally it can still use `pipeline.db`, while the deployment can provide its own path through an environment variable.
