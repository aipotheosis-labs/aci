#!/bin/bash

set -euo pipefail

function usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  -h, --help   Display this help message
  plans        Seed only the subscription plans
  apps         Seed only the apps
  functions    Seed only the functions
  user         Seed only the user resource

If no arguments are provided, the script will seed everything.
EOF
}

# Declare flags for seeding various resources
SEED_PLANS=false
SEED_APPS=false
SEED_FUNCTIONS=false
SEED_USER=false

parse_arguments() {

  if [ $# -eq 0 ]; then
    # No arguments: default to seed everything
    SEED_PLANS=true
    SEED_APPS=true
    SEED_FUNCTIONS=true
    SEED_USER=true
  else
    # Parse arguments
    for arg in "$@"; do
      case $arg in
        plans)
          SEED_PLANS=true
          ;;
        apps)
          SEED_APPS=true
          ;;
        functions)
          SEED_FUNCTIONS=true
          ;;
        user)
          SEED_USER=true
          ;;
        -h|--help)
          usage
          exit 0
          ;;
        *)
          echo "Unknown argument: $arg"
          usage
          exit 1
          ;;
      esac
    done
  fi
}

# Call our argument parser
parse_arguments "$@"

# Seed the database with a default project and a default agent. The command will
# output the API key of that agent that can be used in the swagger UI.
if [ "$SEED_USER" = true ]; then
  python -m aci.cli.aci create-random-api-key --visibility-access public --org-id 107e06da-e857-4864-bc1d-4adcba02ab76
fi

# Seed the database with Plans
if [ "$SEED_PLANS" = true ]; then
  python -m aci.cli populate-subscription-plans --skip-dry-run
fi

# Seed the database with Apps
if [ "$SEED_APPS" = true ]; then
  for app_dir in ./apps/*/; do
    app_file="${app_dir}app.json"
    secrets_file="${app_dir}.app.secrets.json"

    # Check if secrets file exists and construct command accordingly
    if [ -f "$secrets_file" ]; then
      python -m aci.cli upsert-app \
        --app-file "$app_file" \
        --secrets-file "$secrets_file" \
        --skip-dry-run
    else
      python -m aci.cli upsert-app \
        --app-file "$app_file" \
        --skip-dry-run
    fi
  done
fi

# Seed the database with Functions
if [ "$SEED_FUNCTIONS" = true ]; then
  for functions_file in ./apps/*/functions.json; do
    python -m aci.cli upsert-functions \
      --functions-file "$functions_file" \
      --skip-dry-run
  done
fi
