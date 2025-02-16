import json
import logging
from pathlib import Path

from aipolabs.common import embeddings
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import AppEmbeddingFields, AppUpsert
from aipolabs.common.schemas.function import FunctionCreate
from aipolabs.server import config

logger = logging.getLogger(__name__)
openai_service = OpenAIService(config.OPENAI_API_KEY)
DUMMY_APPS_DIR = Path(__file__).parent / "dummy_apps"


def prepare_dummy_apps_and_functions() -> (
    list[tuple[AppUpsert, list[FunctionCreate], list[float], list[list[float]]]]
):
    results: list[tuple[AppUpsert, list[FunctionCreate], list[float], list[list[float]]]] = []
    """
    Prepare dummy apps and functions for testing.
    Returns a list of tuples, where each tuple contains:
    - AppUpsert: the app to to created in the db
    - list[FunctionCreate]: the functions of the app to to created in the db
    - list[float]: the app embeddings
    - list[list[float]]: the embeddings for each function
    """
    for app_dir in DUMMY_APPS_DIR.glob("*"):
        app_file = app_dir / "app.json"
        functions_file = app_dir / "functions.json"
        with open(app_file, "r") as f:
            app_data = json.load(f)
            app_upsert: AppUpsert = AppUpsert.model_validate(app_data)
            app_embedding_fields = AppEmbeddingFields.model_validate(app_data)
        with open(functions_file, "r") as f:
            functions_create: list[FunctionCreate] = [
                FunctionCreate.model_validate(function) for function in json.load(f)
            ]
        # check function names match app name
        for function_create in functions_create:
            assert function_create.name.startswith(app_upsert.name)

        app_embedding = embeddings.generate_app_embedding(
            app_embedding_fields,
            openai_service,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )
        function_embeddings = embeddings.generate_function_embeddings(
            functions_create,
            openai_service,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )
        results.append((app_upsert, functions_create, app_embedding, function_embeddings))
    return results
