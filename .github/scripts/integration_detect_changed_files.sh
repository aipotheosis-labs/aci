#!/bin/bash

# Takes base SHA and head SHA as inputs
BASE_SHA="$1"
HEAD_SHA="$2"

# Get the list of changed files, focusing on integration-related files
CHANGED_FILES=$(git diff --name-only $BASE_SHA $HEAD_SHA | grep -E '^(apps)/' | grep -E '\.json$' || echo "")

# Echo debugging information to stderr, not stdout
# This way it won't be captured in $GITHUB_OUTPUT
echo "Changed files: $CHANGED_FILES" >&2

# Check if there are integration-related changes
if [ -z "$CHANGED_FILES" ]; then
  echo "No relevant integration files changed, skipping review" >&2
  echo "skip=true"
else
  echo "skip=false"
fi

# Output the changed files list - using proper GitHub Actions output syntax
echo "changed_files<<EOF"
echo "$CHANGED_FILES"
echo "EOF" 