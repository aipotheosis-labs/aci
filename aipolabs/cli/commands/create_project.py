from uuid import UUID

import click

from aipolabs.cli import config
from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.enums import Visibility
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService

openai_service = OpenAIService(config.OPENAI_API_KEY)


@click.command()
@click.option(
    "--name",
    "name",
    required=True,
    help="project name",
)
@click.option(
    "--owner-id",
    "owner_id",
    required=True,
    type=UUID,
    help="owner id, either user id or organization id",
)
@click.option(
    "--visibility-access",
    "visibility_access",
    required=True,
    type=Visibility,
    help="visibility access of the project, if 'public', the project can only access public apps and functions",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="provide this flag to run the command and apply changes to the database",
)
def create_project(
    name: str,
    owner_id: UUID,
    visibility_access: Visibility,
    skip_dry_run: bool,
) -> UUID:
    """
    Create a project in db.
    Note this is a privileged command, as it can create projects under any user or organization.
    """
    return create_project_helper(name, owner_id, visibility_access, skip_dry_run)


def create_project_helper(
    name: str,
    owner_id: UUID,
    visibility_access: Visibility,
    skip_dry_run: bool,
) -> UUID:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:

        project = crud.projects.create_project(db_session, owner_id, name, visibility_access)
        if not skip_dry_run:
            click.echo(create_headline(f"will create new project {project.name}"))
            click.echo(project)
            click.echo(create_headline("provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"committing creation of project {project.name}"))
            click.echo(project)
            db_session.commit()
        return project.id  # type: ignore
