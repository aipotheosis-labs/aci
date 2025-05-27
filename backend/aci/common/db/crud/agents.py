import secrets
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from aci.common import encryption
from aci.common.db.sql_models import Agent, APIKey
from aci.common.enums import APIKeyStatus
from aci.common.schemas.agent import AgentUpdate, ValidInstruction


def create_agent(
    db_session: Session,
    project_id: UUID,
    name: str,
    description: str,
    allowed_apps: list[str],
    custom_instructions: dict[str, ValidInstruction],
) -> Agent:
    """
    Create a new agent under a project, and create a new API key for the agent.
    """
    # Create the agent
    agent = Agent(
        project_id=project_id,
        name=name,
        description=description,
        allowed_apps=allowed_apps,
        custom_instructions=custom_instructions,
    )
    db_session.add(agent)

    key = secrets.token_hex(32)
    key_hmac = encryption.hmac_sha256(key)

    # Create the API key for the agent
    api_key = APIKey(key=key, key_hmac=key_hmac, agent_id=agent.id, status=APIKeyStatus.ACTIVE)
    db_session.add(api_key)

    db_session.flush()
    db_session.refresh(agent)

    return agent


def update_agent(
    db_session: Session,
    agent: Agent,
    update: AgentUpdate,
) -> Agent:
    """
    Update Agent record by agent id
    """

    if update.name is not None:
        agent.name = update.name
    if update.description is not None:
        agent.description = update.description
    if update.allowed_apps is not None:
        agent.allowed_apps = update.allowed_apps
    if update.custom_instructions is not None:
        agent.custom_instructions = update.custom_instructions

    db_session.flush()
    db_session.refresh(agent)

    return agent


def delete_agent(db_session: Session, agent: Agent) -> None:
    db_session.delete(agent)
    db_session.flush()


def delete_app_from_agents_allowed_apps(
    db_session: Session, project_id: UUID, app_name: str
) -> None:
    statement = (
        update(Agent)
        .where(Agent.project_id == project_id)
        .values(allowed_apps=func.array_remove(Agent.allowed_apps, app_name))
    )
    db_session.execute(statement)


def get_agents_by_project(db_session: Session, project_id: UUID) -> list[Agent]:
    return list(db_session.execute(select(Agent).filter_by(project_id=project_id)).scalars().all())


def get_agent_by_id(db_session: Session, agent_id: UUID) -> Agent | None:
    return db_session.execute(select(Agent).filter_by(id=agent_id)).scalar_one_or_none()


def get_agent_by_api_key_id(db_session: Session, api_key_id: UUID) -> Agent | None:
    return db_session.execute(
        select(Agent).join(APIKey, Agent.id == APIKey.agent_id).filter(APIKey.id == str(api_key_id))
    ).scalar_one_or_none()


def get_agents_whose_allowed_apps_contains(db_session: Session, app_name: str) -> list[Agent]:
    statement = select(Agent).where(Agent.allowed_apps.contains([app_name]))
    return list(db_session.execute(statement).scalars().all())


def get_api_key_by_agent_id(db_session: Session, agent_id: UUID) -> APIKey | None:
    return db_session.execute(select(APIKey).filter_by(agent_id=agent_id)).scalar_one_or_none()


def get_api_key(db_session: Session, key: str) -> APIKey | None:
    key_hmac = encryption.hmac_sha256(key)
    return db_session.execute(select(APIKey).filter_by(key_hmac=key_hmac)).scalar_one_or_none()
