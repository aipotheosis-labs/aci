from uuid import UUID

import click

from aipolabs.cli import config
from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService

openai_service = OpenAIService(config.OPENAI_API_KEY)


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
    "--excluded-apps",
    "excluded_apps",
    required=False,
    default=[],
    type=list[UUID],
    help="list of app ids to exclude from the agent",
)
@click.option(
    "--excluded-functions",
    "excluded_functions",
    required=False,
    default=[],
    type=list[UUID],
    help="list of function ids to exclude from the agent",
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
    excluded_apps: list[UUID],
    excluded_functions: list[UUID],
    custom_instructions: dict[UUID, str],
    skip_dry_run: bool,
) -> UUID:
    """
    Create an agent in db.
    """
    return create_agent_helper(
        project_id,
        name,
        description,
        excluded_apps,
        excluded_functions,
        custom_instructions,
        skip_dry_run,
    )


def create_agent_helper(
    project_id: UUID,
    name: str,
    description: str,
    excluded_apps: list[UUID],
    excluded_functions: list[UUID],
    custom_instructions: dict[UUID, str],
    skip_dry_run: bool,
) -> UUID:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:

        agent = crud.projects.create_agent(
            db_session,
            project_id,
            name,
            description,
            excluded_apps,
            excluded_functions,
            custom_instructions,
        )

        if not skip_dry_run:
            click.echo(create_headline(f"will create new agent {agent.name}"))
            click.echo(agent)
            click.echo(create_headline("provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"committing creation of agent {agent.name}"))
            click.echo(agent)
            db_session.commit()

        return agent.id  # type: ignore
