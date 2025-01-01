# Aipolabs CLI
Internal admin CLI tool for Aipolabs to manage apps, functions, users, etc.

## Setup
Follow the [setup instructions](../README.md) for the project.

## Commands
For commands that require database connection, make sure the database you are connecting to is running and the `CLI_DB_` variables in `.env` file is set up correctly.

<details>
  <summary>Create App</summary>
  
  - Create an app (without its functions) in the database, based on the app json file provided.
  - --secrets-file is optional, it is to temporarily store sensitive data such as default api key, default OAuth2 client secret etc, which will be used to populate the placeholders in app.json file.
  - Example files: [`google_calendar`](../../apps/google_calendar/app.json).

  ```bash
  python -m aipolabs.cli.aipolabs create-app --app-file ./apps/brave_search/app.json --secrets-file ./apps/brave_search/.app.secrets.json
  ```
</details>

<details>
  <summary>Create Functions</summary>
  
  - Create functions for an app in the database, based on the functions json file provided.
  - Note that the app must already exist in the database.
  - Example files: [`google_calendar`](../../apps/google_calendar/functions.json).

  ```bash
  python -m aipolabs.cli.aipolabs create-functions --functions-file ./apps/google_calendar/functions.json
  ```
</details>

<details>
  <summary>Create User</summary>
  
  - Create a user in the database.

  ```bash
  python -m aipolabs.cli.aipolabs create-user --auth-provider google --auth-user-id 1234567890 --name "John Doe" --email "john.doe@example.com" --profile-picture "https://example.com/profile.jpg" --plan free
  ```
</details>

<details>
  <summary>Create Project</summary>
  
  - Create a project in the database.
  - You need to create the user first before creating a project for the user.

  ```bash
  python -m aipolabs.cli.aipolabs create-project --project-name "My Project" --owner-type user --owner-id "8341edc4-eeb6-4e90-abe3-0051a9a7b9a5" --created-by "8341edc4-eeb6-4e90-abe3-0051a9a7b9a5" --visibility-access public
  ```
</details>

<details>
  <summary>Create Agent</summary>
  
  - Create an agent in the database.
  - You need to create the project first before creating an agent for the project.

  ```bash
  python -m aipolabs.cli.aipolabs create-agent --agent-name "My Agent" --description "My Agent Description" --project-id "51711368-ef40-4efc-a9ab-5d44dbe0d671" --created-by "8341edc4-eeb6-4e90-abe3-0051a9a7b9a5"
  ```
</details>

<details>
  <summary>Create Random API Key</summary>
  
  - Create an api key for random user and project and agent.
  Set the --visibility-access to private if you want to test with private apps and functions.

  ```bash
  python -m aipolabs.cli.aipolabs create-random-api-key --visibility-access public
  ```
</details>

<details>
  <summary>Fuzzy Test Function Execution</summary>

  - This command will test function execution with GPT-generated inputs.
  - You need to first create a test API key with `create-random-api-key` command.
  - Make sure you have a server running (locally or on the cloud). And set the `CLI_SERVER_URL` in `.env` file.

  ```bash
  python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name "my_function" --aipolabs-api-key "your_api_key_here"
  ```
</details>

## Testing
Follow all guidelines below for setting up the development environment, running services and testing locally
