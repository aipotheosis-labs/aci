#!/bin/bash

set -exou pipefail

# poetry install # needed because the Dockerfile.server skipped dev dependencies
docker compose build
docker compose down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error
docker compose up -d
poetry run pytest
docker compose down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error