"""
Quota and resource limitation control.

This module contains functions for enforcing various resource limits and quotas
across the platform, such as maximum projects per user, API rate limits, storage
quotas, and other resource constraints.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.exceptions import MaxProjectsReached
from aipolabs.common.logging import get_logger
from aipolabs.server import config

logger = get_logger(__name__)


def check_project_limit(db_session: Session, owner_id: UUID) -> None:
    """
    Check and enforce that the user/organization hasn't exceeded their project creation limit.

    Args:
        db_session: Database session
        user_id: ID of the user to check

    Raises:
        MaxProjectsReached: If the user has reached their maximum allowed projects
    # TODO: check for organization as well once we have organization support
    """
    projects = crud.projects.get_projects_by_owner(db_session, owner_id)
    if len(projects) >= config.MAX_PROJECTS_PER_USER:
        logger.error(
            "user/organization has reached maximum projects limit",
            extra={
                "owner_id": owner_id,
                "max_projects": config.MAX_PROJECTS_PER_USER,
                "num_projects": len(projects),
            },
        )
        raise MaxProjectsReached()
