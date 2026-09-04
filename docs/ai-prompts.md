# AI Prompts

I used AI at a few points during the project, mainly when starting the application, checking some of the workflow rules, and preparing the documentation. I did not use the responses as the final implementation without checking them against the assignment.

## 1. Getting the initial structure working

### What I needed

I was starting with an empty workspace, so I first wanted a basic FastAPI application with SQLite, users, applications, the hiring stages, and some demo data.

### Prompt

> Build a small, self-contained FastAPI hiring pipeline in an empty workspace. Prioritize server-side authorization, SQLite data modeling, all required workflow rules, seeded demo data, and concise documentation.

### Result

This gave me the initial project structure and a basic `app.py`. It included the FastAPI setup, database initialization, login route, some of the tables, the pipeline stages, and the initial UI styling.

It was useful for getting started, but it was not something I could use as-is.

### Changes I made

While going through the code against the assignment, I noticed that the stage handling needed correction and that the application did not have a way to remember the stage before rejection.

I changed the pipeline to:

`Applied → Screening → Interview → Offer → Hired`

I also added `rejected_from` to the applications table. This became important later because reinstating a rejected candidate has to return them to the stage they were actually in before rejection.

---

## 2. Checking rejection and bulk actions

### What I needed

The rejection and reinstatement rules were one of the parts I wanted to check carefully. I also wanted to make sure that a problem with one candidate in a bulk operation would not stop the other candidates from being processed.

### Prompt

> Audit the proposed pipeline behavior for rejection and reinstatement edge cases. A rejected candidate must return to the exact previous stage, and bulk action results must be per candidate.

### Result

The response pointed out the need for a stored previous stage and suggested handling bulk actions separately for each application.

However, the first version of the reinstatement logic was not quite right. It could clear the stored previous stage too early, which would make it impossible to reliably return the candidate to the correct stage.

### Changes I made

I changed the rejection flow so that the current stage is stored in `rejected_from`.

For example:

`Interview → Rejected`

stores:

`rejected_from = Interview`

When the candidate is reinstated, the application uses that value:

`Rejected → Interview`

I also changed the bulk action handling so each application is checked separately and the result for each candidate is shown separately.

---

## 3. Reviewing the application rules

### What I needed

Once the main routes were working, I wanted to go through the assignment requirements and see whether there were any important rules that I had missed.

### Prompt

> Review the hiring pipeline requirements and identify the important business rules that should be enforced by the server rather than only by the UI.

### Result

This gave me a useful checklist for going through the application.

The main areas I checked were:

- User roles
- Stage transitions
- Rejection and reinstatement
- Candidate history
- Interviewer assignments
- Bulk actions
- Search and filtering
- Stalled candidates
- Dashboard information
- CSV export

I then checked these areas against the actual routes and database operations instead of relying only on the checklist.

---

## 4. Documentation

### What I needed

I wanted the documentation to explain the choices made in the project, especially why I used SQLite and a server-rendered application instead of adding a separate frontend and database service.

### Prompt

> Draft an architecture and schema explanation for a small FastAPI hiring pipeline. Explain the main design choices and distinguish between what is implemented for the demo and what would normally be added in a production system.

### Result

The response gave me a starting point for the architecture and schema documentation.

I went through it and removed or changed statements that did not match the actual code. I wanted the documentation to describe the project as it exists, rather than describing features that could be added later.

For example, I kept the explanation about using SQLite for a small self-contained application, but did not want the documentation to claim that features were implemented when they were not.

---

## 5. Deployment issue

### What I needed

After deploying the application, I ran into an Internal Server Error. I used a prompt to help narrow down the possible causes.

### Prompt

> What should I check if a deployed FastAPI application returns a 500 Internal Server Error on Render?

### Result

The response suggested checking the application logs, database configuration, startup behavior, and the host/port configuration.

This helped me focus on the deployment configuration instead of changing application logic without knowing what was actually failing.

I then checked the Render logs and the deployment configuration to identify the actual problem.

---

## 6. Final review

### What I needed

Before submitting, I wanted one final pass over the project to catch obvious gaps.

### Prompt

> Review the completed hiring pipeline against the assignment requirements and point out important missing functionality, edge cases, security issues, or documentation problems.

### Result

I used the response mainly as a checklist.

I went back through the application and manually checked the important parts, especially:

- Role restrictions
- Stage transitions
- Rejection and reinstatement
- Bulk operations
- History
- Interviewer access
- Stalled alerts
- Search and pagination
- CSV export
- Security
- Documentation

The final code was based on those checks and on the assignment requirements, rather than simply copying the review output.

## What I learned from using it

The useful part of AI assistance was getting a starting point and another way of looking at some of the edge cases.

The initial scaffold was helpful for getting the basic structure in place, but I still had to go through the code carefully. In particular, the rejection/reinstatement behavior showed that a seemingly small requirement can affect both the database schema and the application logic.

The `rejected_from` field and the per-candidate bulk results were two examples where I had to look beyond the initial implementation and make changes based on the actual requirement.

I also found that documentation needs to be checked against the code. It is easy for documentation to describe something as implemented when it is actually only an idea for future work, so I kept the final documentation limited to what is actually present in the project.
