import logging
import os

import click
import pandas as pd

import wandb

# Import after environment is loaded
from evals.intent_prompts import PROMPTS
from evals.search_evaluator import SearchEvaluator
from evals.synthetic_intent_generator import SyntheticIntentGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress verbose httpx logging
logging.getLogger("httpx").setLevel(logging.WARNING)

DEFAULT_DATASET_ARTIFACT = "synthetic_intent_dataset"
DEFAULT_DATASET_FILENAME = "synthetic_intents.json"
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
        prompt_type: str = "prompt_easy",
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

        dataset_path = os.path.join(artifact_dir, dataset_filename)
        return pd.read_json(dataset_path, orient="records")

    def _create_composite_artifact(
        self,
        dataset_artifact: str,
        dataset_filename: str,
        df: pd.DataFrame,
        detailed_metrics: dict,
        incorrect_results: list,
    ) -> str:
        """
        Create a composite artifact with properly written files.

        Args:
            dataset_artifact: Name of the dataset artifact
            dataset_filename: Filename for the dataset
            df: DataFrame containing the dataset
            detailed_metrics: Dictionary of detailed metrics
            incorrect_results: List of incorrect results

        Returns:
            Name of the created artifact
        """
        import json
        import os
        import tempfile

        # Create composite artifact without automatic suffixes
        composite_artifact_name = dataset_artifact

        composite_artifact = wandb.Artifact(
            name=composite_artifact_name,
            type="dataset",
            description=f"Composite evaluation results for {dataset_artifact} - includes dataset, metrics, and incorrect predictions",
        )

        temp_files = []

        try:
            # Create dataset file
            if df is not None:
                dataset_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                temp_files.append(dataset_file.name)
                # Write data and ensure it's flushed to disk
                df.to_json(dataset_file.name, orient="records", indent=2)
                dataset_file.close()  # Explicitly close to ensure data is written
                composite_artifact.add_file(dataset_file.name, name=dataset_filename)

            # Create metrics file
            metrics_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            temp_files.append(metrics_file.name)
            # Write data and ensure it's flushed to disk
            with open(metrics_file.name, "w") as f:
                json.dump(detailed_metrics, f, indent=2)
            metrics_file.close()  # Explicitly close
            composite_artifact.add_file(metrics_file.name, name="detailed_metrics.json")

            # Create incorrect results file if any exist
            if incorrect_results:
                incorrect_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
                temp_files.append(incorrect_file.name)
                # Write data and ensure it's flushed to disk
                with open(incorrect_file.name, "w") as f:
                    json.dump(incorrect_results, f, indent=2)
                incorrect_file.close()  # Explicitly close
                composite_artifact.add_file(incorrect_file.name, name="incorrect_results.json")

            # Log the composite artifact
            wandb.log_artifact(composite_artifact)

            logger.info(
                f"Saved composite evaluation results to artifact: {composite_artifact_name}"
            )
            if incorrect_results:
                logger.info(f"Included {len(incorrect_results)} incorrect results for analysis")

            return composite_artifact_name

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

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

        # Extract incorrect results for the composite artifact
        incorrect_results = metrics.pop("incorrect_results", [])

        # Create detailed metrics
        detailed_metrics = {
            "correct": metrics["correct"],
            "mrr": metrics["mrr"],
            "response_time": metrics["response_time"],
            "top_k": metrics["top_k"],
            "avg_response_time": metrics["avg_response_time"],
            "total_samples": metrics["total_samples"],
            "incorrect_count": len(incorrect_results),
            "evaluation_config": {
                "prompt_type": self.prompt_type,
                "model": self.model,
                "evaluation_samples": evaluation_samples,
                "dataset_artifact": dataset_artifact,
            },
        }

        # Create composite artifact with all files using the new method
        self._create_composite_artifact(
            dataset_artifact=dataset_artifact,
            dataset_filename=dataset_filename,
            df=df,
            detailed_metrics=detailed_metrics,
            incorrect_results=incorrect_results,
        )

        # Log only summary metrics to wandb
        summary_metrics = {
            "correct": metrics["correct"],
            "mrr": metrics["mrr"],
            "avg_response_time": metrics["avg_response_time"],
            "total_samples": metrics["total_samples"],
            "incorrect_count": len(incorrect_results),
        }
        wandb.log(summary_metrics)

        # Log concise results
        logger.info("Evaluation Results:")
        logger.info(f"Correct: {metrics['correct']}")
        logger.info(f"MRR: {metrics['mrr']:.3f}")
        logger.info(f"Top-K: {metrics['top_k']}")
        logger.info(f"Average Response Time: {metrics['avg_response_time']:.2f}s")
        logger.info(f"Total Samples: {metrics['total_samples']}")
        logger.info(f"Incorrect Predictions: {len(incorrect_results)}")

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
                "prompt_type": self.prompt_type,
                "generation_model": self.model,
            },
        )

        df = None
        try:
            if generate_data:
                # For generate-only mode, still create the dataset artifact
                # For generate-and-evaluate mode, we'll include it in the composite evaluation artifact
                if not evaluate_data:
                    # Generate-only mode: create separate dataset artifact
                    df = self._generate(
                        dataset_artifact=dataset_artifact,
                        dataset_filename=dataset_filename,
                        generation_limit=generation_limit,
                    )
                else:
                    # Generate-and-evaluate mode: generate but don't save separately
                    # The dataset will be included in the composite evaluation artifact
                    logger.info("Generating synthetic intents...")
                    df = self.generator._fetch_app_function_data()

                    if df.empty:
                        raise ValueError(
                            "No app and function data found in the database. Please seed the database."
                        )

                    if generation_limit:
                        df = df[:generation_limit]

                    # Generate intents
                    from tqdm import tqdm

                    from evals.intent_prompts import PROMPTS

                    df[self.prompt_type] = df.apply(PROMPTS[self.prompt_type], axis=1)
                    df["synthetic_output"] = [
                        self.generator._generate_intent(prompt)
                        for prompt in tqdm(df[self.prompt_type])
                    ]

                    logger.info(f"Generated {len(df)} synthetic intents")

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
    "--prompt-type",
    type=click.Choice(list(PROMPTS.keys())),
    default="prompt_easy",
    help="Type of prompt to use for intent generation",
    show_default=True,
)
@click.option(
    "--dataset",
    default=DEFAULT_DATASET_ARTIFACT,
    help="Name of the W&B dataset artifact to use",
    show_default=True,
)
@click.option(
    "--dataset-filename",
    default=DEFAULT_DATASET_FILENAME,
    type=str,
    help="Filename to save the generated dataset to (supports .json)",
    show_default=True,
)
@click.option("--generation-limit", type=int, help="Limit number of samples to generate")
@click.option("--evaluation-samples", type=int, help="Limit number of samples to evaluate")
def main(
    mode: str,
    prompt_type: str,
    dataset: str,
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

    # Automatically append prompt type to dataset name for better organization
    # BUT don't append if it's already an evaluation artifact
    if "_evaluation" in dataset:
        # This is already an evaluation artifact, use as-is
        dataset_with_prompt = dataset
    elif dataset == DEFAULT_DATASET_ARTIFACT:
        dataset_with_prompt = f"{dataset}_{prompt_type}"
    else:
        # If user provided custom dataset name, still append prompt type
        dataset_with_prompt = f"{dataset}_{prompt_type}"

    # Create pipeline
    pipeline = EvaluationPipeline(
        search_server_url=str(search_server_url),
        search_api_key=str(search_api_key),
        openai_api_key=str(openai_api_key),
        wandb_token=str(wandb_token),
        prompt_type=prompt_type,
    )

    # Determine operation modes
    generate_data = mode in ["generate-only", "generate-and-evaluate"]
    evaluate_data = mode in ["evaluate-only", "generate-and-evaluate"]

    # Run pipeline
    pipeline.run(
        dataset_artifact=dataset_with_prompt,
        dataset_filename=dataset_filename,
        generate_data=generate_data,
        evaluate_data=evaluate_data,
        generation_limit=generation_limit,
        evaluation_samples=evaluation_samples,
    )


if __name__ == "__main__":
    main()
