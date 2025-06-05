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
- `example_usage.py` - Demo script showing prompt types
- `prompt.md` - Original prompt templates documentation

## Metrics

The evaluation system tracks:

- **Accuracy**: Top-1 accuracy (correct function at rank 1)
- **MRR**: Mean Reciprocal Rank
- **Top-K Accuracy**: Accuracy at ranks 1, 3, and 5
- **Response Time**: Average API response time
- **Incorrect Results**: Detailed tracking of failed matches for analysis
