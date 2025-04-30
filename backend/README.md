# ACI.dev Backend

[![Backend CI](https://github.com/aipotheosis-labs/aci/actions/workflows/backend.yml/badge.svg)](https://github.com/aipotheosis-labs/aci/actions/workflows/backend.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Overview

The backend component of ACI.dev provides the server infrastructure, API endpoints, database models, and integration libraries that enable over 600+ tool integrations with multi-tenant authentication and granular permissions.

- [ACI.dev Backend](#acidev-backend)
  - [Overview](#overview)
  - [Code Structure](#code-structure)
  - [Development Setup](#development-setup)
    - [Prerequisites](#prerequisites)
    - [Code Style](#code-style)
    - [IDE Configuration](#ide-configuration)
    - [Getting Started](#getting-started)
    - [Running Tests](#running-tests)
  - [Database Management](#database-management)
    - [Working with Migrations](#working-with-migrations)
  - [Webhooks (for local end-to-end development with frontend)](#webhooks-for-local-end-to-end-development-with-frontend)
  - [Admin CLI](#admin-cli)
  - [Contributing](#contributing)
  - [License](#license)

## Code Structure

The backend consists of several main components:

- **Server**: FastAPI application handling API requests, authentication, and tool executions
- **Database**: PostgreSQL with pgvector for vector similarity search
- **CLI**: Command-line interface for local testing and development
- **Common**: Shared code and utilities used across components

## Development Setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- `uv` package manager

### Code Style

We follow strict code quality standards:

- **Formatting & Linting**: We use `ruff` for code formatting and linting
- **Type Checking**: We use `mypy` for static type checking
- **Pre-commit Hooks**: Install with `pre-commit install`

### IDE Configuration

For VS Code users, configure Ruff formatter:

```json
{
    "[python]": {
      "editor.formatOnSave": true,
      "editor.defaultFormatter": "charliermarsh.ruff",
      "editor.codeActionsOnSave": {
        "source.organizeImports.ruff": "always"
      }
    }
}
```

### Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/aipotheosis-labs/aci.git
   cd aci/backend
   ```

2. Install dependencies and activate virtual environment:

   ```bash
   uv sync
   source .venv/bin/activate
   ```

3. Install `pre-commit` hooks:

   ```bash
   pre-commit install
   ```

4. Set up environment variables:

   ```bash
   cp .env.example .env
   ```

   There are 4 env vars you need to set in `.env`:

   - `SERVER_OPENAI_API_KEY`: create an API key yourself
   - `CLI_OPENAI_API_KEY`: create an API key yourself
   - `SERVER_PROPELAUTH_API_KEY`: we'll give you an API key if you are one of our approved
     contributors. You can also create a PropelAuth Org yourself. See the [Webhooks](#webhooks-for-local-end-to-end-development-with-frontend)
     section for how to get an API key once you have access to a PropelAuth Org.
   - `SERVER_SVIX_SIGNING_SECRET`: you don't need it if you aren't developing the dev
     portal. But if you are, complete the [Webhooks](#webhooks-for-local-end-to-end-development-with-frontend)
     section before moving on.

   Note: Most insensitive variables are already defined in `.env.shared`

5. Start services with Docker Compose:

   ```bash
   docker compose up --build
   ```

   This will start:
   - `server`: Backend API service
   - `db`: PostgreSQL database
   - `aws`: LocalStack for mocking AWS services
   - `runner`: Container for running commands like tests or database seeds

6. (Optional) Seed the database with sample data:

   ```bash
   docker compose exec runner ./scripts/seed_db.sh
   ```

7. (Optional) Connect to the database using a GUI client (e.g., `DBeaver`)

   - Parameters for the db connection can be found in the `.env.shared` file

8. Create a random API key for local development (step 6 also creates a random API key when you run the seed db script):

   ```bash
   docker compose exec runner python -m aci.cli create-random-api-key --visibility-access public
   ```

9. Access the API documentation at:

   ```bash
   http://localhost:8000/v1/notforhuman-docs
   ```

10. (Optional) If you are developing the dev portal, follow the instructions on [frontend README](../frontend/README.md) to start the dev portal.

### Running Tests

Ensure the `db` service is running and the database is empty (in case you have seeded the db in the previous steps) before running tests:

```bash
docker compose exec runner pytest
```

## Database Management

### Working with Migrations

When making changes to database models:

1. Check for detected changes:

   ```bash
   docker compose exec runner alembic check
   ```

2. Generate a migration:

   ```bash
   docker compose exec runner alembic revision --autogenerate -m "description of changes"
   ```

3. Manually review and edit the generated file in `database/alembic/versions/` if needed to add custom changes, e.g.,:
   - pgvector library imports
   - Index creation/deletion
   - Vector extension setup
   - Other database-specific operations

4. Apply the migration (to the local db):

   ```bash
   docker compose exec runner alembic upgrade head
   ```

5. To revert the latest migration:

   ```bash
   docker compose exec runner alembic downgrade -1
   ```

## Webhooks (for local end-to-end development with frontend)

If you are developing the dev portal, you would need a real `user` and `org` in the
PropelAuth test environment as well as a default `project` and `agent` in your local db.

Follow the steps here to set up the webhooks so that when you sign up on the PropelAuth
test environment, PropelAuth will notify your local server to create an org in the
PropelAuth test environment for you as well as creating a default project and agent in
the local db.

1. Install and set up ngrok:
   - Follow [ngrok's getting started guide](https://ngrok.com/docs/getting-started/?os=macos)
   - Expose your local server: `ngrok http http://localhost:8000`
   - Copy your public endpoint you just exposed from previous step and create a new endpoint in the [ngrok dashboard](https://dashboard.ngrok.com/endpoints) (e.g. <https://7c4c-2a06-5904-1e06-6a00-ddc6-68ce-ffae-8783.ngrok-free.app>)

2. Configure PropelAuth:
   - Go to the `aipolabs local` PropelAuth Org [dashboard](https://app.propelauth.com/proj/1b327933-ffbf-4a36-bd05-76cd896b0d56) if you have access, or create your own local dev
   organization yourself if you don't.
   - Go to the **Users** and **Organizations** tabs, delete your previously created user and organization. (Note: only delete your own user and org)
     ![delete user](./images/delete-user.png)
     ![delete org](./images/delete-org.png)
   - If you don't have a PropelAuth API key already, go to the **Backend Integration** tab and
     create an API key for the test environment, set it as `SERVER_PROPELAUTH_API_KEY`
     in `.env`.
    ![propelauth-api-key](./images/propelauth-api-key.png)
   - Go to the **Integrations** tab on the dashboard, click Webhooks. And click **Set Up Webhooks** for the **TEST ENV**, which will lead you to [Svix endpoints](https://app.svix.com/app_2uuG50X13IEu2cVRRL5fnXOeWWv/endpoints)
    page.
    ![webhook-setup](./images/webhook-setup.png)
   - Click `Add Endpoint`, put `<your_gnrok_public_endpoint>/v1/webhooks/auth/user-created` as the endpoint and subscribe to the `user.created` event. Hit Create.
    ![svix](./images/svix.png)
   - Copy the `Signing Secret` of the endpoint and set it as `SERVER_SVIX_SIGNING_SECRET`
    in `.env`.
    ![svix](./images/svix-signing-secret.png)
   - Go back to the [Getting Started](#getting-started) section step 5 to bring up
     docker compose

## Admin CLI

The CLI module is an internal admin tool for ACI to manage apps, functions, users, etc.
For local development, the commands can be executed via the `runner` container.

```bash
docker compose exec runner python -m aci.cli upsert-app --app-file ./apps/brave_search/app.json --secrets-file ./apps/brave_search/.app.secrets.json
```

## Contributing

Please refer to the [Contributing Guide](../CONTRIBUTING.md) for details on making contributions to this project.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.
