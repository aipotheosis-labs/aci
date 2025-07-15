# ACI Integration Guide: Apps and Functions

## Overview

In the ACI framework, integrations are composed of two main components: **Apps** and **Functions**. Apps define external services (metadata, authentication), while Functions define their specific operations (endpoints, parameters, protocols). This guide provides a complete walkthrough for creating new integrations.

## 1. App Configuration (`app.json`)

The `app.json` file defines the foundational metadata and authentication for an integration.

### Step 1: Create App Directory and File

First, create a directory for your app and an empty `app.json` file inside it.

```bash
# Navigate to the apps directory
cd backend/apps

# Create a directory (use lowercase_with_underscores)
mkdir your_app_name

# Create the app.json file
touch your_app_name/app.json
```

### Step 2: Define App Schema

The `app.json` file contains the app's metadata and, crucially, its security schemes.

```json
{
  "name": "YOUR_APP_NAME",
  "display_name": "Your App Display Name",
  "logo": "https://example.com/logo.svg",
  "provider": "Company Name",
  "version": "1.0.0",
  "description": "Detailed description of what this app does and its capabilities.",
  "security_schemes": {
    "api_key": {
      "location": "header",
      "name": "Authorization",
      "prefix": "Bearer"
    }
  },
  "default_security_credentials_by_scheme": {},
  "categories": ["Category1", "Category2"],
  "visibility": "public",
  "active": true
}
```

#### Security Scheme Examples

-   **API Key Authentication:**
    ```json
    "security_schemes": {
      "api_key": {
        "location": "header",
        "name": "X-API-Key",
        "prefix": null
      }
    }
    ```
-   **OAuth2 Authentication:**
    ```json
    "security_schemes": {
      "oauth2": {
        "location": "header",
        "name": "Authorization",
        "prefix": "Bearer",
        "client_id": "{{ YOUR_CLIENT_ID }}",
        "client_secret": "{{ YOUR_CLIENT_SECRET }}",
        "scope": "read write",
        "authorize_url": "https://api.example.com/oauth/authorize",
        "access_token_url": "https://api.example.com/oauth/token",
        "refresh_token_url": "https://api.example.com/oauth/token"
      }
    }
    ```
-   **No Authentication:**
    ```json
    "security_schemes": {
      "no_auth": {}
    }
    ```

### Step 3: Secrets Management for OAuth2-based Application

-   **Naming**: Use `lowercase_with_underscores` for the directory name and `UPPERCASE_WITH_UNDERSCORES` for the app `name` field.
-   **Descriptions**: Write detailed descriptions to improve semantic search and discovery.
-   **Versioning**: Use the highest stable API version if the service has multiple.
-   **Secrets**: For sensitive data like OAuth credentials, use Jinja2 templates (`{{ VARIABLE }}`) in `app.json` and store the actual values in a separate `.app.secrets.json` file. This file should never be committed to version control.

    **`.app.secrets.json` example:**
    ```json
    {
      "YOUR_CLIENT_ID": "actual_client_id_value",
      "YOUR_CLIENT_SECRET": "actual_client_secret_value"
    }
    ```

## 2. Function Configuration (`functions.json`)

Functions define the specific operations an app can perform. The `functions.json` file contains an array of these function definitions.

### Step 1: Create `functions.json`

```bash
# In your app directory
touch your_app_name/functions.json
```

### Step 2: Define Function Schema

Each function object has the following structure. Full examples are in the "Examples" section.

```json
[
  {
    "name": "APP_NAME__FUNCTION_NAME",
    "description": "Detailed description of what this function does.",
    "tags": ["tag1", "tag2"],
    "visibility": "public",
    "active": true,
    "protocol": "rest",
    "protocol_data": {
      "method": "POST",
      "path": "/v1/endpoint",
      "server_url": "https://api.example.com"
    },
    "parameters": {
      // JSON Schema with visibility extensions
    }
  }
]
```

### Protocol Types

