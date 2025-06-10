"""
A convenience command to create a test api key for local development.
This will:
- create a new dummy user
- create a new dummy project with the new user as the owner
- create a new dummy agent in the project
"""

import uuid

import click
from rich.console import Console

from aci.cli import config
from aci.cli.commands import create_agent, create_project
from aci.common import utils
from aci.common.db import crud
from aci.common.db.sql_models import APIKey
from aci.common.enums import Visibility

console = Console()


@click.option(
    "--visibility-access",
    "visibility_access",
    required=True,
    type=Visibility,
    help="visibility access of the project that the api key belongs to, either 'public' or 'private'",
)
@click.option(
    "--org-id",
    "org_id",
    required=False,
    type=uuid.UUID,
    help="organization id",
)
@click.command()
def create_random_api_key(visibility_access: Visibility, org_id: uuid.UUID | None) -> str:
    """Create a random test api key for local development."""
    return create_random_api_key_helper(visibility_access, org_id)


def create_random_api_key_helper(visibility_access: Visibility, org_id: uuid.UUID | None) -> str:
    # can not do dry run because of the dependencies
    skip_dry_run = True

    random_id = str(uuid.uuid4())[:8]  # Get first 8 chars of UUID

    project_id = create_project.create_project_helper(
        name=f"Test Project {random_id}",
        org_id=org_id or uuid.uuid4(),
        visibility_access=visibility_access,
        skip_dry_run=skip_dry_run,
    )

    agent_id = create_agent.create_agent_helper(
        project_id=project_id,
        name=f"Test Agent {random_id}",
        description="This agent is created by the create-random-api-key CLI command",
        allowed_apps=[],
        custom_instructions={},
        skip_dry_run=skip_dry_run,
    )

    # get the api key by agent id
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        api_key: APIKey | None = crud.projects.get_api_key_by_agent_id(db_session, agent_id)
        if not api_key:
            raise ValueError(f"API key with agent ID {agent_id} not found")

        console.rule("[bold green]Summary[/bold green]")

        console.print(
            {
                "Project Id": str(project_id),
                "Agent Id": str(agent_id),
                "API Key": str(api_key.key),
            }
        )

    return str(api_key.key)
