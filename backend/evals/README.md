# Guide to Running ACI Evaluation Pipeline

> [!IMPORTANT]
> Before you begin, ensure you have followed the main [backend README](../README.md) to:
> 1. Create and configure your `.env.local` file.
> 2. Start all services using `docker compose up -d`.

## 1. Environment Configuration

The evaluation pipeline requires several environment variables to be set in your terminal session. These are passed directly into the Docker container when you run the evaluation commands.

```bash
# Set these environment variables in your terminal:
export EVALS_SERVER_URL=http://localhost:8000
export EVALS_OPENAI_KEY=<your_openai_api_key> # Can be the same as in your .env.local

# Optional: For logging results to Weights & Biases
# Get your key from wandb.ai/authorize
export EVALS_WANDB_KEY=<your_wandb_api_key>
```

The final variable, `EVALS_ACI_API_KEY`, is generated dynamically in the next step.

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

**Copy the `API Key` value and export it as an environment variable:**

```bash
export EVALS_ACI_API_KEY=<your_generated_api_key>
```

## 3. Running the Evaluation Pipeline

Now you're ready to run the evaluation. The commands below must include the `-e` flags to pass your environment variables into the container.

### Basic Modes

#### Generate and Evaluate

```bash
docker compose exec \
  -e EVALS_SERVER_URL \
  -e EVALS_ACI_API_KEY \
  -e EVALS_OPENAI_KEY \
  -e EVALS_WANDB_KEY \
  runner python -m evals.evaluation_pipeline --mode generate-and-evaluate
```

#### Generate Synthetic Data Only

```bash
docker compose exec \
  -e EVALS_SERVER_URL \
  -e EVALS_ACI_API_KEY \
  -e EVALS_OPENAI_KEY \
  -e EVALS_WANDB_KEY \
  runner python -m evals.evaluation_pipeline --mode generate-only
```

#### Evaluate Existing Dataset Only

```bash
docker compose exec \
  -e EVALS_SERVER_URL \
  -e EVALS_ACI_API_KEY \
  -e EVALS_OPENAI_KEY \
  -e EVALS_WANDB_KEY \
  runner python -m evals.evaluation_pipeline --mode evaluate-only
```

### Advanced Options

You can add flags to limit sample sizes or customize dataset names.

#### Quick Test Run Example

```bash
# Generate and evaluate with a small sample size of 10
docker compose exec \
  -e EVALS_SERVER_URL \
  -e EVALS_ACI_API_KEY \
  -e EVALS_OPENAI_KEY \
  -e EVALS_WANDB_KEY \
  runner python -m evals.evaluation_pipeline \
  --mode generate-and-evaluate \
  --generation-limit 10 \
  --evaluation-samples 10
```

## 4. Viewing Results

- **Console Output**: Metrics like accuracy, MRR, and response time will be printed directly to your terminal.
- **Weights & Biases**: If you provided a `EVALS_WANDB_KEY`, you can view detailed results and artifacts at [wandb.ai/aipotheosis-labs/function-search-evaluation](https://wandb.ai/aipotheosis-labs/function-search-evaluation).

## 5. Troubleshooting

- **"401 Unauthorized" Error**: This almost always means your environment variables aren't being passed correctly. Double-check that you have `export`ed the variables in your terminal and that you are including the `-e` flags in your `docker compose exec` command.
- **"No app and function data found"**: The database is likely empty. Rerun the seed script: `docker compose exec runner ./scripts/seed_db.sh --all --mock`.
- **OpenAI Errors**: Check that `EVALS_OPENAI_KEY` is set correctly and that the key is valid.
- **Docker Restart**: If you update variables in your `.env.local` file, you must restart the services for changes to take effect: `docker compose down && docker compose up -d`.
