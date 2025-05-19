"""
Quota and resource limitation control.

This module contains functions for enforcing various resource limits and quotas
across the platform, such as maximum projects per user, API rate limits, storage
quotas, and other resource constraints.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.exceptions import (
    MaxAgentsReached,
    MaxProjectsReached,
    MaxUniqueLinkedAccountOwnerIdsReached,
    SubscriptionPlanNotFound,
)
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


def enforce_linked_accounts_creation_quota(
    db_session: Session, org_id: UUID, linked_account_owner_id: str
) -> None:
    """
    Check and enforce that the organization doesn't have a unique_account_owner_id exceeding the
    quota determined by the organization's current subscription plan.

    Args:
        db_session: Database session
        org_id: ID of the organization to check
        linked_account_owner_id: ID of the linked account owner to check

    Raises:
        MaxUniqueLinkedAccountOwnerIdsReached: If the organization has reached its maximum
        allowed unique linked account owner ids
        SubscriptionPlanNotFound: If the organization's subscription plan cannot be found
    """
    if crud.linked_accounts.linked_account_owner_id_exists_in_org(
        db_session, org_id, linked_account_owner_id
    ):
        # If the linked account owner id already exists in the organization, linking this account
        # will not increase the total number of unique linked account owner ids or exceed the quota.
        return

    # Get the organization's subscription
    subscription = crud.subscriptions.get_subscription_by_org_id(db_session, org_id)
    if not subscription:
        # If no subscription found, use the free plan
        plan = crud.plans.get_by_name(db_session, "free")
        if not plan:
            raise SubscriptionPlanNotFound("Free plan not found")
    else:
        # Get the plan from the subscription
        plan = crud.plans.get_by_id(db_session, subscription.plan_id)
        if not plan:
            raise SubscriptionPlanNotFound(f"Plan {subscription.plan_id} not found")

    # Get the linked accounts quota from the plan's features
    max_unique_linked_account_owner_ids = plan.features.get("linked_accounts", 0)

    num_unique_linked_account_owner_ids = (
        crud.linked_accounts.get_total_number_of_unique_linked_account_owner_ids(db_session, org_id)
    )

    if num_unique_linked_account_owner_ids >= max_unique_linked_account_owner_ids:
        logger.error(
            "organization has reached maximum unique linked account owner ids quota for the current plan",
            extra={
                "org_id": org_id,
                "max_unique_linked_account_owner_ids": max_unique_linked_account_owner_ids,
                "num_unique_linked_account_owner_ids": num_unique_linked_account_owner_ids,
                "plan": plan.name,
            },
        )
        raise MaxUniqueLinkedAccountOwnerIdsReached()
