### Summary
This PR integrates SerpAPI into our application, allowing users to scrape search engine results from Google, Bing, Yahoo, and other search engines. SerpAPI provides a simple API to access search engine results in a structured JSON format.

APP_URL: https://serpapi.com
APP_API_DOCS_URL: https://serpapi.com/search-api

### Integrated API
```
SERPAPI__GOOGLE_SEARCH
SERPAPI__GOOGLE_IMAGES
SERPAPI__GOOGLE_NEWS
SERPAPI__GOOGLE_SCHOLAR
SERPAPI__GOOGLE_TRENDS
```

### Fuzzy Tests
```
docker compose exec runner python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name SERPAPI__SEARCH_GOOGLE --linked-account-owner-id <LINKED_ACCOUNT_OWNER_ID> --aipolabs-api-key <AIPOLABS_API_KEY> --prompt "search Google for AI news this week"

docker compose exec runner python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name SERPAPI__SEARCH_YOUTUBE --linked-account-owner-id <LINKED_ACCOUNT_OWNER_ID> --aipolabs-api-key <AIPOLABS_API_KEY> --prompt "find tutorial videos about Python programming"
```

### Videos 

<video width="100%" controls>
  <source src="res/serpapi.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>