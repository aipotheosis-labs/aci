# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ACI.dev is an open-source tool-calling platform providing 600+ integrations for AI agents. It serves as infrastructure for Unified MCP (Model Context Protocol) servers and VibeOps automated DevOps workflows. The platform handles multi-tenant authentication, granular permissions, and dynamic tool discovery.

## Repository Structure

This is a **monorepo** with two main components:

- `backend/` - FastAPI server with 600+ integrations (Python 3.12+, PostgreSQL, uv package manager)
- `frontend/` - Next.js 15 developer portal (React 19, TypeScript, Tailwind CSS, shadcn/ui)

## Essential Development Commands

### Backend Commands

```bash
cd backend
uv sync                                          # Install dependencies
source .venv/bin/activate                       # Activate virtual environment
docker compose up --build                       # Start all services (includes PostgreSQL with pgvector)
docker compose exec runner ./scripts/seed_db.sh # Seed database

# Database management
docker compose exec runner alembic upgrade head                    # Apply migrations
docker compose exec runner alembic revision --autogenerate -m "description" # Create migration

# Testing and quality
docker compose exec test-runner pytest         # Run tests
ruff format .                                   # Format code
ruff check .                                    # Lint code
mypy .                                          # Type checking

# Admin CLI
docker compose exec runner python -m aci.cli --help
docker compose exec runner python -m aci.cli upsert-app --app-file ./apps/gmail/app.json
```

### Frontend Commands

```bash
cd frontend
npm install --legacy-peer-deps                 # Install dependencies (React 19 compatibility required)
cp .env.example .env                           # Setup environment
npm run dev                                    # Start development server

# Code quality
npm run format                                 # Prettier formatting
npm run lint                                   # ESLint
npm run test                                   # Vitest in watch mode
npm run build                                  # Production build
```

## Core Architecture

### Database Models (`backend/aci/common/db/sql_models.py`)

- **Project**: Multi-tenant container for API keys, apps, and agents
- **Agent**: Logical actors that access the platform (tied to API keys)
- **App**: Third-party service integrations (Gmail, Slack, etc.)
- **Function**: Individual API endpoints within apps
- **LinkedAccount**: User authentication credentials for OAuth/API keys
- **AppConfiguration**: User-specific app settings and permissions

### Backend Structure (`backend/aci/`)

- `server/` - FastAPI application with routes, middleware, app_connectors
- `common/db/` - SQLAlchemy models and CRUD operations
- `common/schemas/` - Pydantic models for validation
- `cli/` - Admin command-line interface
- `apps/` - 600+ integration definitions as JSON configs

### Frontend Structure (`frontend/src/`)

- `app/` - Next.js App Router pages (apps/, playground/, settings/)
- `components/` - Reusable UI components with shadcn/ui
- `lib/` - API clients and utilities
- `hooks/` - Custom React hooks

## Integration System

Each integration requires two JSON files in `backend/apps/{app_name}/`:

- `app.json` - Metadata, authentication schemes, categories, visibility
- `functions.json` - API endpoints and their schemas

Apps support OAuth2, API keys, and no-auth patterns with encrypted credential storage.

## Key Services (Docker Compose)

- **server**: FastAPI backend (port 8000)
- **db**: PostgreSQL with pgvector extension (port 5432)
- **aws**: LocalStack for AWS services (port 4566)
- **runner**: Utility container for CLI commands and database operations
- **test-runner**: Isolated testing environment

## Authentication & API Structure

### Authentication Methods

1. **PropelAuth**: Web portal authentication for developers
2. **API Keys**: Agent/programmatic access via `X-API-KEY` header
3. **OAuth2/API Keys**: End-user service authentication stored as LinkedAccounts

### Core API Endpoints (`/v1/`)

- `/apps` - Browse and configure integrations
- `/functions` - Execute tool calls with semantic search using pgvector
- `/linked-accounts` - Manage user authentication
- `/projects` - Project and agent management
- `/playground` - Interactive agent testing

## Function Execution Flow

1. **Discovery**: Semantic search finds relevant functions using OpenAI embeddings
2. **Authentication**: Validates API key and linked account permissions
3. **Execution**: Routes calls through appropriate connectors
4. **Logging**: Comprehensive request/response tracking with Sentry/Logfire

## Local Development Setup

1. **Backend**: Copy `.env.example` to `.env.local`, set OpenAI API keys, run `docker compose up --build`
2. **Frontend**: Copy `.env.example` to `.env`, run `npm install --legacy-peer-deps`
3. **Database**: Run `docker compose exec runner ./scripts/seed_db.sh` to populate with sample data

## Package Managers

- **Backend**: Uses `uv` (modern Python package manager) - do not use pip/poetry
- **Frontend**: Uses npm with `--legacy-peer-deps` flag required for React 19 compatibility

## Testing

- **Backend**: `docker compose exec test-runner pytest` (isolated test environment)
- **Frontend**: `npm run test` (Vitest in watch mode)

## Code Quality Tools

- **Backend**: ruff (formatting/linting), mypy (type checking), pre-commit hooks
- **Frontend**: Prettier (formatting), ESLint (linting), TypeScript compiler
