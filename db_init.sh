#!/bin/bash

set -eou pipefail

poetry install # needed because the Dockerfile.server skipped dev dependencies
poetry run alembic upgrade head
