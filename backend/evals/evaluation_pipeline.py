import argparse
import logging
import os

import pandas as pd
import wandb
from dotenv import load_dotenv

from evals.search_evaluator import SearchEvaluator
from evals.synthetic_intent_generator import SyntheticIntentGenerator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DATASET_ARTIFACT = "synthetic_intent_dataset"
DEFAULT_EVALUATION_MODEL = "dual-encoder-text-embedding-1024"


class EvaluationPipeline:
    """
    Pipeline for generating synthetic intents and evaluating search performance.

    This pipeline:
    1. Optionally generates synthetic intents
    2. Evaluates search performance on the dataset
    3. Tracks results in Weights & Biases
    """

    def __init__(
        self,
        search_server_url: str,
        search_api_key: str,
        openai_api_key: str,
        wandb_token: str,
        model: str = "gpt-4o-mini",
        prompt_type: str = "task",
    ):
        """
        Initialize the pipeline with configuration.

        Args:
            search_server_url: Base URL of the search API
            search_api_key: API key for search API
            openai_api_key: OpenAI API key
            wandb_token: Weights & Biases API token
            model: OpenAI model to use for generation
            prompt_type: Type of prompt to use
        """
        self.model = model
        self.prompt_type = prompt_type
        self.wandb_token = wandb_token

        # Initialize components
        self.generator = SyntheticIntentGenerator(
            model=model,
            prompt_type=prompt_type,
            openai_api_key=openai_api_key,
        )
        self.evaluator = SearchEvaluator(
            api_url=search_server_url,
            api_key=search_api_key,
        )

    def _load_dataset_from_wandb(self, artifact_name: str) -> pd.DataFrame:
        """
        Load a dataset from a W&B artifact.

        Args:
            artifact_name: Name of the W&B artifact

        Returns:
            DataFrame containing the dataset
        """
        artifact = wandb.use_artifact(f"{artifact_name}:latest")
        artifact_dir = artifact.download()
        return pd.read_csv(os.path.join(artifact_dir, "temp_dataset.csv"))

    def run(
        self,
        dataset_artifact: str,
        generate_data: bool = False,
        generation_limit: int | None = None,
        evaluation_samples: int | None = None,
    ) -> dict:
        """
        Run the evaluation pipeline.

        Args:
            generate_data: Whether to generate new data
            generation_limit: Optional limit on number of samples to generate
            evaluation_samples: Optional limit on number of samples to evaluate
            dataset_artifact: Optional name of existing dataset artifact to use

        Returns:
            Dictionary containing evaluation metrics
        """
        # Initialize wandb run
        wandb.login(key=self.wandb_token)
        wandb.init(
            project="function-search-evaluation",
            job_type="evaluation",
            config={
                "generate_data": generate_data,
                "generation_limit": generation_limit,
                "evaluation_model": DEFAULT_EVALUATION_MODEL,
                "evaluation_samples": evaluation_samples,
                "dataset_artifact": dataset_artifact,
            },
        )

        try:
            # Handle dataset
            if generate_data:
                logger.info("Generating synthetic intents...")
                df = self.generator.generate(
                    dataset_artifact=DEFAULT_DATASET_ARTIFACT,
                    limit=generation_limit,
                )
            else:
                logger.info(f"Loading dataset from artifact: {dataset_artifact}")
                df = self._load_dataset_from_wandb(dataset_artifact)

            # Evaluate search performance
            logger.info("Evaluating search performance...")
            metrics = self.evaluator.evaluate_dataset(
                dataset=df,
                num_samples=evaluation_samples,
            )

            # Log metrics to wandb
            wandb.log(metrics)

            # Log results
            logger.info("Evaluation Results:")
            logger.info(f"Accuracy: {metrics['accuracy']:.2%}")
            logger.info(f"MRR: {metrics['mrr']:.3f}")
            logger.info(f"Top-K Accuracy: {metrics['top_k_accuracy']}")
            logger.info(f"Average Response Time: {metrics['avg_response_time']:.2f}s")
            logger.info(f"Total Samples: {metrics['total_samples']}")
            logger.info(f"Correct Predictions: {metrics['correct_predictions']}")

            return metrics

        finally:
            wandb.finish()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run function search evaluation pipeline")
    parse_group = parser.add_mutually_exclusive_group()
    parse_group.add_argument(
        "--generate", action="store_true", default=False, help="Generate new synthetic data"
    )
    parse_group.add_argument(
        "--dataset",
        default=DEFAULT_DATASET_ARTIFACT,
        help="Name of existing W&B dataset artifact to use (default: synthetic_intent_dataset:latest)",
    )
    parser.add_argument("--generation-limit", type=int, help="Limit number of samples to generate")
    parser.add_argument(
        "--evaluation-samples", type=int, help="Limit number of samples to evaluate"
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the evaluation pipeline."""
    args = parse_args()

    # Get API keys from environment
    search_server_url = os.getenv("EVALS_SERVER_URL")
    search_api_key = os.getenv("EVALS_ACI_API_KEY")
    openai_api_key = os.getenv("EVALS_OPENAI_KEY")
    wandb_token = os.getenv("EVALS_WANDB_KEY")

    if not all([search_server_url, search_api_key, openai_api_key, wandb_token]):
        raise ValueError(
            "EVALS_SERVER_URL, EVALS_ACI_API_KEY, EVALS_OPENAI_KEY, and EVALS_WANDB_KEY must be set in environment"
        )

    # Create and run pipeline
    pipeline = EvaluationPipeline(
        search_server_url=str(search_server_url),
        search_api_key=str(search_api_key),
        openai_api_key=str(openai_api_key),
        wandb_token=str(wandb_token),
    )
    pipeline.run(
        generate_data=args.generate,
        dataset_artifact=args.dataset,
        generation_limit=args.generation_limit,
        evaluation_samples=args.evaluation_samples,
    )


if __name__ == "__main__":
    main()
