import os

import openai
import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv
from intent_prompts import PROMPTS
from sqlalchemy import select
from tqdm import tqdm

from aci.cli import config
from aci.common import utils
from aci.common.db.sql_models import App, Function

load_dotenv()


def generate_synthetic_intent_dataset(
    hf_dataset_name: str,
    model: str,
    prompt_type: str,
) -> None:
    """
    Generates synthetic data using OpenAI's API.

    Args:
        openai_api_key (str): OpenAI API key
        model (str): OpenAI model to use
        output_path (str): Path to save the output parquet file
    """
    client = openai.OpenAI(api_key=os.getenv("EVALS_OPENAI_KEY"))

    if prompt_type not in PROMPTS:
        raise ValueError(
            f"Invalid prompt type: {prompt_type}. Must be one of {list(PROMPTS.keys())}"
        )

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

    # Create a dataframe with the results
    df = pd.DataFrame(results)

    def call_chatgpt(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        return content.strip() if content is not None else ""

    df["prompt"] = df.apply(PROMPTS[prompt_type], axis=1)
    df["synthetic_output"] = [call_chatgpt(prompt) for prompt in tqdm(df["prompt"])]

    # Upload dataset to Hugging Face
    dataset = Dataset.from_pandas(df)
    dataset.push_to_hub(hf_dataset_name, token=os.getenv("EVALS_HF_TOKEN"), private=True)

    print(f"Dataset uploaded to {hf_dataset_name}")


if __name__ == "__main__":
    generate_synthetic_intent_dataset(
        hf_dataset_name="Aipolabs/function_search_synthetic_data",
        model="gpt-4o-mini",
        prompt_type="task",
    )
