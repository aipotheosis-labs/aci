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
)
from aci.common.logging_setup import get_logger
from aci.common.schemas.quota import PlanFeatures, PlanInfo, QuotaResourceUsage, QuotaUsageResponse
from aci.server import billing, config

logger = get_logger(__name__)


def enforce_project_creation_quota(db_session: Session, org_id: UUID) -> None:
    """
    Check and enforce that the user/organization hasn't exceeded their project creation quota
    based on their subscription plan.

    Args:
        db_session: Database session
        org_id: ID of the organization to check

    Raises:
        MaxProjectsReached: If the user has reached their maximum allowed projects
        SubscriptionPlanNotFound: If the organization's subscription plan cannot be found
    """
    subscription = billing.get_subscription_by_org_id(db_session, org_id)

    # Get the projects quota from the plan's features
    max_projects = subscription.plan.features["projects"]

    projects = crud.projects.get_projects_by_org(db_session, org_id)
    if len(projects) >= max_projects:
        logger.error(
            "user/organization has reached maximum projects quota for their plan",
            extra={
                "org_id": org_id,
                "max_projects": max_projects,
                "num_projects": len(projects),
                "plan": subscription.plan.name,
            },
        )
        raise MaxProjectsReached(
            message=f"Maximum number of projects ({max_projects}) reached for the {subscription.plan.name} plan"
        )


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

    # Get the plan for the organization
    subscription = billing.get_subscription_by_org_id(db_session, org_id)

    # Get the linked accounts quota from the plan's features
    max_unique_linked_account_owner_ids = subscription.plan.features["linked_accounts"]

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
                "plan": subscription.plan.name,
            },
        )
        raise MaxUniqueLinkedAccountOwnerIdsReached(
            message=f"Maximum number of unique linked account owner ids ({max_unique_linked_account_owner_ids}) reached for the {subscription.plan.name} plan"
        )


def get_quota_usage(db_session: Session, org_id: UUID) -> QuotaUsageResponse:
    """
    Get quota usage for an organization

    Args:
        db_session: Database session
        org_id: ID of the organization

    Returns:
        QuotaUsageResponse: include all quota usage information
    """
    # get subscription and plan
    subscription = billing.get_subscription_by_org_id(db_session, org_id)
    plan = subscription.plan
    logger.info("get quota usage", extra={"org_id": org_id, "plan": plan.name})

    # get project usage
    projects = crud.projects.get_projects_by_org(db_session, org_id)
    projects_used = len(projects)
    projects_limit = plan.features["projects"]
    projects_remaining = max(0, projects_limit - projects_used)

    # get agent credentials usage (total secrets as each stores app credentials)
    agent_credentials_used = crud.secret.get_total_number_of_secrets_in_org(db_session, org_id)
    agent_credentials_limit = plan.features["agent_credentials"]
    agent_credentials_remaining = max(0, agent_credentials_limit - agent_credentials_used)

    # get linked accounts usage
    linked_accounts_used = crud.linked_accounts.get_total_number_of_unique_linked_account_owner_ids(
        db_session, org_id
    )
    linked_accounts_limit = plan.features["linked_accounts"]
    linked_accounts_remaining = max(0, linked_accounts_limit - linked_accounts_used)

    return QuotaUsageResponse(
        projects=QuotaResourceUsage(
            used=projects_used, limit=projects_limit, remaining=projects_remaining
        ),
        linked_accounts=QuotaResourceUsage(
            used=linked_accounts_used,
            limit=linked_accounts_limit,
            remaining=linked_accounts_remaining,
        ),
        agents_credentials=QuotaResourceUsage(
            used=agent_credentials_used,
            limit=agent_credentials_limit,
            remaining=agent_credentials_remaining,
        ),
        plan=PlanInfo(name=plan.name, features=PlanFeatures(**plan.features)),
    )
