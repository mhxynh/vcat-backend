**STOP!** Before submitting, ensure your PR is **Atomic**. If this PR fixes a bug _and_ adds a feature, split it into two. Bloated PRs will be rejected without review.

## Jira Ticket

[DEV-XXX]()

## Summary of Changes

_Describe the changes briefly. What logic, endpoint, or database change does this PR introduce? (Bullet points are OK!)_

## Scope Control

_By checking these boxes, you confirm this PR is not "bloated":_

- [ ] **Single Purpose**: This PR addresses only the ticket listed above.
- [ ] **No Hidden Refactors**: I have NOT refactored or reformatted code in files unrelated to this ticket.
- [ ] **Template Accuracy**: If I changed `template.yaml`, I have verified only the necessary resources were added.

## Test Walkthrough (Required)

_Provide a step-by-step guide on how the reviewer can reproduce your test results locally._

1. **Command**: (e.g., Run `sam local start-api`)
2. **Request**: (e.g., Send POST to `/controls` with body `{...}`)
3. **Validation**: (e.g., Check Postgres for new row with `id: 502`)

## Visual Proof

Attach a screenshot of your terminal logs OR a snippet from your database client proving the successful execution.

## Database & Infrastructure

- [ ] **Schema Change**: Does this PR modify the database schema? (If yes, list the tables affected).
- [ ] **Environment Variables**: Does this require new keys in the `.env.example` and `env.json.example` file?
- [ ] **Dependencies**: I have added any new libraries to `requirements.txt`.

## Quality Standards

- [ ] **Black**: I ran `black .` to format the code.
- [ ] **Flake8**: I ran `flake8` and fixed any naming convention errors (snake_case).
- [ ] **DB Connection**: I verified the connection to the RDS/Sandbox DB.

## Reviewer’s "Quick Reject" Criteria

_Reviewers, you may click Request Changes immediately if:_

- The Scope Control boxes are checked but the PR contains unrelated changes.
- The Test Walkthrough is missing or non-functional.
- The PR includes "accidental" formatting changes to the entire `template.yaml`.
- There is no proof (logs) that the code actually executes.
- The author included multiple unrelated Lambda function changes in one PR.
