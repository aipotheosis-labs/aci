#!/bin/bash

set -euo pipefail

function usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  -h, --help   Display this help message
  apps         Seed only the apps
  functions    Seed only the functions
  user         Seed only the user resource

If no arguments are provided, the script will seed everything.
EOF
}

# Declare flags for seeding various resources
SEED_APPS=false
SEED_FUNCTIONS=false
SEED_USER=false

parse_arguments() {

  if [ $# -eq 0 ]; then
    # No arguments: default to seed everything
    SEED_APPS=true
    SEED_FUNCTIONS=true
    SEED_USER=true
  else
    # Parse arguments
    for arg in "$@"; do
      case $arg in
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


# Seed the database with Apps
if [ "$SEED_APPS" = true ]; then
  for app_dir in ./apps/*/; do
    app_file="${app_dir}app.json"
    secrets_file="${app_dir}.app.secrets.json"
    python -m aipolabs.cli.aipolabs create-app \
      --app-file "$app_file" \
      --secrets-file "$secrets_file" \
      --skip-dry-run
  done
fi

# Seed the database with Functions
if [ "$SEED_FUNCTIONS" = true ]; then
  for functions_file in ./apps/*/functions.json; do
    python -m aipolabs.cli.aipolabs create-functions \
      --functions-file "$functions_file" \
      --skip-dry-run
  done
fi

# Seed the database with a user resource
if [ "$SEED_USER" = true ]; then
  python -m aipolabs.cli.aipolabs create-random-api-key --visibility-access public
fi