import json
from uuid import UUID

import click
from rich.console import Console

from aci.cli import config
from aci.common import utils
from aci.common.db import crud
from aci.common.exceptions import AgentNotFound
from aci.common.schemas.agent import AgentUpdate

console = Console()


# TODO: Make an upsert update agent command so you can use json files to update the agent
@click.command()
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
    "--allowed-apps",
    "allowed_apps",
    required=False,
    help="comma-separated list of app names to allow the agent to access (e.g., 'app1,app2,app3')",
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
    agent_id: UUID,
    name: str | None,
    description: str | None,
    allowed_apps: str | None,
    custom_instructions: str | None,
    skip_dry_run: bool,
) -> UUID:
    """
    Update an existing agent in db.
    """
    list_of_allowed_apps = (
        [app.strip() for app in allowed_apps.split(",")] if allowed_apps is not None else None
    )

    return update_agent_helper(
        agent_id,
        name,
        description,
        list_of_allowed_apps,
        json.loads(custom_instructions) if custom_instructions else None,
        skip_dry_run,
    )


def update_agent_helper(
    agent_id: UUID,
    name: str | None,
    description: str | None,
    allowed_apps: list[str] | None,
    custom_instructions: dict[str, str] | None,
    skip_dry_run: bool,
) -> UUID:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        agent = crud.projects.get_agent_by_id(db_session, agent_id)
        if not agent:
            raise AgentNotFound(f"agent={agent_id} not found.")

        update = AgentUpdate(
            name=name,
            description=description,
            allowed_apps=allowed_apps,
            custom_instructions=custom_instructions,
        )

        updated_agent = crud.projects.update_agent(db_session, agent, update)

        if not skip_dry_run:
            console.rule(
                f"[bold green]Provide --skip-dry-run to Update Agent: {updated_agent.name}[/bold green]"
            )
            db_session.rollback()
        else:
            db_session.commit()
            console.rule(f"[bold green]Updated Agent: {updated_agent.name}[/bold green]")

        console.print(updated_agent)

        return updated_agent.id
