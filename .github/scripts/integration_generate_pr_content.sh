#!/bin/bash

# Takes PR title, body and changed files as inputs
PR_TITLE="$1"
PR_BODY="$2"
CHANGED_FILES="$3"
BASE_SHA="$4"
HEAD_SHA="$5"

CONTENT=""

# Include PR title and description
CONTENT+="# Pull Request Information\n"
CONTENT+="Title: $PR_TITLE\n"
CONTENT+="Description: $PR_BODY\n\n"

CONTENT+="# Changed Files Content\n\n"

# Read content of each changed file with diff
for file in $CHANGED_FILES; do
  if [ -f "$file" ]; then
    CONTENT+="## $file\n"
    
    # Handle different file types differently
    if [[ "$file" == *"app.json" ]]; then
      # For app.json, include the full file content
      CONTENT+="\`\`\`json\n$(cat $file)\n\`\`\`\n\n"
    elif [[ "$file" == *"functions.json" ]]; then
      # For functions.json, only include the diff
      # append relative path to the file
      CONTENT+="### $file\n"
      # add the file content in app.json in the same directory
      # get the directory of the file
      DIR=$(dirname $file)
      CONTENT+="### app.json\n"
      CONTENT+="\`\`\`json\n$(cat $DIR/app.json)\n\`\`\`\n\n"
      CONTENT+="### Changes in diff format:\n"
      CONTENT+="\`\`\`diff\n$(git diff $BASE_SHA $HEAD_SHA -- $file)\n\`\`\`\n\n"
    else
      # For all other files, include both full content and diff
      CONTENT+="\`\`\`\n$(cat $file)\n\`\`\`\n\n"
      
      CONTENT+="### Changes in diff format:\n"
      CONTENT+="\`\`\`diff\n$(git diff $BASE_SHA $HEAD_SHA -- $file)\n\`\`\`\n\n"
    fi
  fi
done

# Output the content
echo -e "$CONTENT" > pr_content.txt 