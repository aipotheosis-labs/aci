import json
from uuid import UUID

import click

from aipolabs.cli import config
from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.exceptions import AgentNotFound, ProjectNotFound
from aipolabs.common.logging import create_headline
from aipolabs.common.schemas.agent import AgentUpdate


# TODO: Make an upsert update agent command so you can use json files to update the agent
@click.command()
@click.option(
    "--project-id",
    "project_id",
    required=True,
    type=UUID,
    help="project id under which the agent exists",
)
@click.option("--agent-id", "agent_id", required=True, type=UUID, help="id of the agent to update")
@click.option(
    "--name",
    "name",
    required=False,
    help="new agent name",
)
@click.option(
    "--description",
    "description",
    required=False,
    help="new agent description",
)
@click.option(
    "--excluded-apps",
    "excluded_apps",
    required=False,
    type=list[str],
    help="new list of app names to exclude from the agent",
)
@click.option(
    "--excluded-functions",
    "excluded_functions",
    required=False,
    type=list[str],
    help="new list of function names to exclude from the agent",
)
@click.option(
    "--custom-instructions",
    "custom_instructions",
    required=False,
    type=str,
    help="new custom instructions for the agent",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="provide this flag to run the command and apply changes to the database",
)
def update_agent(
    project_id: UUID,
    agent_id: UUID,
    name: str | None,
    description: str | None,
    excluded_apps: list[str] | None,
    excluded_functions: list[str] | None,
    custom_instructions: str | None,
    skip_dry_run: bool,
) -> UUID:
    """
    Update an existing agent in db.
    """
    return update_agent_helper(
        project_id,
        agent_id,
        name,
        description,
        excluded_apps,
        excluded_functions,
        custom_instructions,
        skip_dry_run,
    )


def update_agent_helper(
    project_id: UUID,
    agent_id: UUID,
    name: str | None,
    description: str | None,
    excluded_apps: list[str] | None,
    excluded_functions: list[str] | None,
    custom_instructions: str | None,
    skip_dry_run: bool,
) -> UUID:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        agent = crud.projects.get_agent_by_id(db_session, agent_id)
        if not agent:
            raise AgentNotFound(f"agent={agent_id} not found in project={project_id}")

        project = crud.projects.get_project(db_session, project_id)
        if not project:
            raise ProjectNotFound(f"project={project_id} not found")

        if agent.project_id != project_id:
            raise AgentNotFound(f"agent={agent_id} not found in project={project_id}")

        if custom_instructions:
            custom_instructions = json.loads(custom_instructions)

        update = AgentUpdate(
            name=name,
            description=description,
            excluded_apps=excluded_apps,
            excluded_functions=excluded_functions,
            custom_instructions=custom_instructions,
        )

        updated_agent = crud.projects.update_agent(db_session, agent, update)

        if not skip_dry_run:
            click.echo(create_headline(f"will update agent {updated_agent.name}"))
            click.echo(updated_agent)
            click.echo(create_headline("provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"committing update of agent {updated_agent.name}"))
            click.echo(updated_agent)
            db_session.commit()

        return updated_agent.id  # type: ignore
