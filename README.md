# Aipolabs Core Components

![CI](https://github.com/aipotheosis-labs/aipolabs/actions/workflows/ci.yml/badge.svg)

## Project Structure

Currently only contains the server code, common (shared code) and cli,
but can be extended to include more services (e.g., separate admin server, sdk, etc.) as a monorepo if needed.

## Server

Follow all guidelines below for setting up the development environment, running services and testing locally for the server.

<details>
  <summary>Setup</summary>

- Git clone the repo
- Python ^3.12
- Install `docker`
- Install `poetry`
- Activate virtual env: `poetry shell`
  - We use docker and docker compose to run components in a container, so using a virtual env is more for development purposes. (IDE, pytest, dev dependencies, etc.)
- Install dependencies: `poetry install`
- Coding style
  - all the following tools are part of `pyproject.toml` dev dependencies, and are automatically installed when running `poetry install`
  - use `ruff` to format and lint the code
  - use `mypy` to type check the code
  - use `pre-commit` to run the above tools as pre-commit hooks
- Install `pre-commit` hooks: `pre-commit install`
- Setup you preferred editor to use `Ruff` formatter
  - e.g., you might need to install `Ruff` formatter extension in VS Code, and configure the setting as below

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

</details>

<details>
  <summary>Local Development</summary>

- Set up `.env` file according to `.env.example`
  - Note that most of the variables needed are already set in the `.env.shared` file, that's why you don't need to set them in the `.env` file
- Use docker compose to run necessary services locally: `docker compose up --build`, which contains:
  - `server`: the backend service
  - `db`: the postgres db
  - `aws`: a local aws mock with `localstack` (this `aws` service was added because of `Agent Secrets Manager`)
  - `runner`: a staging host for running any commands, e.g., `pytest`, `seed db`, etc.
- (Optional) Connect to the database using a GUI client like `DBeaver`
  - Parameters for the db connection can be found in the `.env.shared` file
- (Optional) To seed the db with some data: `docker compose exec runner ./scripts/seed_db.sh`
- You can access the `Swagger UI` at `http://localhost:8000/v1/notforhuman-docs`
- To run `pytest`, make sure the db is empty (in case you have seeded the db before), and then: `docker compose exec runner pytest`

</details>

<details>
  <summary>If any changes are made to the database or it's models</summary>

- You need to generate a new migration, which will generate a new file in `database/alembic/versions/`
- First check if new upgrade operations detected: `docker compose exec runner alembic check`
- If so, generate a new migration file: `docker compose exec runner alembic revision --autogenerate -m "<some message>"`
- (If needed) Change the generated file in `database/alembic/versions/` to add the necessary changes (that are not auto-generated), e.g.,:
  - import `pgvector` library for `Vector` type
  - create and drop necessary indexes
  - create and drop vector extension
  - ...
- Apply the changes to the **local** database: `docker compose exec runner alembic upgrade head`
- (If needed) you can undo the last change to the database: `docker compose exec runner alembic downgrade -1`

</details>

## CLI

Follow the [CLI instructions](aipolabs/cli/README.md) for the cli module.
