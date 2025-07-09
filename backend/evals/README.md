# Guide to Running ACI Evaluation Pipeline

## 1. Environment Configuration

### Step 1: Navigate to Backend Directory

```bash
cd ~/aci/backend
```

### Step 2: Create and Configure `.env.local`

```bash
# Create the .env.local file from the example
cp .env.example .env.local
```

Now, edit the `.env.local` file with your OpenAI API key:

- **What to edit**: `SERVER_OPENAI_API_KEY` and `CLI_OPENAI_API_KEY`
- **Where to get key**: [OpenAI API Keys page](https://platform.openai.com/api-keys)

Your `.env.local` should look like this (with your actual key):

```
SERVER_OPENAI_API_KEY=sk-proj-your-actual-openai-key
CLI_OPENAI_API_KEY=sk-proj-your-actual-openai-key
```

### Step 3: Set Up Evaluation Environment Variables

These are needed to pass credentials to the evaluation script inside Docker.

```bash
# Get your Weights & Biases API key from wandb.ai/authorize
# then type wandb login on your terminal to setup the api key in terminal
# Then set these environment variables in your terminal:
EVALS_SERVER_URL=http://localhost:8000
EVALS_ACI_API_KEY=<your_api_key_for_the_server_returned_from_seed_db_script>
EVALS_OPENAI_KEY=<your_openai_api_key>
EVALS_WANDB_KEY=<your_wandb_api_key>
```

**Important**: You'll get the `EVALS_ACI_API_KEY` in a later step.

## 2. Running Docker Commands

### Step 4: Stop and Remove Old Containers

```bash
docker compose down
```

### Step 5: Pull Latest Images and Rebuild

```bash
docker compose pull
docker compose build
```

### Step 6: Start All Services

```bash
docker compose up -d
```

### Step 7: Verify Services are Running

```bash
docker compose ps
```

Look for `running` or `healthy` status for all services.

### Step 8: Wait for Database to be Ready

```bash
# Check logs to see when the database is ready
docker compose logs -f db
# Press Ctrl+C to exit when you see "database system is ready to accept connections"
```

### Step 9: Seed Database and Get ACI API Key

```bash
# Seed with all apps and mock credentials
# this creates a mock db for you to configure and test few mock apps
docker compose exec runner ./scripts/seed_db.sh --all --mock
```

This will output an API key like:

```
{
    'Project Id': '65cf26b9-a919-4008-85de-ecb850c3fc36',
    'Agent Id': '74273ac1-f68e-4314-b8be-fee4a5855d8a',
    'API Key': '88c55e31e817bd2d48aa455e94b61e766fb6e6610c97abe6f724733bf222e3e0'
}
```

**Copy the `API Key` value and set it as an environment variable:**

```bash
EVALS_ACI_API_KEY=88c55e31e8--
# Use your actual key
```

## 3. Running the Evaluation Pipeline

Now you're ready to run the evaluation! Here are the different modes and options:

### Basic Modes

#### Generate and Evaluate (Recommended)

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

#### Limit Sample Size

```bash
# Generate only 10 samples
docker compose exec runner python -m evals.evaluation_pipeline \
  --mode generate-only \
  --generation-limit 10

# Evaluate only 5 samples
docker compose exec runner python -m evals.evaluation_pipeline \
  --mode evaluate-only \
  --evaluation-samples 5
```

#### Custom Dataset Names

```bash
# Use custom artifact name and filename
docker compose exec runner python -m evals.evaluation_pipeline \
  --mode generate-and-evaluate \
  --dataset-artifact my_custom_dataset \
  --dataset-filename my_intents.csv
```

### Quick Test Run Example

```bash
# Generate and evaluate with a small sample size
docker compose exec runner python -m evals.evaluation_pipeline \
  --mode generate-and-evaluate \
  --generation-limit 10 \
  --evaluation-samples 10
```

## 4. Viewing Results

- **Console Output**: Metrics like accuracy, MRR, and response time will be printed
- **Weights & Biases**: Visit [wandb.ai/aipotheosis-labs/function-search-evaluation](https://wandb.ai/aipotheosis-labs/function-search-evaluation)

## 5. Troubleshooting

- **"401 Unauthorized" Error**: Your environment variables aren't being passed correctly. Make sure you use the `-e` flags with `docker compose exec`.
- **"No app and function data found"**: Rerun the seed script: `docker compose exec runner ./scripts/seed_db.sh --all --mock`.
- **OpenAI Errors**: Check your OpenAI key in `.env.local` and restart Docker.
- **W&B Login Issues**: Run `docker compose exec runner wandb login` and enter your W&B API key.
