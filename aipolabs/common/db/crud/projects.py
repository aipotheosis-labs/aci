"""
CRUD operations for projects, including direct entities under a project such as agents and API keys.
TODO: function todelete project and all related data (app_configurations, agents, api_keys, etc.)
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import Agent, APIKey, Project
from aipolabs.common.enums import APIKeyStatus, Visibility


def create_project(
    db_session: Session,
    owner_id: UUID,
    name: str,
    visibility_access: Visibility = Visibility.PUBLIC,
) -> Project:
    db_project = Project(
        owner_id=owner_id,
        name=name,
        visibility_access=visibility_access,
    )
    db_session.add(db_project)

    return db_project


def get_project(db_session: Session, project_id: UUID) -> Project | None:
    db_project: Project | None = db_session.execute(
        select(Project).filter_by(id=project_id)
    ).scalar_one_or_none()
    return db_project


# TODO: scalar_one() vs scalar_one_or_none() for consistency. Relevant for all get ops like
# set_project_visibility_access: when and where to check if the project exists?
def get_project_by_api_key_id(db_session: Session, api_key_id: UUID) -> Project:
    # api key id -> agent id -> project id
    db_project: Project = db_session.execute(
        select(Project)
        .join(Agent, Project.id == Agent.project_id)
        .join(APIKey, Agent.id == APIKey.agent_id)
        .filter(APIKey.id == api_key_id)
    ).scalar_one()

    return db_project


def set_project_visibility_access(
    db_session: Session, project_id: UUID, visibility_access: Visibility
) -> None:
    statement = update(Project).filter_by(id=project_id).values(visibility_access=visibility_access)
    db_session.execute(statement)


# TODO: TBD by business model
def increase_project_quota_usage(db_session: Session, project: Project) -> None:
    now: datetime = datetime.now(timezone.utc)
    need_reset = now >= project.daily_quota_reset_at.replace(tzinfo=timezone.utc) + timedelta(
        days=1
    )

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
    excluded_apps: list[UUID],
    excluded_functions: list[UUID],
) -> Agent:
    """
    Create a new agent under a project, and create a new API key for the agent.
    """
    # Create the agent
    db_agent = Agent(
        project_id=project_id,
        name=name,
        description=description,
        excluded_apps=excluded_apps,
        excluded_functions=excluded_functions,
    )
    db_session.add(db_agent)

    # Create the API key for the agent
    api_key = APIKey(key=secrets.token_hex(32), agent_id=db_agent.id, status=APIKeyStatus.ACTIVE)
    db_session.add(api_key)

    return db_agent


def get_agent_by_id(db_session: Session, agent_id: UUID) -> Agent | None:
    db_agent: Agent | None = db_session.execute(
        select(Agent).filter_by(id=agent_id)
    ).scalar_one_or_none()

    return db_agent


def get_api_key_by_agent_id(db_session: Session, agent_id: UUID) -> APIKey | None:
    db_api_key: APIKey | None = db_session.execute(
        select(APIKey).filter_by(agent_id=agent_id)
    ).scalar_one_or_none()

    return db_api_key


def get_api_key(db_session: Session, key: str) -> APIKey | None:
    db_api_key: APIKey | None = db_session.execute(
        select(APIKey).filter_by(key=key)
    ).scalar_one_or_none()

    return db_api_key
