# Aipolabs Developer Portal

![CI](https://github.com/aipotheosis-labs/aci/actions/workflows/devportal.yml/badge.svg)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

The [developer portal](https://platform.aci.dev/) for Aipolabs, a platform for developers to manage and configure the apps and functions used by their agents.

## Table of Contents

- [Aipolabs Developer Portal](#aipolabs-developer-portal)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Development Setup](#development-setup)
  - [Linting \& Testing](#linting--testing)
  - [Directory Structure](#directory-structure)
  - [Conventions](#conventions)
  - [Deployment](#deployment)

## Description

The Dev Portal enables developers to create and manage their projects efficiently. It provides the following key pages for comprehensive project management:

- **Projects Settings**
- **Home Page**
- **App Store Page**
- **App Configurations Page**
- **Linked Accounts Page**
- **Agent Playground Page**
- **Account Settings**

## Development Setup

1. **Bring up backend in docker compose:**
   Refer to the [backend README](../backend/README.md) to set it up. Make sure you
   complete the [Webhooks](../backend/README.md#webhooks-for-local-end-to-end-development-with-frontend) section of the setup.

1. Make sure you are in the **frontend** directory

1. **Install dependencies:**
   If you're using npm:

   ```bash
   npm install --legacy-peer-deps
   ```

   (Note: This repo uses Next.js 15, which requires React 19 that is
   [stabilized in Dec 05, 2024](https://react.dev/blog/2024/12/05/react-19).
   Some libraries are still upgrading to React 19, so we need to use the
   `--legacy-peer-deps` flag in the mean time.)

1. **Configure Environment Variables:** Copy `.env.example` to `.env`

   ```bash
   cp .env.example .env
   ```

1. **Start the application:**

   ```bash
   npm run dev
   ```

1. **Sign up on the local dev portal:**
   After signup, a new user will be created in the PropelAuth local dev org's test
   environment. PropelAuth will also call the user-created webhook, which will create a
   test project and agent in your local DB for you to use.

## Linting & Testing

This repo uses prettier for formatting, next lint for linting, and vitest for unit tests.

- **Format code:**

  ```bash
  npm run format
  ```

- **Run linters:**

  ```bash
  npm run lint
  ```

- **Run vitest in watch mode:**

  ```bash
  npm run test
  ```

- **Get test coverage:**

  ```bash
  npm run test:coverage
  ```

You can also setup pre-commit hook to run format, lint, and tests when you
commit your code by running (make sure you have [pre-commit](https://pre-commit.com/) installed):

```bash
pre-commit install
```

## Directory Structure

```text
src
├── app (Next.js App Router folder)
│   ├── ... (different pages of the dev portal)
├── components
│   ├── ... (components we created for use in the pages of dev portal)
│   └── ui  (shadcn/ui components we installed)
├── hooks
│   └── use-mobile.tsx
└── lib
│   ├── api          (functions for interacting with the Aipolabs backend API)
│   ├── types        (types of the Aipolabs backend API response)
│   └── utils.ts
└── __test__ (test files, the structure of this folder should be the same as the structure of the src/app folder)
    ├── apps
    ├── linked-accounts
    ├── project-setting
    └── ...
```

## Conventions

- All functions calling the backend API directly should be put in the [src/lib/api](./src/lib/api/) folder.

## Deployment

The Dev Portal is deployed on Vercel: [obnoxiousproxys-projects/aci-dev-portal](https://vercel.com/obnoxiousproxys-projects/aci-dev-portal)

The environment variables need to be set correctly on Vercel: <https://vercel.com/obnoxiousproxys-projects/aci-dev-portal/settings/environment-variables>.

For example, for the Vercel production environment, we set the following environment variables:

```sh
NEXT_PUBLIC_API_URL=https://api.aci.dev
NEXT_PUBLIC_DEV_PORTAL_URL=https://platform.aci.dev
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_AUTH_URL=<actual_production_propelauth_endpoint>
```
