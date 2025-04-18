"""
Quota and resource limitation control.

This module contains functions for enforcing various resource limits and quotas
across the platform, such as maximum projects per user, API rate limits, storage
quotas, and other resource constraints.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.exceptions import MaxAgentsReached, MaxProjectsReached
from aci.common.logging_setup import get_logger
from aci.server import config

logger = get_logger(__name__)


def enforce_project_creation_quota(db_session: Session, org_id: UUID) -> None:
    """
    Check and enforce that the user/organization hasn't exceeded their project creation quota.

    Args:
        db_session: Database session
        user_id: ID of the user to check

    Raises:
        MaxProjectsReached: If the user has reached their maximum allowed projects
    """
    projects = crud.projects.get_projects_by_org(db_session, org_id)
    if len(projects) >= config.MAX_PROJECTS_PER_ORG:
        logger.error(
            "user/organization has reached maximum projects quota",
            extra={
                "org_id": org_id,
                "max_projects": config.MAX_PROJECTS_PER_ORG,
                "num_projects": len(projects),
            },
        )
        raise MaxProjectsReached()


def enforce_agent_creation_quota(db_session: Session, project_id: UUID) -> None:
    """
    Check and enforce that the project hasn't exceeded its agent creation quota.

    Args:
        db_session: Database session
        project_id: ID of the project to check

    Raises:
        MaxAgentsReached: If the project has reached its maximum allowed agents
    """
    agents = crud.projects.get_agents_by_project(db_session, project_id)
    if len(agents) >= config.MAX_AGENTS_PER_PROJECT:
        logger.error(
            "project has reached maximum agents quota",
            extra={
                "project_id": project_id,
                "max_agents": config.MAX_AGENTS_PER_PROJECT,
                "num_agents": len(agents),
            },
        )
        raise MaxAgentsReached()
