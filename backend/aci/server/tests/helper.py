import json
import logging
from pathlib import Path

from openai import OpenAI

from aci.common import embeddings
from aci.common.schemas.app import AppEmbeddingFields, AppUpsert
from aci.common.schemas.function import FunctionEmbeddingFields, FunctionUpsert
from aci.server import config

logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
DUMMY_APPS_DIR = Path(__file__).parent / "dummy_apps"
REAL_APPS_DIR = Path(__file__).parent.parent.parent.parent / "apps"
CONNECTOR_APPS = [
    "agent_secrets_manager",
]


def prepare_dummy_apps_and_functions() -> list[
    tuple[AppUpsert, list[FunctionUpsert], list[float], list[list[float]]]
]:
    results: list[tuple[AppUpsert, list[FunctionUpsert], list[float], list[list[float]]]] = []
    """
    Prepare dummy apps and functions for testing.
    Returns a list of tuples, where each tuple contains:
    - AppUpsert: the app to to created in the db
    - list[FunctionUpsert]: the functions of the app to to created in the db
    - list[float]: the app embeddings
    - list[list[float]]: the embeddings for each function
    """
    for app_dir in [*DUMMY_APPS_DIR.glob("*"), *[REAL_APPS_DIR / app for app in CONNECTOR_APPS]]:
        app_file = app_dir / "app.json"
        functions_file = app_dir / "functions.json"
        with open(app_file) as f:
            app_upsert: AppUpsert = AppUpsert.model_validate(json.load(f))
            app_embedding_fields = AppEmbeddingFields.model_validate(app_upsert.model_dump())
        with open(functions_file) as f:
            functions_upsert: list[FunctionUpsert] = [
                FunctionUpsert.model_validate(function) for function in json.load(f)
            ]
            functions_embedding_fields: list[FunctionEmbeddingFields] = [
                FunctionEmbeddingFields.model_validate(function_upsert.model_dump())
                for function_upsert in functions_upsert
            ]
        # check function names match app name
        for function_upsert in functions_upsert:
            assert function_upsert.name.startswith(app_upsert.name)

        app_embedding = embeddings.generate_app_embedding(
            app_embedding_fields,
            openai_client,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )
        function_embeddings = embeddings.generate_function_embeddings(
            functions_embedding_fields,
            openai_client,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )
        results.append((app_upsert, functions_upsert, app_embedding, function_embeddings))
    return results
