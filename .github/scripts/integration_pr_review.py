import os
import sys

import anthropic

# Check if the file exists
if not os.path.exists("pr_content.txt"):
    print("ERROR: The PR content file does not exist")
    sys.exit(1)
# Read the content of the PR
with open("pr_content.txt") as f:
    pr_content = f.read()

# Print the content of the PR
print("PR Content:")
print(pr_content)

# Define the prompt for Claude
prompt = f"""
## Roles
You are a senior integration engineer with deep expertise in API configurations, function specifications, and integration documentation.
You are reviewing a pull request that modified integration configuration files.

## Objectives
- Analyze the changes in a pull request that modified integration files, focus on checking required and visible fields in function specification
- Identify potential issues, improvements, and best practices, and provide actionable feedback for the developer
- Evaluate the overall quality of the integration changes

## Integration Context
This project has integrations in the 'apps/' directory:
- Each subdirectory represents a different integration (e.g., Discord, Slack, GitHub)
- Each integration typically has an app.json file (containing configuration) and a functions.json file (defining API operations)
- The function specifications follow a structured format with metadata and parameters

## Workflow
1. Search relevant documentation for the integration
2. According to api documentation and function specification, special rules, check the pull request and provide feedback
## Function Specification (Function Object)
- The function specification including the metadata of the API, such as name, description, tags, visibility, active, protocol, protocol_data, parameters.
- The function didn't include the return value, because the return value is not relevant to the LLM in current design.
Each "function" object should detail a specific API operation or endpoint. This includes information such as the operation name, HTTP method, URL path, parameters etc. But also some custom fields like "visible" and "required".
- for metadata field, follow following rules:
  - name: the name of the function, should be unique, uppercase, begin with application name then double underscore then the function name like "GITHUB__GET_USER"
  - description: the description of the function, should be a short sentence.
  - tags: the tags of the function, should be a list of string.
  - visibility: the visibility of the function, should be a string, could be "public" or "private", default is "public".
  - active: the active status of the function, should be a boolean, default is true.
  - protocol: the protocol of the function, should be a string, could be "rest" or "graphql", default is "rest".
  - protocol_data: the protocol data of the function, should be a object, including method, path, server_url.
    - method: the method of the function, should be a string, could be "GET", "POST", "PUT", "DELETE", etc.
    - path: the path of the function, should be a string, could be "/users", "/repos", etc.
    - server_url: the server url of the function, should be a string, could be "https://api.github.com", "https://discord.com/api/v10", etc.
  - parameters: the parameters of the function, should be a object
- for required field, it should be a list of required parameters, you should fill according to the original markdown documentation.
- for visible field, you should thinking if we need to show this parameter to LLM or not. usually, we don't need to show the parameter like version.
## Special Rules
- The Authorization information like token or api key has been configured in the app.json file and should not be shown in the function specification.
- the version number and api path should in `server_url` field, not in `path` field in `protocol_data` object.

## Output Format
For each issue you find, include:
- The file and line numbers
- A description of the problem
- A suggested solution or improvement

At the end, provide:
- A summary of the changes and their impact on the integration functionality
- An overall assessment rating (High quality / Acceptable / Needs improvement)
- Actionable next steps for the developer

## Pull Request Content
{pr_content}
"""

# Get API key
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY environment variable is not set")
    sys.exit(1)

try:
    # Create the client
    client = anthropic.Anthropic(api_key=api_key)

    # Call the API with streaming for long requests
    with open("claude_review.md", "w") as f:
        # Start the streaming request
        stream = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=64000,
            temperature=0.0,
            system="You are an expert code reviewer specialized in API integrations and configurations. Focus on analyzing the diff sections where lines are prefixed with + (additions) or - (deletions).",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        # Process the stream using the correct attribute
        for event in stream:
            if event.type == "content_block_delta":
                f.write(event.delta.text)

    print("Integration code review completed successfully")

except Exception as e:
    print(f"ERROR: Failed to call Anthropic API: {e!s}")
    sys.exit(1)
