#/bin/bash

set -eou pipefail

poetry install
poetry run alembic upgrade head
