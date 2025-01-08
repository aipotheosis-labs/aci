"""
A convenience command to create a test api key for local development.
This will:
- create a new dummy user
- create a new dummy project with the new user as the owner
- create a new dummy agent in the project
"""

import uuid

import click

from aipolabs.cli import config
from aipolabs.cli.commands import create_agent, create_project, create_user
from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import APIKey
from aipolabs.common.enums import SubscriptionPlan, Visibility
from aipolabs.common.logging import create_headline


@click.option(
    "--visibility-access",
    "visibility_access",
    required=True,
    type=Visibility,
    help="visibility access of the project that the api key belongs to, either 'public' or 'private'",
)
@click.command()
def create_random_api_key(visibility_access: Visibility) -> str:
    """Create a random test api key for local development."""
    return create_random_api_key_helper(visibility_access)


def create_random_api_key_helper(visibility_access: Visibility) -> str:
    # can not do dry run because of the dependencies
    skip_dry_run = True

    random_id = str(uuid.uuid4())[:8]  # Get first 8 chars of UUID

    user_id = create_user.create_user_helper(
        auth_provider="google",
        auth_user_id=random_id,
        name=f"Test User {random_id}",
        email=f"test_{random_id}@example.com",
        profile_picture=f"https://example.com/profile_{random_id}.png",
        plan=SubscriptionPlan.FREE,
        skip_dry_run=skip_dry_run,
    )
    project_id = create_project.create_project_helper(
        name=f"Test Project {random_id}",
        owner_id=user_id,
        visibility_access=visibility_access,
        skip_dry_run=skip_dry_run,
    )
    agent_id = create_agent.create_agent_helper(
        project_id=project_id,
        name=f"Test Agent {random_id}",
        description=f"Test Agent {random_id}",
        excluded_apps=[],
        excluded_functions=[],
        skip_dry_run=skip_dry_run,
    )

    # get the api key by agent id
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        db_api_key: APIKey | None = crud.projects.get_api_key_by_agent_id(db_session, agent_id)
        if not db_api_key:
            raise ValueError(f"API key with agent ID {agent_id} not found")
        api_key: str = db_api_key.key
        click.echo(create_headline("created test API key"))
        # print user, project, agent, api key
        click.echo(f"User id: {user_id}")
        click.echo(f"Project id: {project_id}")
        click.echo(f"Agent id: {agent_id}")
        click.echo(f"API Key: {api_key}")

    return api_key
