import json
from pathlib import Path
from uuid import UUID

import click
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from sqlalchemy.orm import Session

from aipolabs.cli import config
from aipolabs.common import embeddings, utils
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import AppCreate, AppEmbeddingFields, AppUpdate

openai_service = OpenAIService(config.OPENAI_API_KEY)


@click.command()
@click.option(
    "--app-file",
    "app_file",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to the app JSON file",
)
@click.option(
    "--secrets-file",
    "secrets_file",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    show_default=True,
    help="Path to the secrets JSON file",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="Provide this flag to run the command and apply changes to the database",
)
def upsert_app(app_file: Path, secrets_file: Path | None, skip_dry_run: bool) -> UUID:
    """
    Insert or update an App in the DB from a JSON file, optionally injecting secrets.
    If an app with the given name already exists, performs an update; otherwise, creates a new app.
    """
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        return upsert_app_helper(db_session, app_file, secrets_file, skip_dry_run)


def upsert_app_helper(
    db_session: Session, app_file: Path, secrets_file: Path | None, skip_dry_run: bool
) -> UUID:
    # Load secrets if provided
    secrets = {}
    if secrets_file:
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
    # Render the template in-memory and load JSON data
    rendered_content = _render_template_to_string(app_file, secrets)
    app_data: dict = json.loads(rendered_content)
    click.echo(create_headline("Provided App Data"))
    click.echo(app_data)

    # Ensure mandatory 'name' field exists
    app_name: str | None = app_data.get("name")
    if not app_name:
        raise click.ClickException("Missing 'name' in app file.")

    # NOTE: We set public_only and active_only to False here so that we can find the app regardless.
    existing_app = crud.apps.get_app(db_session, app_name, public_only=False, active_only=False)
    if existing_app is None:
        return create_app_helper(db_session, app_data, skip_dry_run)
    else:
        return update_app_helper(db_session, existing_app, app_data, skip_dry_run)


def create_app_helper(db_session: Session, app_data: dict, skip_dry_run: bool) -> UUID:
    """
    Create a new app in the database.
    Validates the input against AppCreate and generates app embeddings.
    """
    # Validate and parse the app data against AppCreate schema
    app_create = AppCreate.model_validate(app_data)
    # Generate app embedding using the fields defined in AppEmbeddingFields
    app_embedding = embeddings.generate_app_embedding(
        AppEmbeddingFields.model_validate(app_data),
        openai_service,
        config.OPENAI_EMBEDDING_MODEL,
        config.OPENAI_EMBEDDING_DIMENSION,
    )

    # Create the app entry in the database
    app = crud.apps.create_app(db_session, app_create, app_embedding)

    if not skip_dry_run:
        click.echo(create_headline(f"Will create new app '{app.name}'"))
        click.echo(app)
        click.echo(create_headline("Provide --skip-dry-run to commit changes"))
        db_session.rollback()
    else:
        click.echo(create_headline(f"Committing creation of app '{app.name}'"))
        click.echo(app)
        db_session.commit()

    return app.id  # type: ignore


def update_app_helper(
    db_session: Session, existing_app: App, app_data: dict, skip_dry_run: bool
) -> UUID:
    """
    Update an existing app in the database.
    If fields used for generating embeddings (name, display_name, provider, description, categories) are changed,
    re-generates the app embedding.
    """
    # Validate and parse the app data against AppUpdate schema
    app_update = AppUpdate.model_validate(app_data)
    update_fields = app_update.model_dump(exclude_unset=True)

    # Determine if any fields affecting the embedding have changed
    embedding_fields = AppEmbeddingFields.model_fields.keys()
    recalc_embedding = False
    diffs = []

    for field, new_val in update_fields.items():
        old_val = getattr(existing_app, field, None)
        if new_val != old_val:
            diffs.append(f"{field}: {old_val} -> {new_val}")
            if field in embedding_fields:
                recalc_embedding = True

    if recalc_embedding:
        diffs.append("embedding: will be updated")

    # Re-generate embedding if necessary
    new_embedding = None
    if recalc_embedding:
        # Merge existing embedding fields with any updated values
        embedding_data = {}
        for field in embedding_fields:
            embedding_data[field] = update_fields.get(field, getattr(existing_app, field))
        new_embedding = embeddings.generate_app_embedding(
            AppEmbeddingFields.model_validate(embedding_data),
            openai_service,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )

    # Update the app in the database with the new fields and optional embedding update
    updated_app = crud.apps.update_app(db_session, existing_app, app_update, new_embedding)

    if not skip_dry_run:
        if diffs:
            click.echo(
                create_headline(
                    f"Will update app '{existing_app.name}' with the following changes:"
                )
            )
            for diff in diffs:
                click.echo(diff)
            click.echo(create_headline("Provide --skip-dry-run to commit changes"))
        else:
            click.echo(create_headline(f"No changes to app '{existing_app.name}'"))
        db_session.rollback()
    else:
        click.echo(create_headline(f"Committing update of app '{existing_app.name}'"))
        click.echo(updated_app)
        db_session.commit()

    return updated_app.id  # type: ignore


def _render_template_to_string(template_path: Path, secrets: dict[str, str]) -> str:
    """
    Render a Jinja2 template with the provided secrets and return as string.
    """
    env = Environment(
        loader=FileSystemLoader(template_path.parent),
        undefined=StrictUndefined,  # Raise error if any placeholders are missing
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template: Template = env.get_template(template_path.name)
    rendered_content: str = template.render(secrets)
    return rendered_content
