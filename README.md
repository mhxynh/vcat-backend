# Backend README

This repository contains the serverless infrastructure and API logic for the Vanguard Controls Automation Tool (V-CAT).

## Docker Local Stack

For full-stack local development, clone the backend and frontend repositories as siblings:

```text
vcats/
  vcat-backend/
  vcat-frontend/
```

Then start the full local stack from this backend repository:

```bash
docker compose up --build
```

The frontend container loads Cognito values from `../vcat-frontend/.env`, so make sure that file contains real `REACT_APP_USER_POOL_ID` and `REACT_APP_APP_CLIENT_ID` values before logging in.

This starts:

- Postgres at `localhost:5432`
- Backend SAM local API at `http://localhost:3001`
- Frontend React app at `http://localhost:3000`

The first startup can take a little longer because compose builds the local Lambda invoke image and the backend container warms the core local SAM API routes before the frontend starts. To warm every mounted route before the frontend starts, run with `WARM_BACKEND_ROUTES=all docker compose up --build`; to only wait until SAM is listening, use `WARM_BACKEND_ROUTES=off`.

Postgres is initialized from `database/schema.sql` and `database/seed.sql` the first time the Docker volume is created. Cognito is not containerized; the frontend and backend continue to use the AWS-hosted Cognito configuration.

For Docker local development, compose builds a `vcat-backend-lambda-local` invoke image containing the shared Python dependencies that normally live in `CommonDependencyLayer`. The backend entrypoint generates `.docker-sam/docker-template.yaml` from `template.yaml`, removes that local layer from the Docker-only template, and runs `sam local start-api` directly against the source folders. SAM launches Lambda runtime containers through Docker, so the compose service mounts the Docker socket, joins those Lambda containers to the `vcat-dev` network, and uses `host.docker.internal` for SAM-to-Lambda runtime traffic. The Docker command uses SAM's `docker` config environment so it does not inherit the default eager warm-container setting from `samconfig.toml`.

The backend entrypoint derives SAM's Docker-visible `.docker-sam` path from the `/app` bind mount. If that path is incorrect for your Docker engine, set `SAM_DOCKER_VOLUME_BASEDIR` manually, then rerun `docker compose up --build`.

To verify the running Docker stack, run:

```bash
python scripts/docker_smoke_test.py
```

The smoke test checks the frontend, backend API, key read routes, a temporary create/update/delete workflow, and the export/import/help-media URL routes. It deletes its temporary data before exiting.

## Step-by-Step Local Start

1. **Clone the repo**: `git clone https://github.com/mhxynh/vcat-backend.git`
2. **Install dependencies**: Run `python scripts/setup.py` to check your AWS credentials and install the necessary Python libraries.

   This script will
   - Verify that you have the AWS CLI installed.
   - Check if your machine is successfully authenticated with our AWS environment.
   - Guide you through the aws configure process if you aren't connected yet.
   - Automatically `run pip install -r requirements.txt`.

3. **Configure Environment**: We use two files to manage secrets. This file is **git-ignored** to keep our database secure.
   - File 1: `.env` (Used by local utility scripts)
     - `cp .env.example .env`
     - Fill in the `DB_PASSWORD`
   - File 2: `env.json` (Used by Docker/SAM)
     - `cp env.json.example env.json`
     - Ensure the `DB_PASSWORD` matches your `.env`

## Local Database Setup (Sandbox)

If you are working on database schema changes or want to test without an internet connection, you need to initialize your local PostgreSQL "Sandbox."

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

## Backend Local Development

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

## Virtual Environment (`venv`)

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
