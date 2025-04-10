### Summary
This PR integrates Solscan API into our application, providing users with comprehensive data about the Solana blockchain. Solscan is a block explorer and analytics platform for Solana that offers detailed information about accounts, tokens, NFTs, and transactions.

APP_URL: https://solscan.io
APP_API_DOCS_URL: https://docs.solscan.io

### Integrated API
```
SOLSCAN__GET_CHAIN_INFO
SOLSCAN__GET_ACCOUNT_DETAIL
SOLSCAN__GET_ACCOUNT_BALANCE_CHANGE
SOLSCAN__GET_ACCOUNT_TRANSACTIONS
SOLSCAN__GET_ACCOUNT_PORTFOLIO
```

### Fuzzy Tests
```
docker compose exec runner python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name SOLSCAN__ACCOUNT_GET --linked-account-owner-id <LINKED_ACCOUNT_OWNER_ID> --aipolabs-api-key <AIPOLABS_API_KEY> --prompt "get information about Solana account 9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"

docker compose exec runner python -m aipolabs.cli.aipolabs fuzzy-test-function-execution --function-name SOLSCAN__TOKEN_METADATA --linked-account-owner-id <LINKED_ACCOUNT_OWNER_ID> --aipolabs-api-key <AIPOLABS_API_KEY> --prompt "get metadata for USDC token on Solana"
```

### Videos 
<video width="100%" controls>
  <source src="res/solscan.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>