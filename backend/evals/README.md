# Function Search Evaluation System

This directory contains tools for evaluating the performance of function search using synthetic intents generated with different difficulty levels.

## Overview

The evaluation system consists of:

1. **Intent Generation**: Generate synthetic user intents using different prompt templates
2. **Search Evaluation**: Test how well the search system matches intents to the correct functions
3. **Metrics Tracking**: Track performance metrics using Weights & Biases

## Prompt Types

The system supports three different prompt difficulty levels:

### `prompt_easy`
- **Difficulty**: Easy
- **Description**: User mentions the app name and has a straightforward goal
- **Use case**: Basic intent matching evaluation

### `prompt_medium`
- **Difficulty**: Medium
- **Description**: User mentions app name but avoids explicit function terms, embeds goals in business context
- **Use case**: More realistic, indirect intent matching

### `prompt_hard`
- **Difficulty**: Hard
- **Description**: User may or may not mention app name, uses broader contextual language
- **Use case**: Most challenging, real-world scenario testing

## Usage

### Command Line Interface

#### Basic Commands

Run the evaluation pipeline with different prompt types:

```bash
# Generate easy prompts and evaluate
python evaluation_pipeline.py --mode generate-and-evaluate --prompt-type prompt_easy

# Generate medium difficulty prompts only
python evaluation_pipeline.py --mode generate-only --prompt-type prompt_medium --generation-limit 100

# Evaluate existing dataset
python evaluation_pipeline.py --mode evaluate-only --dataset my_dataset --evaluation-samples 50

# Generate hard prompts with custom dataset name
python evaluation_pipeline.py --mode generate-and-evaluate --prompt-type prompt_hard --dataset hard_intent_dataset
```

#### Dataset Filename Parameter (`--dataset-filename`)

The `--dataset-filename` parameter allows you to specify custom filenames for your datasets. This is useful for organizing different evaluation runs and file formats.

**Default**: `synthetic_intents.json`

**Supported formats**: `.json` and `.csv`

##### Examples:

```bash
# Use custom JSON filename for generation
python evaluation_pipeline.py \
  --mode generate-only \
  --prompt-type prompt_medium \
  --dataset-filename synthetic_intent_med.json

# Use custom CSV filename
python evaluation_pipeline.py \
  --mode generate-only \
  --prompt-type prompt_easy \
  --dataset-filename easy_intents.csv

# Evaluate using specific dataset filename
python evaluation_pipeline.py \
  --mode evaluate-only \
  --dataset synthetic_intent_dataset_prompt_medium_evaluation_20250609_135609 \
  --dataset-filename synthetic_intent_med.json

# Generate and evaluate with custom filename
python evaluation_pipeline.py \
  --mode generate-and-evaluate \
  --prompt-type prompt_hard \
  --dataset-filename hard_evaluation_dataset.json \
  --generation-limit 50
```

##### Use Cases:

1. **Organizing by difficulty**:
   ```bash
   --dataset-filename easy_intents.json
   --dataset-filename medium_intents.json
   --dataset-filename hard_intents.json
   ```

2. **Organizing by date/version**:
   ```bash
   --dataset-filename intents_v2_20250609.json
   --dataset-filename baseline_eval.json
   ```

3. **Organizing by app focus**:
   ```bash
   --dataset-filename github_specific_intents.json
   --dataset-filename slack_evaluation.json
   ```

4. **Different file formats**:
   ```bash
   --dataset-filename results.csv  # For Excel compatibility
   --dataset-filename data.json    # For programmatic access
   ```

##### Important Notes:

- **File format detection**: The system automatically detects format based on file extension (`.json` or `.csv`)
- **Artifact naming**: The dataset filename doesn't affect W&B artifact names, only the internal file naming
- **Evaluation artifacts**: When evaluating, the system looks for `dataset_<filename>` in evaluation artifacts
- **Backward compatibility**: Existing datasets without custom filenames will continue to work
- **Case sensitivity**: Filenames are case-sensitive

### Programmatic Usage

```python
from intent_prompts import PROMPTS
import pandas as pd

# Sample data
row = pd.Series({
    "app_name": "github",
    "app_description": "GitHub is a platform for version control and collaboration",
    "function_name": "GITHUB_CREATE_REPOSITORY",
    "function_description": "Create a new repository in GitHub"
})

# Generate different prompt types
easy_prompt = PROMPTS["prompt_easy"](row)
medium_prompt = PROMPTS["prompt_medium"](row)
hard_prompt = PROMPTS["prompt_hard"](row)
```

### Example Demo

Run the example script to see all prompt types in action:

```bash
python example_usage.py
```

## Environment Variables

Set these environment variables before running evaluations:

```bash
export EVALS_SERVER_URL="http://localhost:8000"
export EVALS_ACI_API_KEY="your-api-key"
export EVALS_OPENAI_KEY="your-openai-key"
export EVALS_WANDB_KEY="your-wandb-key"
```

## Files

- `intent_prompts.py` - Prompt template definitions
- `synthetic_intent_generator.py` - Generate synthetic intents using OpenAI
- `search_evaluator.py` - Evaluate search performance
- `evaluation_pipeline.py` - Main pipeline orchestrator with CLI


## Metrics

The evaluation system tracks:

- **Accuracy**: Top-1 accuracy (correct function at rank 1)
- **MRR**: Mean Reciprocal Rank
- **Top-K Accuracy**: Accuracy at ranks 1, 3, and 5
- **Response Time**: Average API response time
- **Incorrect Results**: Detailed tracking of failed matches for analysis
