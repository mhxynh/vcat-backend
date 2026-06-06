# Backend README — Vanguard Controls Automation Tool (V-CAT)

This repository contains the serverless infrastructure, database schemas, and API logic for the Vanguard Controls Automation Tool (V-CAT). V-CAT is designed to replace legacy spreadsheet-based tracking methods with centralized, automated compliance control workflows.

---

## Contents of the Deliverable

### Implemented Features & Architecture

- **Serverless Microservices Architecture:** Built using AWS Lambda and Amazon API Gateway to handle scalable back-end execution.
- **Data Persistence:** Centrally managed relational database via AWS RDS for all operational data, control tracking, and system state.
- **File Import/Export Engine:** Dedicated integration with Amazon S3 strictly utilized for importing compliance datasets and exporting generated reports.
- **Authentication & Access Control:** Native integration with Amazon Cognito User Pools for secure user authentication and session validation.
- **Automated Testing Framework:** Complete suite of unit, integration (via Postman collection runs), and End-to-End (E2E) testing configurations covering 495 total automated test cases.

### Features Not Implemented (Future Scope)

- **Native Containerized Authentication:** Amazon Cognito is not containerized locally; the system requires an active internet connection to communicate with AWS-hosted Cognito configurations during local development.
- **Automated RDS Migration Pipeline:** Database schema modifications currently require manual tracking and execution via regional configurations rather than automated CI/CD migrations.

### Known Open Issues & Workarounds

- **Eager Warm-Container Docker Conflict:** When executing `sam local start-api` natively outside of Docker Compose, SAM may attempt to enforce an eager container-warming policy defined in `samconfig.toml`, causing execution delays.
  - _Workaround:_ Use the provided Docker Compose environment (`docker compose up --build`), which passes specific flags to utilize SAM's custom `docker` configuration environment and bypasses eager warming.

---

## Docker Local Stack (Recommended Setup)

For full-stack local development, clone the backend and frontend repositories as sibling directories:

```text
vcats/
  vcat-backend/
  vcat-frontend/
```

Then start the full local stack from this backend repository:

```bash
docker compose up --build
```

> **Important**: The frontend container loads Cognito values from `../vcat-frontend/.env`, so make sure that file contains real `REACT_APP_USER_POOL_ID` and `REACT_APP_APP_CLIENT_ID` values before logging in.

### Running the Stack

This command initializes and starts:

- Postgres at `localhost:5432`
- Backend SAM local API at `http://localhost:3001`
- Frontend React app at `http://localhost:3000`

### Backend Routing Warmup Options

The first startup can take a little longer because compose builds the local Lambda invoke image and the backend container warms the core local SAM API routes before the frontend starts.

- To warm every mounted route before the frontend starts: `WARM_BACKEND_ROUTES=all docker compose up --build`
- To skip warmup and only wait until SAM is listening: W`ARM_BACKEND_ROUTES=off docker compose up --build`

### Verifying the Local Stack

To verify the health and data workflows of the running Docker stack, run:

```bash
python scripts/docker_smoke_test.py
```

The smoke test verifies frontend/backend connectivity, reads core control routes, executes a temporary CRUD workflow, tests S3 export/import routes, and automatically tears down its temporary test data before exiting.

## Step-by-Step Manual Local Start

1. **Clone the repo**: `git clone https://github.com/mhxynh/vcat-backend.git`
2. **Install dependencies**: Run `python scripts/setup.py` to audit your machine's AWS configurations and configure Python dependencies.

   This utility script will automatically verify your AWS CLI installation, check your connectivity to our AWS ecosystem, guide you through `aws configure` if needed, and execute `pip install -r requirements.txt`.

3. **Configure Environment**: We use two files to manage secrets. These files are **git-ignored** to keep our database secure.
   - File 1: `.env` (Used by local utility and maintenance scripts)
     - `cp .env.example .env`
     - Fill in the `DB_PASSWORD`
   - File 2: `env.json` (Used by SAM during local API simulation)
     - `cp env.json.example env.json`
     - Ensure the `DB_PASSWORD` matches your `.env`

## Local Database Setup (Sandbox)

If you are working on database schema changes or want to test without an internet connection, you need to initialize a local PostgreSQL sandbox.

Run these commands **once** to create and seed your local DB:

```
# 1. Create the database
createdb -U postgres vcat_sandbox

# 2. Initialize the schema
psql -U postgres -d vcat_sandbox -f database/schema.sql

# 3. Seed with initial data
psql -U postgres -d vcat_sandbox -f database/seed.sql

# 4. Verify setup (should return rows)
psql -d vcat_sandbox -U postgres -c "SELECT * FROM controls;"
```

## Backend Local Development Execution

To test the backend locally or provide data to the Frontend:

1. Ensure Docker is running
2. Activate your venv (if you're using one, more notes below on why you should use one)

- Windows: `.\venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

3. Build the project: `sam build`
4. Start the local API: `sam local start-api`
   - The API will be available at [http://127.0.0.1:3001](http://127.0.0.1:3001).
     - Note: If you change your code, you must `Ctrl+C`, then `sam build` again to see the changes.

### Testing Procedures for PRs

When reviewing a PR, check which environment the author used.

- **If the PR affects the schema**: You **MUST** test this against a **Local Sandbox** first. Never run untested `ALTER TABLE` or `DROP` commands against the shared RDS.
- **If the PR is a UI/Logic fix**: You can test against the **RDS** to ensure it works with our existing dataset.

## Virtual Environment (`venv`) Guidelines

While the backend actually runs inside a Docker container when you use `sam local start-api`, a local `venv` should still be used for two critical reasons:

1. Your Code Editor (IntelliSense)
   Without a `venv`, VS Code or PyCharm won't know where our Python libraries (like `psycopg2`) are located.
   - With `venv`: You get autocomplete, parameter hints, and zero "red squiggly lines" under your imports.
   - Without `venv`: Your editor will think your code is broken because it can't "see" inside the Docker container.

2. Local Utility Scripts
   Our `setup.py` script run directly on your machine, not inside Docker. These scripts need a local environment where dependencies are installed so they can verify your AWS connection and RDS access quickly.
   - Docker runs the API
   - The `venv` runs your tools and helps you write code

The `setup.py` script creates the venv for you, but you need to activate it in your terminal to use it:

- Windows: `.\venv\Scripts\activate`
- Mac/Linux: `source venv/bin/activate`

Once activated, your terminal prompt will show `(venv)`, letting you know you're using the project-specific tools.