-   **`rest`**: For direct API calls. `protocol_data` must contain `method`, `path`, and `server_url`.
-   **`connector`**: For custom logic. The ACI framework routes execution to a corresponding Python class in `backend/aci/server/app_connectors/`. `protocol_data` is an empty object `{}`.

#### REST Protocol Example (Brave Search)
The following `functions.json` entry for `BRAVE_SEARCH__WEB_SEARCH` shows a simple REST function that passes a search query via URL parameters.
```json
{
  "name": "BRAVE_SEARCH__WEB_SEARCH",
  "description": "Search the web using Brave's independent search index with privacy protection.",
  "protocol": "rest",
  "protocol_data": {
    "method": "GET",
    "path": "/web/search",
    "server_url": "https://api.search.brave.com"
  },
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "object",
        "properties": {
          "q": { "type": "string", "description": "Search query string." }
        },
        "required": ["q"],
        "visible": ["q"]
      }
    },
    "required": ["query"],
    "visible": ["query"]
  }
}
```

#### Connector Protocol Example (Gmail)
The `GMAIL__SEND_EMAIL` function uses the `connector` protocol, routing execution to a custom Python class. The implementation logic for this can be found in [`backend/aci/server/app_connectors/gmail.py`](https://github.com/aipotheosis-labs/aci/blob/main/backend/aci/server/app_connectors/gmail.py).
```json
{
  "name": "GMAIL__SEND_EMAIL",
  "description": "Sends an email on behalf of the user using the Gmail API.",
  "protocol": "connector",
  "protocol_data": {},
  "parameters": {
    "type": "object",
    "properties": {
      "recipient": { "type": "string", "format": "email" },
      "subject": { "type": "string" },
      "body": { "type": "string" }
    },
    "required": ["recipient", "body"],
    "visible": ["recipient", "subject", "body"]
  }
}
```

### Parameter Schema with Visibility Rules

The `parameters` object extends JSON Schema with a `visible` field to control which parameters are exposed to AI agents. This creates a clean separation: the AI focuses on user intent, while the framework handles technical details.

**Key Concept**:
-   `required`: A JSON Schema keyword for validation. If a parameter is in this list, it must be provided.
-   `visible`: An ACI extension. Only parameters in this list are exposed to the AI.

| Rule | Combination | Behavior | Use Case |
| :--- | :--- | :--- | :--- |
| 1 | **Visible + Required** | AI can see and **must** provide a value. | A user's search query. |
| 2 | **Visible + Optional** | AI can see and **may** provide a value. | An optional filter like `limit`. |
| 3 | **Invisible + Required** | Auto-injected by the system. **Must** have a `default` value. | A `Content-Type` header. |
| 4 | **Invisible + Optional** | Omitted unless a `default` value is provided. | A system-level tracking ID. |

**Important**:
-   Authentication details should **never** be in function parameters. They are handled centrally by `app.json`.
-   Every object level in the `parameters` schema must have a `visible` field.
-   For strict validation, always set `additionalProperties: false`.

### Parameter Structure Patterns

These patterns demonstrate how to apply visibility rules effectively.

#### Simple REST Function (GET Request)

This pattern is ideal for simple API calls where parameters are passed in the URL query string.

```json
// See full schema in ARXIV__SEARCH_PAPERS example
"parameters": {
  "type": "object",
  "properties": {
    "query": {
      "type": "object",
      "properties": {
        "search_query": {
          "type": "string",
          "description": "Search terms for finding papers"
        },
        "max_results": {
          "type": "integer",
          "default": 10
        }
      },
      "required": ["search_query"],
      "visible": ["search_query", "max_results"]
    }
  },
  "required": ["query"],
  "visible": ["query"]
}
```

-   **Execution Flow**: An AI prompt like `"find papers on transformers"` generates `{"search_query": "transformers"}`. ACI constructs the URL `GET /api/query?search_query=transformers&max_results=10`.

#### Complex POST Function (Request Body with Headers)

This pattern separates user-facing `body` parameters from system-level `header` parameters.

```json
"parameters": {
  "type": "object",
  "properties": {
    "header": {
      "type": "object",
      "properties": {
        "Content-Type": { "type": "string", "default": "application/json" }
      },
      "required": ["Content-Type"],
      "visible": [] // Invisible to AI, auto-injected
    },
    "body": {
      "type": "object",
      "properties": {
        "to": { "type": "string", "format": "email" },
        "subject": { "type": "string" },
        "content": { "type": "string" }
      },
      "required": ["to", "content"],
      "visible": ["to", "subject", "content"] // Visible to AI
    }
  },
  "required": ["header", "body"],
  "visible": ["body"]
}
```

-   **Execution Flow**: `Content-Type` is injected automatically. The AI only works with the email's `body`.

#### Connector Function (Custom Logic)

This pattern provides maximum flexibility for integrations that require custom Python code. The parameters are sent directly to the corresponding Python method. For a complete example, refer to the **Connector Protocol Example (Gmail)** above.

-   **Execution Flow**: ACI routes the call and its parameters to the corresponding Python method, e.g., `GmailConnector.send_email(...)`. The implementation logic resides in a dedicated file, like [`backend/aci/server/app_connectors/gmail.py`](https://github.com/aipotheosis-labs/aci/blob/main/backend/aci/server/app_connectors/gmail.py) for Gmail.

---

# 3. Integration Step by Step

This six-step process walks you through registering and testing a new integration.

### Prerequisites

Before integrating new apps, ensure your development environment is ready:

- **Frontend Setup**: Follow the [Frontend README](frontend/README.md) for the Next.js development server.
- **Backend Setup**: Follow the [Backend README](backend/README.md) for Docker containerization.
- **Database**: Initialize with seed data using the provided scripts.

### Environment Setup

```bash
# In the backend directory, build and start containers
cd backend
docker compose up --build

# In a separate terminal, initialize the database
docker compose exec runner ./scripts/seed_db.sh user
```

### Step 1: Insert an App

Use the `upsert-app` CLI command to register your app's basic configuration (metadata, security schemes) with the database. At this stage, you do not need to provide secrets.

```bash
docker compose exec runner python -m aci.cli upsert-app \
  --app-file ./apps/your_app/app.json \
  --skip-dry-run

# Verify insertion
docker compose exec runner python -m aci.cli list-apps
```

### Step 2: Set Secrets for OAuth2 Applications (If Applicable)

If your app uses OAuth2, you must provide its `client_id` and `client_secret`. Create a `.app.secrets.json` file and run `upsert-app` again with the `--secrets-file` flag to securely store them.

**This step is not needed for No-Auth or user-provided API Key apps.**

```bash
# This command reads secrets from the .app.secrets.json file.
docker compose exec runner python -m aci.cli upsert-app \
  --app-file ./apps/your_app/app.json \
  --secrets-file ./apps/your_app/.app.secrets.json \
  --skip-dry-run
```

### Step 3: Insert Functions

Use the `upsert-functions` CLI command to add the app's functions.

```bash
docker compose exec runner python -m aci.cli upsert-functions \
  --functions-file ./apps/your_app/functions.json \
  --skip-dry-run

# Verify insertion
docker compose exec runner python -m aci.cli list-functions --app-name YOUR_APP_NAME
```

### Step 4: Generate API Key and Create Linked Account

To test your integration, you need an API key and a linked account.

1.  **Generate an API Key**:
    ```bash
    docker compose exec runner python -m aci.cli create-random-api-key \
      --visibility-access private
    ```
    Copy the returned key for the next steps.

2.  **Create App Configuration & Linked Account**: This is currently done via the Swagger UI.
    -   Navigate to [http://localhost:8000/v1/notforhuman-docs](http://localhost:8000/v1/notforhuman-docs).
    -   Authorize using your generated API key.
    -   Use `POST /v1/app-configurations` to enable your app.
    -   Use the appropriate `POST /v1/linked-accounts/*` endpoint to create a linked account (e.g., `/api-key`, `/default`).

### Step 5: Fuzzy Test the Function

The `fuzzy-test-function-execution` command uses an LLM to generate parameters from a natural language prompt, providing a realistic test of your function.

```bash
docker compose exec runner python -m aci.cli fuzzy-test-function-execution \
  --function-name YOUR_APP__FUNCTION_NAME \
  --linked-account-owner-id test_user \
  --aci-api-key your_generated_api_key \
  --prompt "a natural language description of what you want to test"
```
**Troubleshooting**: If this step fails, common causes are an invalid linked account or incorrect visibility rules in `functions.json` preventing the LLM from seeing necessary parameters.

### Step 6: Final Validation in Frontend

For a complete end-to-end test, validate the integration in the UI.

1.  Start the frontend development server (`cd frontend && npm run dev`).
2.  Open [http://localhost:3000](http://localhost:3000) and navigate to the **Playground**.
3.  Select your app and function, and test with real inputs.

---

# 4. Examples

These complete examples demonstrate the three main integration patterns.

## BRAVE_SEARCH (API Key Authentication)

This example shows a simple REST API using API key authentication.

**`apps/brave_search/app.json`**
```json
{
  "name": "BRAVE_SEARCH",
  "display_name": "Brave Search",
  "logo": "https://raw.githubusercontent.com/aipotheosis-labs/aipolabs-icons/refs/heads/main/apps/brave_search.svg",
  "provider": "Brave Software, Inc.",
  "version": "1.0.0",
  "description": "Brave Search API provides independent web search results with privacy protection, powered by Brave's own search index.",
  "security_schemes": {
    "api_key": {
      "location": "header",
      "name": "X-Subscription-Token",
      "prefix": null
    }
  },
  "default_security_credentials_by_scheme": {},
  "categories": ["Search & Scraping"],
  "visibility": "public",
  "active": true
}
```

**`apps/brave_search/functions.json`**
```json
[
  {
    "name": "BRAVE_SEARCH__WEB_SEARCH",
    "description": "Search the web using Brave's independent search index with privacy protection.",
    "tags": ["search", "web"],
    "visibility": "public",
    "active": true,
    "protocol": "rest",
    "protocol_data": {
      "method": "GET",
      "path": "/web/search",
      "server_url": "https://api.search.brave.com"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "object",
          "properties": {
            "q": {
              "type": "string",
              "description": "Search query string."
            },
            "count": {
              "type": "integer",
              "default": 10,
              "minimum": 1,
              "maximum": 20,
              "description": "Number of search results to return."
            },
            "offset": {
              "type": "integer",
              "default": 0,
              "minimum": 0,
              "description": "Number of results to skip."
            }
          },
          "required": ["q"],
          "visible": ["q", "count"],
          "additionalProperties": false
        }
      },
      "required": ["query"],
      "visible": ["query"],
      "additionalProperties": false
    }
  }
]
```

## ARXIV (No Authentication)

This example shows a public REST API that requires no authentication.

**`apps/arxiv/app.json`**
```json
{
  "name": "ARXIV",
  "display_name": "arXiv",
  "logo": "https://raw.githubusercontent.com/aipotheosis-labs/aipolabs-icons/refs/heads/main/apps/arxiv.svg",
  "provider": "Cornell University",
  "version": "1.0.0",
  "description": "arXiv is a free distribution service and open-access archive for scholarly articles.",
  "security_schemes": {
    "no_auth": {}
  },
  "default_security_credentials_by_scheme": {},
  "categories": ["Research", "Academic"],
  "visibility": "public",
  "active": true
}
```

**`apps/arxiv/functions.json`**
```json
[
  {
    "name": "ARXIV__SEARCH_PAPERS",
    "description": "Search for academic papers on arXiv by keywords, authors, or categories.",
    "tags": ["search", "academic", "papers"],
    "visibility": "public",
    "active": true,
    "protocol": "rest",
    "protocol_data": {
      "method": "GET",
      "path": "/api/query",
      "server_url": "https://export.arxiv.org"
    },
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "object",
          "properties": {
            "search_query": {
              "type": "string",
              "description": "Search terms for finding papers."
            },
            "max_results": {
              "type": "integer",
              "default": 10,
              "minimum": 1,
              "maximum": 100,
              "description": "Maximum number of papers to return."
            }
          },
          "required": ["search_query"],
          "visible": ["search_query", "max_results"],
          "additionalProperties": false
        }
      },
      "required": ["query"],
      "visible": ["query"],
      "additionalProperties": false
    }
  }
]
```

## GMAIL (OAuth2 & Connector)

This example demonstrates an OAuth2-protected app that uses the `connector` protocol. The full implementation logic can be found in [`backend/aci/server/app_connectors/gmail.py`](https://github.com/aipotheosis-labs/aci/blob/main/backend/aci/server/app_connectors/gmail.py).

**`apps/gmail/app.json`**
```json
{
  "name": "GMAIL",
  "display_name": "Gmail",
  "logo": "https://raw.githubusercontent.com/aipotheosis-labs/aipolabs-icons/refs/heads/main/apps/gmail.svg",
  "provider": "Google",
  "version": "1.0.0",
  "description": "The Gmail API enables sending, reading, and managing emails.",
  "security_schemes": {
    "oauth2": {
      "location": "header",
      "name": "Authorization",
      "prefix": "Bearer",
      "client_id": "{{ AIPOLABS_GMAIL_CLIENT_ID }}",
      "client_secret": "{{ AIPOLABS_GMAIL_CLIENT_SECRET }}",
      "scope": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
      "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
      "access_token_url": "https://oauth2.googleapis.com/token",
      "refresh_token_url": "https://oauth2.googleapis.com/token"
    }
  },
  "default_security_credentials_by_scheme": {},
  "categories": ["Communication"],
  "visibility": "public",
  "active": true
}
```

**`apps/gmail/functions.json`**
```json
[
  {
    "name": "GMAIL__SEND_EMAIL",
    "description": "Sends an email on behalf of the user using the Gmail API.",
    "tags": ["email", "communication"],
    "visibility": "public",
    "active": true,
    "protocol": "connector",
    "protocol_data": {},
    "parameters": {
      "type": "object",
      "properties": {
        "recipient": {
          "type": "string",
          "format": "email",
          "description": "Recipient's email address."
        },
        "subject": {
          "type": "string",
          "description": "The subject line of the email."
        },
        "body": {
          "type": "string",
          "description": "The body content of the email (plain text)."
        }
      },
      "required": ["recipient", "body"],
      "visible": ["recipient", "subject", "body"],
      "additionalProperties": false
    }
  }
]
```

## Closing Notes and Further Reading

This guide provides a universal tutorial for integrating apps and functions into ACI, focusing on schema design, step-by-step insertion, and testing. It aligns with key design decisions such as deriving schemas from OpenAPI specs (with modifications like inline objects and visibility fields), centralized authentication, and flexible protocols. For properties not visible to LLMs, ensure defaults are set for required fields.

**Key References:**
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Anthropic Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [HTTP Messages](https://developer.mozilla.org/en-US/docs/Web/HTTP/Messages)
- [OpenAPI Specification](https://swagger.io/specification/)

**ACI Resources:**
- Review existing integrations in [backend/apps](https://github.com/aipotheosis-labs/aci/tree/main/backend/apps)
- CLI details in [backend/aci/cli](https://github.com/aipotheosis-labs/aci/tree/main/backend/aci/cli)
- Backend README for setup: [backend/README.md](https://github.com/aipotheosis-labs/aci/blob/main/backend/README.md)

After testing locally, commit your `app.json` and `functions.json` (never commit `.app.secrets.json`) and submit a PR to the ACI repo. For pending decisions (e.g., parameter naming, advanced auth flows), check the repo's issues or contribute discussions. If you encounter issues, refer to the Miscellaneous section in the reference guide for tips like ngrok for OAuth testing.
