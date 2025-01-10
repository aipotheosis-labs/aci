import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from aipolabs.common import embeddings
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import AppCreate
from aipolabs.common.schemas.function import FunctionCreate
from aipolabs.server import config

logger = logging.getLogger(__name__)
openai_service = OpenAIService(config.OPENAI_API_KEY)


def create_dummy_apps_and_functions(db_session: Session) -> list[App]:
    dummy_apps: list[App] = []
    # for app.json and functions.json in each dummy_apps directory, create an app and functions
    dummy_apps_dir = Path(__file__).parent / "dummy_apps"
    for app_dir in dummy_apps_dir.glob("*"):
        app_file = app_dir / "app.json"
        functions_file = app_dir / "functions.json"
        dummy_apps.append(_upsert_app_and_functions(db_session, app_file, functions_file))
    return dummy_apps


def _upsert_app_and_functions(db_session: Session, app_file: Path, functions_file: Path) -> App:
    """Upsert App and Functions to db from a json file."""
    with open(app_file, "r") as f:
        app: AppCreate = AppCreate.model_validate(json.load(f))
    with open(functions_file, "r") as f:
        functions: list[FunctionCreate] = [
            FunctionCreate.model_validate(function) for function in json.load(f)
        ]

    app_embedding = embeddings.generate_app_embedding(
        app, openai_service, config.OPENAI_EMBEDDING_MODEL, config.OPENAI_EMBEDDING_DIMENSION
    )
    function_embeddings = embeddings.generate_function_embeddings(
        functions, openai_service, config.OPENAI_EMBEDDING_MODEL, config.OPENAI_EMBEDDING_DIMENSION
    )

    # TODO: check app name and functio name match?
    logger.info(f"Upserting app and functions for app: {app.name}...")
    db_app = crud.apps.create_app(db_session, app, app_embedding)
    db_session.flush()
    crud.functions.create_functions(db_session, functions, function_embeddings)

    db_session.commit()

    return db_app
