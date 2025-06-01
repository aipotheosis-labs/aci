import openai
import pandas as pd
import wandb
from dotenv import load_dotenv
from sqlalchemy import select
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tqdm import tqdm

from aci.cli import config
from aci.common import utils
from aci.common.db.sql_models import App, Function
from evals.intent_prompts import PROMPTS

load_dotenv()


class SyntheticIntentGenerator:
    """
    Generates synthetic intents for function search evaluation.

    This generator:
    1. Fetches app and function data from the database
    2. Generates synthetic intents using OpenAI's API
    3. Saves the dataset as a W&B artifact
    """

    def __init__(
        self,
        model: str,
        prompt_type: str,
        openai_api_key: str,
    ):
        """
        Initialize the generator with configuration.

        Args:
            model: OpenAI model to use for generation
            prompt_type: Type of prompt to use (must be in PROMPTS)
            openai_api_key: OpenAI API key
        """
        self.model = model
        self.prompt_type = prompt_type

        if prompt_type not in PROMPTS:
            raise ValueError(
                f"Invalid prompt type: {prompt_type}. Must be one of {list(PROMPTS.keys())}"
            )

        # Initialize API clients
        self.openai_client = openai.OpenAI(api_key=openai_api_key)

    def _fetch_app_function_data(self) -> pd.DataFrame:
        """
        Fetch app and function data from the database.

        Returns:
            DataFrame containing app and function information
        """
        db_session = utils.create_db_session(config.DB_FULL_URL)

        # Select specific columns from both App and Function tables
        statement = select(
            App.name.label("app_name"),
            App.description.label("app_description"),
            Function.name.label("function_name"),
            Function.description.label("function_description"),
        ).join(App, Function.app_id == App.id)

        # Execute the query and fetch results
        results = db_session.execute(statement).fetchall()

        return pd.DataFrame(results)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(openai.RateLimitError),
    )
    def _generate_intent(self, prompt: str) -> str:
        """
        Generate a single intent using OpenAI's API.

        Args:
            prompt: The prompt to send to the model

        Returns:
            Generated intent text
        """
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=30,  # seconds
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    def _log_dataset_stats(self, df: pd.DataFrame) -> None:
        """
        Log dataset statistics to wandb.

        Args:
            df: DataFrame containing the generated dataset
        """
        wandb.log(
            {
                "dataset_size": len(df),
            }
        )

    def _save_to_wandb(self, df: pd.DataFrame, dataset_artifact: str, dataset_filename: str) -> str:
        """
        Save the dataset as a wandb artifact.

        Args:
            df: DataFrame containing the generated dataset
            dataset_artifact: Name for the artifact
            dataset_filename: Filename to save the dataset to

        Returns:
            The artifact name for reference
        """
        artifact = wandb.Artifact(
            name=dataset_artifact,
            type="dataset",
            description=f"Synthetic intent dataset generated with {self.model} using {self.prompt_type} prompts",
            metadata={
                "model": self.model,
                "prompt": PROMPTS[self.prompt_type](
                    pd.Series(
                        {
                            "function_name": "FUNCTION_NAME",
                            "function_description": "FUNCTION_DESCRIPTION",
                            "app_name": "APP_NAME",
                            "app_description": "APP_DESCRIPTION",
                        }
                    )
                ),
            },
        )

        # Write dataframe to the temporary file
        df.to_csv(dataset_filename, index=False)
        # Add the file to the artifact
        artifact.add_file(dataset_filename)
        # Log the artifact
        wandb.log_artifact(artifact)

        return artifact.name

    def generate(
        self,
        dataset_artifact: str,
        dataset_filename: str,
        limit: int | None = None,
    ) -> pd.DataFrame:
        """
        Generate synthetic intents and save them.

        Args:
            dataset_artifact: Name of the artifact to save the dataset to
            dataset_filename: Filename to save the dataset to
            limit: Optional limit on number of samples to generate

        Returns:
            DataFrame containing the generated dataset
        """
        # Fetch data
        df = self._fetch_app_function_data()

        if df.empty:
            raise ValueError(
                "No app and function data found in the database. Please seed the database by running: 'docker compose exec runner ./scripts/seed_db.sh'. This command will populate the database with sample apps and functions required for intent generation."
            )

        if limit:
            df = df[:limit]

        # Generate intents
        df["prompt"] = df.apply(PROMPTS[self.prompt_type], axis=1)
        df["synthetic_output"] = [self._generate_intent(prompt) for prompt in tqdm(df["prompt"])]

        # Log and save
        self._log_dataset_stats(df)
        artifact_name = self._save_to_wandb(df, dataset_artifact, dataset_filename)

        print(f"Dataset saved as W&B artifact: {artifact_name}")
        return df
