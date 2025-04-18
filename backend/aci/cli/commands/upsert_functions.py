import json
from pathlib import Path

import click
from deepdiff import DeepDiff
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from sqlalchemy.orm import Session

from aci.cli import config
from aci.common import embeddings, utils
from aci.common.db import crud
from aci.common.schemas.function import FunctionEmbeddingFields, FunctionUpsert

console = Console()

openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


@click.command()
@click.option(
    "--functions-file",
    "functions_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the functions JSON file",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="Provide this flag to run the command and apply changes to the database",
)
def upsert_functions(functions_file: Path, skip_dry_run: bool) -> list[str]:
    """
    Upsert functions in the DB from a JSON file.

    This command groups the functions into three categories:
      - New functions to create,
      - Existing functions that require an update,
      - Functions that are unchanged.

    Batch creation and update operations are performed.
    """
    return upsert_functions_helper(functions_file, skip_dry_run)


def upsert_functions_helper(functions_file: Path, skip_dry_run: bool) -> list[str]:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        with open(functions_file) as f:
            functions_data = json.load(f)

        # Validate and parse each function record
        functions_upsert = [
            FunctionUpsert.model_validate(func_data) for func_data in functions_data
        ]
        app_name = _validate_all_functions_belong_to_the_app(functions_upsert)
        console.rule(f"App={app_name}")
        _validate_app_exists(db_session, app_name)

        new_functions: list[FunctionUpsert] = []
        existing_functions: list[FunctionUpsert] = []

        for function_upsert in functions_upsert:
            existing_function = crud.functions.get_function(
                db_session, function_upsert.name, public_only=False, active_only=False
            )

            if existing_function is None:
                new_functions.append(function_upsert)
            else:
                existing_functions.append(function_upsert)

        console.rule("Checking functions to create...")
        functions_created = create_functions_helper(db_session, new_functions)
        console.rule("Checking functions to update...")
        functions_updated = update_functions_helper(db_session, existing_functions)
        # for functions that are in existing_functions but not in functions_updated
        functions_unchanged = [
            func.name for func in existing_functions if func.name not in functions_updated
        ]

        if not skip_dry_run:
            console.rule("Provide [bold green]--skip-dry-run[/bold green] to upsert functions")
            db_session.rollback()
        else:
            db_session.commit()
            console.rule("[bold green]Upserted functions[/bold green]")

        table = Table("Function Name", "Operation")
        for func in functions_created:
            table.add_row(func, "Create")
        for func in functions_updated:
            table.add_row(func, "Update")
        for func in functions_unchanged:
            table.add_row(func, "No changes")

        console.print(table)

        return functions_created + functions_updated


def create_functions_helper(
    db_session: Session, functions_upsert: list[FunctionUpsert]
) -> list[str]:
    """
    Batch creates functions in the database.
    Generates embeddings for each new function and calls the CRUD layer for creation.
    Returns a list of created function names.
    """
    functions_embeddings = embeddings.generate_function_embeddings(
        [FunctionEmbeddingFields.model_validate(func.model_dump()) for func in functions_upsert],
        openai_client,
        embedding_model=config.OPENAI_EMBEDDING_MODEL,
        embedding_dimension=config.OPENAI_EMBEDDING_DIMENSION,
    )
    created_functions = crud.functions.create_functions(
        db_session, functions_upsert, functions_embeddings
    )

    return [func.name for func in created_functions]


def update_functions_helper(
    db_session: Session, functions_upsert: list[FunctionUpsert]
) -> list[str]:
    """
    Batch updates functions in the database.

    For each function to update, determines if the embedding needs to be regenerated.
    Regenerates embeddings in batch for those that require it and updates the functions accordingly.
    Returns a list of updated function names.
    """
    functions_with_new_embeddings: list[FunctionUpsert] = []
    functions_without_new_embeddings: list[FunctionUpsert] = []

    for function_upsert in functions_upsert:
        existing_function = crud.functions.get_function(
            db_session, function_upsert.name, public_only=False, active_only=False
        )
        if existing_function is None:
            raise click.ClickException(f"Function '{function_upsert.name}' not found.")
        existing_function_upsert = FunctionUpsert.model_validate(
            existing_function, from_attributes=True
        )
        if existing_function_upsert == function_upsert:
            continue
        else:
            diff = DeepDiff(
                existing_function_upsert.model_dump(),
                function_upsert.model_dump(),
                ignore_order=True,
            )
            console.rule(
                f"Will update function '{existing_function.name}' with the following changes:"
            )
            console.print(diff.pretty())

        if _need_function_embedding_regeneration(existing_function_upsert, function_upsert):
            functions_with_new_embeddings.append(function_upsert)
        else:
            functions_without_new_embeddings.append(function_upsert)

    # Generate new embeddings in batch for functions that require regeneration.
    functions_embeddings = embeddings.generate_function_embeddings(
        [
            FunctionEmbeddingFields.model_validate(func.model_dump())
            for func in functions_with_new_embeddings
        ],
        openai_client,
        embedding_model=config.OPENAI_EMBEDDING_MODEL,
        embedding_dimension=config.OPENAI_EMBEDDING_DIMENSION,
    )

    # Note: the order matters here because the embeddings need to match the functions
    functions_updated = crud.functions.update_functions(
        db_session,
        functions_with_new_embeddings + functions_without_new_embeddings,
        functions_embeddings + [None] * len(functions_without_new_embeddings),
    )

    return [func.name for func in functions_updated]


def _validate_app_exists(db_session: Session, app_name: str) -> None:
    app = crud.apps.get_app(db_session, app_name, False, False)
    if not app:
        raise click.ClickException(f"App={app_name} does not exist")


def _validate_all_functions_belong_to_the_app(
    functions_upsert: list[FunctionUpsert],
) -> str:
    app_names = {utils.parse_app_name_from_function_name(func.name) for func in functions_upsert}
    if len(app_names) != 1:
        raise click.ClickException(
            f"All functions must belong to the same app, instead found multiple apps={app_names}"
        )

    return app_names.pop()


def _need_function_embedding_regeneration(
    old_func: FunctionUpsert, new_func: FunctionUpsert
) -> bool:
    """
    Determines if the function embedding should be regenerated based on changes in the
    fields used for embedding (name, description, parameters).
    """
    fields = set(FunctionEmbeddingFields.model_fields.keys())
    return bool(old_func.model_dump(include=fields) != new_func.model_dump(include=fields))
