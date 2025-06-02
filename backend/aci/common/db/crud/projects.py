"""
CRUD operations for projects, including direct entities under a project such as agents and API keys.
TODO: function todelete project and all related data (app_configurations, agents, api_keys, etc.)
"""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from aci.common import encryption
from aci.common.db.sql_models import Agent, APIKey, Project
from aci.common.enums import APIKeyStatus, Visibility
from aci.common.logging_setup import get_logger
from aci.common.schemas.agent import AgentUpdate, ValidInstruction
from aci.common.schemas.project import ProjectUpdate

logger = get_logger(__name__)


def create_project(
    db_session: Session,
    org_id: UUID,
    name: str,
    visibility_access: Visibility = Visibility.PUBLIC,
) -> Project:
    project = Project(
        org_id=org_id,
        name=name,
        visibility_access=visibility_access,
    )
    db_session.add(project)
    db_session.flush()
    db_session.refresh(project)
    return project


def project_exists(db_session: Session, project_id: UUID) -> bool:
    return (
        db_session.execute(select(Project).filter_by(id=project_id)).scalar_one_or_none()
        is not None
    )


def get_project(db_session: Session, project_id: UUID) -> Project | None:
    """
    Get a project by primary key.
    """
    project: Project | None = db_session.execute(
        select(Project).filter_by(id=project_id)
    ).scalar_one_or_none()
    return project


def get_projects_by_org(db_session: Session, org_id: UUID) -> list[Project]:
    projects = list(db_session.execute(select(Project).filter_by(org_id=org_id)).scalars().all())
    return projects


def get_project_by_api_key_id(db_session: Session, api_key_id: UUID) -> Project | None:
    # api key id -> agent id -> project id
    project: Project | None = db_session.execute(
        select(Project)
        .join(Agent, Project.id == Agent.project_id)
        .join(APIKey, Agent.id == APIKey.agent_id)
        .filter(APIKey.id == api_key_id)
    ).scalar_one_or_none()

    return project


def delete_project(db_session: Session, project_id: UUID) -> None:
    # Get the project to delete
    project = get_project(db_session, project_id)

    if not project:
        return

    # Delete the project which will cascade delete all related records
    db_session.delete(project)
    db_session.flush()


def set_project_visibility_access(
    db_session: Session, project_id: UUID, visibility_access: Visibility
) -> None:
    statement = update(Project).filter_by(id=project_id).values(visibility_access=visibility_access)
    db_session.execute(statement)


# TODO: TBD by business model
def increase_project_quota_usage(db_session: Session, project: Project) -> None:
    now: datetime = datetime.now(UTC)
    need_reset = now >= project.daily_quota_reset_at.replace(tzinfo=UTC) + timedelta(days=1)

    if need_reset:
        # Reset the daily quota
        statement = (
            update(Project)
            .where(Project.id == project.id)
            .values(
                {
                    Project.daily_quota_used: 1,
                    Project.daily_quota_reset_at: now,
                    Project.total_quota_used: project.total_quota_used + 1,
                }
            )
        )
    else:
        # Increment the daily quota
        statement = (
            update(Project)
            .where(Project.id == project.id)
            .values(
                {
                    Project.daily_quota_used: project.daily_quota_used + 1,
                    Project.total_quota_used: project.total_quota_used + 1,
                }
            )
        )

    db_session.execute(statement)


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


def get_request_context_by_api_key(
    db_session: Session, key: str
) -> tuple[UUID | None, UUID | None, UUID | None, UUID | None]:
    """
    Get project_id, agent_id, api_key_id, and org_id in a single query given an API key string.
    Returns a tuple of (api_key_id, agent_id, project_id, org_id) - any of which can be None if not found.
    """
    key_hmac = encryption.hmac_sha256(key)

    result = db_session.execute(
        select(APIKey.id, Agent.id, Project.id, Project.org_id)
        .join(Agent, APIKey.agent_id == Agent.id, isouter=True)
        .join(Project, Agent.project_id == Project.id, isouter=True)
        .filter(APIKey.key_hmac == key_hmac)
    ).first()

    if not result:
        return None, None, None, None

    api_key_id, agent_id, project_id, org_id = result
    return api_key_id, agent_id, project_id, org_id


def get_all_api_key_ids_for_project(db_session: Session, project_id: UUID) -> list[UUID]:
    agents = get_agents_by_project(db_session, project_id)
    project_api_key_ids = []
    for agent in agents:
        api_key = get_api_key_by_agent_id(db_session, agent.id)
        if api_key:
            project_api_key_ids.append(api_key.id)

    return project_api_key_ids


def update_project(
    db_session: Session,
    project: Project,
    update: ProjectUpdate,
) -> Project:
    """
    Update Project record
    """
    if update.name is not None:
        project.name = update.name

    db_session.flush()
    db_session.refresh(project)

    return project
