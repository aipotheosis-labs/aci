import logging
import os

import click
import pandas as pd
import wandb

from evals.search_evaluator import SearchEvaluator
from evals.synthetic_intent_generator import SyntheticIntentGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DATASET_ARTIFACT = "synthetic_intent_dataset"
DEFAULT_DATASET_FILENAME = "synthetic_intents.csv"
DEFAULT_EVALUATION_MODEL = "dual-encoder-text-embedding-1024"


class EvaluationPipeline:
    """
    Pipeline for generating synthetic intents and evaluating search performance.

    This pipeline:
    1. Optionally generates synthetic intents
    2. Optionally evaluates search performance on the dataset
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

    def _load_dataset_from_wandb(self, artifact_name: str, dataset_filename: str) -> pd.DataFrame:
        """
        Load a dataset from a W&B artifact.

        Args:
            artifact_name: Name of the W&B artifact
            dataset_filename: Filename to save the dataset to
        Returns:
            DataFrame containing the dataset
        """
        artifact = wandb.use_artifact(f"{artifact_name}:latest")
        artifact_dir = artifact.download()
        return pd.read_csv(os.path.join(artifact_dir, dataset_filename))

    def _generate(
        self,
        dataset_artifact: str,
        dataset_filename: str,
        generation_limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Generate synthetic intents.

        Args:
            dataset_artifact: Name of the artifact to save the dataset to
            dataset_filename: Filename to save the dataset to
            generation_limit: Optional limit on number of samples to generate

        Returns:
            DataFrame containing the generated dataset
        """
        logger.info("Generating synthetic intents...")
        df = self.generator.generate(
            dataset_artifact=dataset_artifact,
            dataset_filename=dataset_filename,
            limit=generation_limit,
        )

        logger.info(f"Generated {len(df)} synthetic intents")
        return df

    def _evaluate(
        self,
        dataset_artifact: str,
        dataset_filename: str,
        evaluation_samples: int | None = None,
        df: pd.DataFrame | None = None,
    ) -> dict:
        """
        Evaluate search performance on a dataset.

        Args:
            dataset_artifact: Name of the dataset artifact to evaluate
            dataset_filename: Filename of the dataset in the artifact
            evaluation_samples: Optional limit on number of samples to evaluate
            df: Optional DataFrame containing the dataset. If None, load from dataset_artifact

        Returns:
            Dictionary containing evaluation metrics
        """
        if df is None:
            logger.info(f"Loading dataset from artifact: {dataset_artifact}")
            df = self._load_dataset_from_wandb(dataset_artifact, dataset_filename)

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

    def run(
        self,
        dataset_artifact: str,
        dataset_filename: str,
        generate_data: bool = False,
        evaluate_data: bool = True,
        generation_limit: int | None = None,
        evaluation_samples: int | None = None,
    ) -> None:
        """
        Run the evaluation pipeline.

        Args:
            dataset_artifact: Name of dataset artifact to use
            dataset_filename: Filename to save/load the dataset to/from
            generate_data: Whether to generate new data
            evaluate_data: Whether to evaluate data
            generation_limit: Optional limit on number of samples to generate
            evaluation_samples: Optional limit on number of samples to evaluate

        Returns:
            Dictionary containing evaluation metrics if evaluation was performed, None otherwise
        """
        # Initialize wandb run
        wandb.login(key=self.wandb_token)
        wandb.init(
            project="function-search-evaluation",
            job_type="pipeline",
            config={
                "generate_data": generate_data,
                "evaluate_data": evaluate_data,
                "generation_limit": generation_limit,
                "evaluation_model": DEFAULT_EVALUATION_MODEL,
                "evaluation_samples": evaluation_samples,
                "dataset_artifact": dataset_artifact,
                "dataset_filename": dataset_filename,
            },
        )

        df = None
        try:
            if generate_data:
                df = self._generate(
                    dataset_artifact=dataset_artifact,
                    dataset_filename=dataset_filename,
                    generation_limit=generation_limit,
                )

            if evaluate_data:
                self._evaluate(
                    dataset_artifact=dataset_artifact,
                    dataset_filename=dataset_filename,
                    evaluation_samples=evaluation_samples,
                    df=df,
                )

        finally:
            wandb.finish()


@click.command(help="Run function search evaluation pipeline")
@click.option(
    "--mode",
    type=click.Choice(["generate-only", "evaluate-only", "generate-and-evaluate"]),
    help="Operation mode: generate only, evaluate only, or both",
    required=True,
)
@click.option(
    "--dataset-artifact",
    default=DEFAULT_DATASET_ARTIFACT,
    help="Name of the W&B dataset artifact to use",
    show_default=True,
)
@click.option(
    "--dataset-filename",
    default=DEFAULT_DATASET_FILENAME,
    type=str,
    help="Filename to save the generated dataset to",
    show_default=True,
)
@click.option("--generation-limit", type=int, help="Limit number of samples to generate")
@click.option("--evaluation-samples", type=int, help="Limit number of samples to evaluate")
def main(
    mode: str,
    dataset_artifact: str,
    generation_limit: int | None,
    evaluation_samples: int | None,
    dataset_filename: str,
) -> None:
    """Main entry point for the evaluation pipeline."""
    # Get API keys from environment
    search_server_url = os.getenv("EVALS_SERVER_URL")
    search_api_key = os.getenv("EVALS_ACI_API_KEY")
    openai_api_key = os.getenv("EVALS_OPENAI_KEY")
    wandb_token = os.getenv("EVALS_WANDB_KEY")

    if not all([search_server_url, search_api_key, openai_api_key, wandb_token]):
        raise click.ClickException(
            "EVALS_SERVER_URL, EVALS_ACI_API_KEY, EVALS_OPENAI_KEY, and EVALS_WANDB_KEY must be set in environment"
        )

    # Create pipeline
    pipeline = EvaluationPipeline(
        search_server_url=str(search_server_url),
        search_api_key=str(search_api_key),
        openai_api_key=str(openai_api_key),
        wandb_token=str(wandb_token),
    )

    # Determine operation modes
    generate_data = mode in ["generate-only", "generate-and-evaluate"]
    evaluate_data = mode in ["evaluate-only", "generate-and-evaluate"]

    # Run pipeline
    pipeline.run(
        dataset_artifact=dataset_artifact,
        dataset_filename=dataset_filename,
        generate_data=generate_data,
        evaluate_data=evaluate_data,
        generation_limit=generation_limit,
        evaluation_samples=evaluation_samples,
    )


if __name__ == "__main__":
    main()
