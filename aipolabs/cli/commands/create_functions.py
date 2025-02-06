import json
from pathlib import Path
from uuid import UUID

import click

from aipolabs.cli import config
from aipolabs.common import embeddings, utils
from aipolabs.common.db import crud
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.function import FunctionCreate

openai_service = OpenAIService(config.OPENAI_API_KEY)


@click.command()
@click.option(
    "--functions-file",
    "functions_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the function json file",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="provide this flag to run the command and apply changes to the database",
)
def create_functions(functions_file: Path, skip_dry_run: bool) -> list[UUID]:
    """Create Functions in db from file."""
    return create_functions_helper(functions_file, skip_dry_run)


def create_functions_helper(functions_file: Path, skip_dry_run: bool) -> list[UUID]:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        with open(functions_file, "r") as f:
            functions_create: list[FunctionCreate] = [
                FunctionCreate.model_validate(function) for function in json.load(f)
            ]

        function_embeddings = embeddings.generate_function_embeddings(
            functions_create,
            openai_service,
            embedding_model=config.OPENAI_EMBEDDING_MODEL,
            embedding_dimension=config.OPENAI_EMBEDDING_DIMENSION,
        )

        functions = crud.functions.create_functions(
            db_session, functions_create, function_embeddings
        )
        if not skip_dry_run:
            click.echo(create_headline(f"will create {len(functions)} functions"))
            for function in functions:
                click.echo(function.name)
            click.echo(create_headline("provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"committing creation of {len(functions)} functions"))
            for function in functions:
                click.echo(f"function id={function.id}, name={function.name}")
            db_session.commit()

        return [function.id for function in functions]
