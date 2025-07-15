# Guide to Running ACI Evaluation Pipeline

> [!IMPORTANT]
> Before you begin, ensure you have followed the main [backend README](../README.md) to:
> 1. Create and configure your `.env.local` file.
> 2. Start all services using `docker compose up -d`.

## 1. Environment Configuration

The evaluation pipeline requires several environment variables to be configured in your `.env.local` file. Make sure the following variables are set:

```bash
# Add these to your .env.local file:
EVALS_SERVER_URL=http://localhost:8000
EVALS_OPENAI_KEY=<your_openai_api_key> # Can be the same as SERVER_OPENAI_API_KEY

# Optional: For logging results to Weights & Biases
# Get your key from wandb.ai/authorize
EVALS_WANDB_KEY=<your_wandb_api_key>
```

The final variable, `EVALS_ACI_API_KEY`, is generated dynamically in the next step and will need to be added to your `.env.local` file.

## 2. Seed Database and Get ACI API Key

Next, run the database seed script. This populates the database with the necessary apps and functions for the evaluation and generates the API key you need.

```bash
# Seed with all apps and mock credentials
docker compose exec runner ./scripts/seed_db.sh --all --mock
```

This will output a JSON object containing the API key:

```json
{
    "Project Id": "65cf26b9-a919-4008-85de-ecb850c3fc36",
    "Agent Id": "74273ac1-f68e-4314-b8be-fee4a5855d8a",
    "API Key": "<your_generated_api_key>"
}
```

**Copy the `API Key` value and add it to your `.env.local` file:**

```bash
# Add this line to your .env.local file:
EVALS_ACI_API_KEY=<your_generated_api_key>
```

**After updating your `.env.local` file, restart the Docker services:**

```bash
# Stop the services with Ctrl+C, then restart with:
docker compose up --build
```

## 3. Running the Evaluation Pipeline

Now you're ready to run the evaluation. Since the environment variables are configured in your `.env.local` file, the commands are straightforward:

### Basic Modes

#### Generate and Evaluate

```bash
docker compose exec runner python -m evals.evaluation_pipeline --mode generate-and-evaluate
```

#### Generate Synthetic Data Only

```bash
docker compose exec runner python -m evals.evaluation_pipeline --mode generate-only
```

#### Evaluate Existing Dataset Only

```bash
docker compose exec runner python -m evals.evaluation_pipeline --mode evaluate-only
```

### Advanced Options

You can add flags to limit sample sizes or customize dataset names.

#### Quick Test Run Example

```bash
# Generate and evaluate with a small sample size of 10
docker compose exec runner python -m evals.evaluation_pipeline \
  --mode generate-and-evaluate \
  --generation-limit 10 \
  --evaluation-samples 10
```

## 4. Viewing Results

- **Console Output**: Metrics like accuracy, MRR, and response time will be printed directly to your terminal.
- **Weights & Biases**: If you provided a `EVALS_WANDB_KEY`, you can view detailed results and artifacts at [wandb.ai/aipotheosis-labs/function-search-evaluation](https://wandb.ai/aipotheosis-labs/function-search-evaluation).

## 5. Troubleshooting

- **"401 Unauthorized" Error**: This usually means your `EVALS_ACI_API_KEY` is missing or incorrect in your `.env.local` file. Make sure you've added it and restarted Docker services.
- **"No app and function data found"**: The database is likely empty. Rerun the seed script: `docker compose exec runner ./scripts/seed_db.sh --all --mock`.
- **OpenAI Errors**: Check that `EVALS_OPENAI_KEY` is set correctly in your `.env.local` file.
- **Docker Restart**: After updating any variables in your `.env.local` file, stop the services with Ctrl+C and restart with `docker compose up --build`.
