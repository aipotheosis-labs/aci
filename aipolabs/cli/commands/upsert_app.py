import json
from pathlib import Path
from uuid import UUID

import click
from deepdiff import DeepDiff
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from openai import OpenAI
from sqlalchemy.orm import Session

from aipolabs.cli import config
from aipolabs.common import embeddings, utils
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App
from aipolabs.common.logging_setup import create_headline
from aipolabs.common.schemas.app import AppEmbeddingFields, AppUpsert

openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


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
    For changing the app name of an existing app, use the <PLACEHOLDER> command.
    """
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        return upsert_app_helper(db_session, app_file, secrets_file, skip_dry_run)


def upsert_app_helper(
    db_session: Session, app_file: Path, secrets_file: Path | None, skip_dry_run: bool
) -> UUID:
    # Load secrets if provided
    secrets = {}
    if secrets_file:
        with open(secrets_file) as f:
            secrets = json.load(f)
    # Render the template in-memory and load JSON data
    rendered_content = _render_template_to_string(app_file, secrets)
    app_upsert = AppUpsert.model_validate(json.loads(rendered_content))

    click.echo(create_headline("Provided App Data"))
    click.echo(app_upsert.model_dump_json(indent=2))

    existing_app = crud.apps.get_app(
        db_session, app_upsert.name, public_only=False, active_only=False
    )
    if existing_app is None:
        click.echo(create_headline(f"New App '{app_upsert.name}' Found, Will Create"))
        return create_app_helper(db_session, app_upsert, skip_dry_run)
    else:
        click.echo(create_headline(f"App '{app_upsert.name}' Exists, Will Update"))
        return update_app_helper(
            db_session,
            existing_app,
            app_upsert,
            skip_dry_run,
        )


def create_app_helper(db_session: Session, app_upsert: AppUpsert, skip_dry_run: bool) -> UUID:
    # Generate app embedding using the fields defined in AppEmbeddingFields
    app_embedding = embeddings.generate_app_embedding(
        AppEmbeddingFields.model_validate(app_upsert.model_dump()),
        openai_client,
        config.OPENAI_EMBEDDING_MODEL,
        config.OPENAI_EMBEDDING_DIMENSION,
    )

    # Create the app entry in the database
    app = crud.apps.create_app(db_session, app_upsert, app_embedding)

    if not skip_dry_run:
        click.echo(create_headline(f"Will create new app '{app.name}'"))
        click.echo(app)
        click.echo(create_headline("Provide --skip-dry-run to commit changes"))
        db_session.rollback()
    else:
        click.echo(create_headline(f"Committing creation of app '{app.name}'"))
        click.echo(app)
        db_session.commit()

    return app.id


def update_app_helper(
    db_session: Session, existing_app: App, app_upsert: AppUpsert, skip_dry_run: bool
) -> UUID:
    """
    Update an existing app in the database.
    If fields used for generating embeddings (name, display_name, provider, description, categories) are changed,
    re-generates the app embedding.
    """
    existing_app_upsert = AppUpsert.model_validate(existing_app, from_attributes=True)
    if existing_app_upsert == app_upsert:
        click.echo(create_headline(f"No changes to app '{existing_app.name}'"))
        return existing_app.id

    # Determine if any fields affecting the embedding have changed
    new_embedding = None
    if _need_embedding_regeneration(existing_app_upsert, app_upsert):
        new_embedding = embeddings.generate_app_embedding(
            AppEmbeddingFields.model_validate(app_upsert.model_dump()),
            openai_client,
            config.OPENAI_EMBEDDING_MODEL,
            config.OPENAI_EMBEDDING_DIMENSION,
        )

    # Update the app in the database with the new fields and optional embedding update
    updated_app = crud.apps.update_app(db_session, existing_app, app_upsert, new_embedding)

    diff = DeepDiff(existing_app_upsert.model_dump(), app_upsert.model_dump(), ignore_order=True)
    click.echo(
        create_headline(f"Will update app '{existing_app.name}' with the following changes:")
    )
    click.echo(diff.pretty())
    if not skip_dry_run:
        click.echo(create_headline("Provide --skip-dry-run to commit changes"))
        db_session.rollback()
    else:
        click.echo(create_headline(f"Committing update of app '{existing_app.name}'"))
        db_session.commit()

    return updated_app.id


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


def _need_embedding_regeneration(old_app: AppUpsert, new_app: AppUpsert) -> bool:
    fields = set(AppEmbeddingFields.model_fields.keys())
    return bool(old_app.model_dump(include=fields) != new_app.model_dump(include=fields))
