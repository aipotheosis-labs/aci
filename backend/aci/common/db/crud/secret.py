from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from aci.common.db.sql_models import LinkedAccount, Project, Secret
from aci.common.logging_setup import get_logger
from aci.common.schemas.secret import SecretCreate, SecretUpdate

logger = get_logger(__name__)


def create_secret(
    db_session: Session,
    linked_account_id: UUID,
    secret_create: SecretCreate,
) -> Secret:
    """
    Create a new secret.
    """
    secret = Secret(
        linked_account_id=linked_account_id,
        key=secret_create.key,
        value=secret_create.value,
    )
    db_session.add(secret)
    db_session.flush()
    db_session.refresh(secret)

    return secret


def get_secret(db_session: Session, linked_account_id: UUID, key: str) -> Secret | None:
    """
    Get a secret by linked_account_id and key.
    """
    statement = select(Secret).filter_by(linked_account_id=linked_account_id, key=key)
    return db_session.execute(statement).scalar_one_or_none()


def list_secrets(db_session: Session, linked_account_id: UUID) -> list[Secret]:
    """
    List all secrets for a linked account.
    """
    statement = select(Secret).filter_by(linked_account_id=linked_account_id)
    secrets = db_session.execute(statement).scalars().all()

    return list(secrets)


def update_secret(
    db_session: Session,
    secret: Secret,
    update: SecretUpdate,
) -> Secret:
    """
    Update a secret's value.
    """
    secret.value = update.value
    db_session.flush()
    db_session.refresh(secret)
    return secret


def delete_secret(db_session: Session, secret: Secret) -> None:
    """
    Delete a secret.
    """
    db_session.delete(secret)
    db_session.flush()


def get_total_number_of_secrets_in_org(db_session: Session, org_id: UUID) -> int:
    """
    Get the total number of secrets for an organization.
    Secrets are stored per linked account, and linked accounts belong to projects in the organization.

    Args:
        db_session: Database session
        org_id: ID of the organization

    Returns:
        int: Total number of secrets across all linked accounts in all projects of the organization
    """
    statement = select(func.count(Secret.id)).where(
        Secret.linked_account_id.in_(
            select(LinkedAccount.id).where(
                LinkedAccount.project_id.in_(select(Project.id).filter(Project.org_id == org_id))
            )
        )
    )
    return db_session.execute(statement).scalar_one()
