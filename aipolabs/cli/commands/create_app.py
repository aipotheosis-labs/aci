import json
from pathlib import Path
from uuid import UUID

import click
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template

from aipolabs.cli import config
from aipolabs.common import embeddings, utils
from aipolabs.common.db import crud
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import AppCreate

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
def create_app(app_file: Path, secrets_file: Path | None, skip_dry_run: bool) -> UUID:
    """Create App in DB from a JSON file, optionally injecting secrets."""
    return create_app_helper(app_file, secrets_file, skip_dry_run)


def create_app_helper(app_file: Path, secrets_file: Path | None, skip_dry_run: bool) -> UUID:
    # Load secrets if secrets_file is provided
    secrets = {}
    if secrets_file:
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
    # Render the template in-memory
    rendered_content = _render_template_to_string(app_file, secrets)
    app_data = json.loads(rendered_content)
    print(create_headline("CREATED APP DATA"))
    print(app_data)
    app: AppCreate = AppCreate.model_validate(app_data)

    # Generate app embedding
    app_embedding = embeddings.generate_app_embedding(
        app,
        openai_service,
        config.OPENAI_EMBEDDING_MODEL,
        config.OPENAI_EMBEDDING_DIMENSION,
    )

    # Create the app in the database
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        db_app = crud.create_app(db_session, app, app_embedding)
        if not skip_dry_run:
            click.echo(create_headline(f"Will create new app '{db_app.name}'"))
            click.echo(db_app)
            click.echo(create_headline("Provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"Committing creation of app '{db_app.name}'"))
            click.echo(db_app)
            db_session.commit()

        return db_app.id  # type: ignore


def _render_template_to_string(template_path: Path, secrets: dict[str, str]) -> str:
    """Render a Jinja2 template with the provided secrets and return as string."""
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
