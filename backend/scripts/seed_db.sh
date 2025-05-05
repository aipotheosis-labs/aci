#!/bin/bash

set -euo pipefail

function usage() {
  cat <<EOF
Usage: $0 [options]

Options:
  -h, --help   Display this help message
  -a, --all    Seed all available Apps and Functions (without this flag, it will seed only a selected set of Apps and their Functions (with dummy OAuth2 client id & secret if it's OAuth2 app))

EOF
}

SEED_ALL=false

parse_arguments() {

  if [ $# -eq 0 ]; then
    # No arguments: default to seed selected test data
    SEED_ALL=false
  else
    # Parse arguments
    for arg in "$@"; do
      case $arg in
        -a|--all)
          SEED_ALL=true
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


seed_test_apps() {
  # Create a temporary file
  temp_oauth2_secrets_file=$(mktemp)

  # Make sure it gets deleted when the script exits
  trap "rm -f $temp_oauth2_secrets_file" EXIT

  # Add content to the temporary file
  cat > "$temp_oauth2_secrets_file" <<EOF
    {
      "AIPOLABS_GOOGLE_APP_CLIENT_ID": "dummy_client_id",
      "AIPOLABS_GOOGLE_APP_CLIENT_SECRET": "dummy_client_secret"
    }
EOF

  python -m aci.cli upsert-app --app-file "./apps/brave_search/app.json" --skip-dry-run
  python -m aci.cli upsert-app --app-file "./apps/hackernews/app.json" --skip-dry-run
  python -m aci.cli upsert-app --app-file "./apps/gmail/app.json" --secrets-file "$temp_oauth2_secrets_file" --skip-dry-run

  python -m aci.cli upsert-functions --functions-file "./apps/brave_search/functions.json" --skip-dry-run
  python -m aci.cli upsert-functions --functions-file "./apps/hackernews/functions.json" --skip-dry-run
  python -m aci.cli upsert-functions --functions-file "./apps/gmail/functions.json" --skip-dry-run
}

seed_all_apps() {
  # Seed the database with Apps
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

  # Seed the database with Functions
  for functions_file in ./apps/*/functions.json; do
    python -m aci.cli upsert-functions \
      --functions-file "$functions_file" \
      --skip-dry-run
  done
}

seed_required_data() {
  # Seed the database with Plans
  python -m aci.cli populate-subscription-plans --skip-dry-run

  # Seed the database with a default project and a default agent. The command will
  # output the API key of that agent that can be used in the swagger UI.
  python -m aci.cli create-random-api-key --visibility-access public --org-id 107e06da-e857-4864-bc1d-4adcba02ab76
}

# Execute the script functions
parse_arguments "$@"
if [ "$SEED_ALL" = true ]; then
  seed_all_apps
else
  seed_test_apps
fi
seed_required_data
