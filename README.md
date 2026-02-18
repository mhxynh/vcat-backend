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

3. **Configure Environment**: We use two files to manage secrets. This file is git-ignored to keep our database secure.
   - File 1: `.env` (Used by local utility scripts)
     - `cp .env.example .env`
     - Fill in the `DB_PASSWORD` from the team’s `#references` channel.
   - File 2: `env.json` (Used by Docker/SAM)
     - `cp env.json.example env.json`
     - Ensure the `DB_PASSWORD` matches your `.env`

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
