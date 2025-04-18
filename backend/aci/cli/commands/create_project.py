from uuid import UUID

import click
from rich.console import Console

from aci.cli import config
from aci.common import utils
from aci.common.db import crud
from aci.common.enums import Visibility

console = Console()


@click.command()
@click.option(
    "--name",
    "name",
    required=True,
    help="project name",
)
@click.option(
    "--org-id",
    "org_id",
    required=True,
    type=UUID,
    help="organization id",
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
    org_id: UUID,
    visibility_access: Visibility,
    skip_dry_run: bool,
) -> UUID:
    """
    Create a project in db.
    Note this is a privileged command, as it can create projects under any user or organization.
    """
    return create_project_helper(name, org_id, visibility_access, skip_dry_run)


def create_project_helper(
    name: str,
    org_id: UUID,
    visibility_access: Visibility,
    skip_dry_run: bool,
) -> UUID:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        project = crud.projects.create_project(db_session, org_id, name, visibility_access)
        if not skip_dry_run:
            console.rule(
                f"[bold green]Provide --skip-dry-run to Create Project: {project.name}[/bold green]"
            )
            db_session.rollback()
        else:
            db_session.commit()
            console.rule(f"[bold green]Project created: {project.name}[/bold green]")

        console.print(project)

        return project.id
