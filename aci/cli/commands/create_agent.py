import json
from uuid import UUID

import click
from rich.console import Console

from aci.cli import config
from aci.common import utils
from aci.common.db import crud

console = Console()


@click.command()
@click.option(
    "--project-id",
    "project_id",
    required=True,
    type=UUID,
    help="project id under which the agent is created",
)
@click.option(
    "--name",
    "name",
    required=True,
    help="agent name",
)
@click.option(
    "--description",
    "description",
    required=True,
    help="agent description",
)
@click.option(
    "--allowed-apps",
    "allowed_apps",
    required=False,
    default="",
    help="comma-separated list of app names to allow the agent to access (e.g., 'app1,app2,app3')",
)
@click.option(
    "--custom-instructions",
    "custom_instructions",
    required=False,
    default="{}",
    type=str,
    help="function level custom instructions for the agent",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="provide this flag to run the command and apply changes to the database",
)
def create_agent(
    project_id: UUID,
    name: str,
    description: str,
    allowed_apps: str,
    custom_instructions: str,
    skip_dry_run: bool,
) -> UUID:
    """
    Create an agent in db.
    """
    # Parse comma-separated string into list, handling empty string case
    list_of_allowed_apps = [app.strip() for app in allowed_apps.split(",")] if allowed_apps else []

    return create_agent_helper(
        project_id,
        name,
        description,
        list_of_allowed_apps,
        json.loads(custom_instructions),
        skip_dry_run,
    )


def create_agent_helper(
    project_id: UUID,
    name: str,
    description: str,
    allowed_apps: list[str],
    custom_instructions: dict[str, str],
    skip_dry_run: bool,
) -> UUID:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        agent = crud.projects.create_agent(
            db_session,
            project_id,
            name,
            description,
            allowed_apps,
            custom_instructions,
        )

        if not skip_dry_run:
            console.rule("[bold green]Provide --skip-dry-run to Create Agent[/bold green]")
            db_session.rollback()
        else:
            db_session.commit()
            console.rule(f"[bold green]Agent created: {agent.name}[/bold green]")

        console.print(agent)

        return agent.id
