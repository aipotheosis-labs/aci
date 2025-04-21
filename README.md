<p align="center">
  <img src="frontend/public/aci-dev-full-logo.svg" alt="ACI.dev Logo" width="100%">
</p>

# ACI: Open Source Tool-Use Infrastructure for AI Agents

<p align="center">
  <a href="https://github.com/aipotheosis-labs/aci/actions/workflows/devportal.yml"><img src="https://github.com/aipotheosis-labs/aci/actions/workflows/devportal.yml/badge.svg" alt="Dev Portal CI"></a>
  <a href="https://github.com/aipotheosis-labs/aci/actions/workflows/backend.yml"><img src="https://github.com/aipotheosis-labs/aci/actions/workflows/backend.yml/badge.svg" alt="Backend CI"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License"></a>
  <a href="https://discord.com/invite/UU2XAnfHJh"><img src="https://img.shields.io/badge/Discord-Join_Chat-7289DA.svg?logo=discord" alt="Discord"></a>
  <a href="https://x.com/AipoLabs"><img src="https://img.shields.io/twitter/follow/AipoLabs?style=social" alt="Twitter Follow"></a>
  <a href="https://badge.fury.io/py/aci-sdk"><img src="https://badge.fury.io/py/aci-sdk.svg" alt="PyPI version"></a>
</p>

ACI.dev connects your AI agents to 600+ tool integrations with multi-tenant authentication, granular permissions, and dynamic tool discovery, accessible through either direct tool/function-calling or a unified MCP server.

**Example:** Instead of writing separate OAuth flows and API clients for Google Calendar, Slack, and more, use ACI.dev to manage authentication and provide your AI agents with unified, secure function calls. Access these capabilities through our lightweight [Python SDK](https://github.com/aipotheosis-labs/aci-python-sdk) or via our unified [MCP server](https://github.com/aipotheosis-labs/aci-mcp), compatible with any LLM framework.

Build production-ready AI agents without the infrastructure headaches.

![ACI.dev Architecture](frontend/public/aci-architecture-intro.svg)

## Key Features

- **600+ Pre-built Integrations**: Connect to popular services and apps in minutes.
- **Flexible Access Methods**: Use our lightweight SDK for direct function calling or our unified MCP server.
- **Multi-tenant Authentication**: Built-in OAuth flows and secrets management for both developers and end-users.
- **Enhanced Agent Reliability**: Natural language permission boundaries and dynamic tool discovery.
- **Framework & Model Agnostic**: Works with any LLM framework and agent architecture.
- **100% Open Source**: Everything released under Apache 2.0 (backend, dev portal, integrations).

## Quick Links

- **Managed Service:** [aci.dev](https://www.aci.dev/)
- **Documentation:** [aci.dev/docs](https://www.aci.dev/docs)
- **Available Tools List:** [aci.dev/tools](https://www.aci.dev/tools)
- **Python SDK:** [github.com/aipotheosis-labs/aci-python-sdk](https://github.com/aipotheosis-labs/aci-python-sdk)
- **Unified MCP Server:** [github.com/aipotheosis-labs/aci-mcp](https://github.com/aipotheosis-labs/aci-mcp)
- **Blog:** [aci.dev/blog](https://www.aci.dev/blog)
- **Community:** [Discord](https://discord.com/invite/UU2XAnfHJh) | [Twitter/X](https://x.com/AipoLabs) | [LinkedIn](https://www.linkedin.com/company/aipotheosis-labs-aipolabs/posts/?feedView=all)

## Why Use ACI.dev?

ACI.dev solves your critical infrastructure challenges for production-ready AI agents:

- **Authentication at Scale**: Connect multiple users to multiple services securely.
- **Discovery Without Overload**: Find and use the right tools without overwhelming LLM context windows.
- **Natural Language Permissions**: Control agent capabilities with human-readable boundaries.
- **Build Once, Run Anywhere**: No vendor lock-in with our open source, framework-agnostic approach.

## Common Use Cases

- **Personal Assistant Chatbots:** Build chatbots that can search the web, manage calendars, send emails, interact with SaaS tools, etc.
- **Research Agent:** Conducts research on specific topics and syncs results to other apps (e.g., Notion, Google Sheets).
- **Outbound Sales Agent:** Automates lead generation, email outreach, and CRM updates.
- **Customer Support Agent:** Provides answers, manages tickets, and performs actions based on customer queries.

## Repository Structure

This is a monorepo that contains the core components of ACI.dev:

- **`/backend`**: Contains the main ACI platform server, including the APIs, core logic, database models, and the entire integration library (over 600+ tools).
- **`/frontend`**: Contains the Next.js application for the ACI.dev Developer Portal. This is the web interface for managing projects, integrations, authentication, and testing agents.

## Getting Started: Local Development

To run the full ACI.dev platform (backend server and frontend portal) locally, follow the individual README files for each component:

- **Backend:** [backend/README.md](backend/README.md)
- **Frontend:** [frontend/README.md](frontend/README.md)


## Tech Stack (local)

- **Backend:**
  - **Language:** Python 3.12+
  - **Framework:** FastAPI
  - **Database:** PostgreSQL
  - **ORM:** SQLAlchemy with Alembic for migrations
  - **Dependency Management:** uv
  - **Testing:** Pytest
  - **Linting/Formatting:** Ruff, MyPy
  - **Containerization:** Docker & Docker Compose
  - **Local AWS Mocking:** LocalStack
- **Frontend:**
  - **Framework:** Next.js (App Router)
  - **Language:** TypeScript
  - **UI Library:** React 19
  - **Styling:** Tailwind CSS
  - **Component Library:** shadcn/ui
  - **Testing:** Vitest
  - **Linting/Formatting:** ESLint, Prettier
- **Authentication:** PropelAuth

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for more information.
