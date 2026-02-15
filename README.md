# Backend README
This repository contains the serverless infrastructure and API logic for the Vanguard Controls Automation Tool (V-CAT).

## Step-by-Step Local Start
1. **Clone the repo**: `git clone https://github.com/mhxynh/vcat-backend.git`
2. **Install dependencies**: Run `python scripts/setup.py` to check your AWS credentials and install the necessary Python libraries.

    This script will
    - Verify that you have the AWS CLI installed.
    - Check if your machine is successfully authenticated with our AWS environment.
    - Guide you through the aws configure process if you aren't connected yet.
    - Automatically `run pip install -r requirements.txt`.

3. **Configure Environment**: We use a `.env` file to store sensitive database credentials. This file is git-ignored to keep our database secure.
    - Copy the example file: `cp .env.example .env`
    - Open `.env` and fill in the `DB_PASSWORD` provided in our team's #references channel.
      - Note: The host, name, and user are already pre-filled for our AWS RDS instance.

## Database Switching: Local vs. RDS
You can choose which database the backend talks to by editing your `.env` file.

### Option A: The "Sandbox" (Safe for testing)
Use this if you are working on database schema changes or don't have an active internet connection.
1. **Start your local Postgres**: Ensure PostgreSQL is running on your machine.
2. **Update** `.env`:
  ```
  DB_HOST=localhost
  DB_NAME=vcat_sandbox
  DB_USER=postgres
  DB_PASSWORD={LOCAL_POSTGRES_PASSWORD}
  ```
### Option B: The "Cloud" (Real team data)
Use this for end-to-end testing with the Frontend or to see live data.
1. **Update** `.env`:
  ```
  DB_HOST={RDS_HOSTNAME}
  DB_NAME=postgres
  DB_USER=postgres
  DB_PASSWORD={RDS_PASSWORD}
  ```

### Testing Procedures for PRs
When reviewing a PR, check which environment the author used.
- **If the PR affects the schema**: You **MUST** test this against a **Local Sandbox** first. Never run untested `ALTER TABLE` or `DROP` commands against the shared RDS.
- **If the PR is a UI/Logic fix**: You can test against the **RDS** to ensure it works with our existing dataset.

## Backend Local Development
To test the backend locally or provide data to the Frontend:

  1. Build the project: `sam build`
  2. Start the local API: `sam local start-api`
      - The API will be available at [http://127.0.0.1:3000](http://127.0.0.1:3000).
      - Important: You must have Docker running for this command to work.

## Virtual Environment (`venv`)
While the backend actually runs inside a Docker container when you use `sam local start-api`, we still use a local `venv` for two critical reasons:
  1. Your Code Editor (IntelliSense)
  Without a `venv`, VS Code or PyCharm won't know where our Python libraries (like `psycopg2`) are located.
      - With venv: You get autocomplete, parameter hints, and zero "red squiggly lines" under your imports.
      - Without venv: Your editor will think your code is broken because it can't "see" inside the Docker container.

  2. Local Utility Scripts
  Our `setup.py` script run directly on your machine, not inside Docker. These scripts need a local environment where dependencies are installed so they can verify your AWS connection and RDS access quickly.
      - Docker runs the API
      - The venv runs your tools and helps you write code

The `setup.py` script creates the venv for you, but you need to activate it in your terminal to use it:
- Windows: .\venv\Scripts\activate
- Mac/Linux: source venv/bin/activate

Once activated, your terminal prompt will show `(venv)`, letting you know you're using the project-specific tools.

## PR Review Checklist
Before approving a Backend PR, please verify:
- [ ] Environment Check: Ensure your `.env` is set up. If you haven't pulled in a while, `run python scripts/setup.py` again to ensure no new dependencies were added.
- [ ] Schema Verification: If the PR includes database changes, verify them by running a manual query or checking the `template.yaml`.
- [ ] Local API Test: Start the API and use Postman (or the Frontend) to hit the modified endpoints.
- [ ] Log Monitoring: Watch the terminal where `sam local start-api` is running. Any Python errors or `psycopg2` connection failures will appear there.
