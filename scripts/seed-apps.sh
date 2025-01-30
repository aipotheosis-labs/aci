#!/bin/bash

set -exou pipefail

# seed the database with Apps with cli
for app_dir in ./apps/*/; do
    app_file="${app_dir}app.json"
    secrets_file="${app_dir}.app.secrets.json"
    python -m aipolabs.cli.aipolabs create-app --app-file "$app_file" --secrets-file "$secrets_file" --skip-dry-run
done
