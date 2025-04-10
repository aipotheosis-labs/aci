### Summary
This PR integrates Sentry API into our application, enabling users to monitor, track, and resolve software errors in real-time. Sentry is an application monitoring platform that helps developers identify and fix crashes in their applications.

APP_URL: https://sentry.io
APP_API_DOCS_URL: https://docs.sentry.io/api/

### Integrated API
```
SENTRY__GET_ISSUES
SENTRY__GET_EVENTS
SENTRY__GET_RELEASES
SENTRY__GET_TAGS
```

### Fuzzy Tests
```
docker compose exec runner python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name SENTRY__ISSUES_LIST --linked-account-owner-id <LINKED_ACCOUNT_OWNER_ID> --aipolabs-api-key <AIPOLABS_API_KEY> --prompt "list all unresolved issues in my project"

docker compose exec runner python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name SENTRY__PROJECTS_LIST --linked-account-owner-id <LINKED_ACCOUNT_OWNER_ID> --aipolabs-api-key <AIPOLABS_API_KEY> --prompt "show all my Sentry projects"
```

### Videos 

<video width="100%" controls>
  <source src="res/sentry.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>