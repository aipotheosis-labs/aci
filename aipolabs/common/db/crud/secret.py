"""
CRUD operations for secrets.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import Secret
from aipolabs.common.logging_setup import get_logger

logger = get_logger(__name__)


def create_secret(
    db_session: Session,
    linked_account_id: UUID,
    name: str,
    value: bytes,
) -> Secret:
    """
    Create a new secret.
    """
    logger.debug(f"Creating secret: {name} for linked account: {linked_account_id}")

    secret = Secret(
        linked_account_id=linked_account_id,
        name=name,
        value=value,
    )

    db_session.add(secret)
    db_session.flush()

    return secret


def get_secret(db_session: Session, linked_account_id: UUID, name: str) -> Secret | None:
    """
    Get a secret by linked_account_id and name.
    """

    stmt = select(Secret).where(
        Secret.linked_account_id == linked_account_id,
        Secret.name == name,
    )

    return db_session.execute(stmt).scalar_one_or_none()


def list_secrets(db_session: Session, linked_account_id: UUID) -> list[Secret]:
    """
    List all secrets for a linked account.
    """
    logger.debug(f"Listing secrets for linked account: {linked_account_id}")

    stmt = select(Secret).where(Secret.linked_account_id == linked_account_id)
    secrets = db_session.execute(stmt).scalars().all()

    return list(secrets)


def update_secret(
    db_session: Session,
    linked_account_id: UUID,
    name: str,
    value: bytes,
) -> Secret:
    """
    Update a secret's value.
    """
    logger.debug(f"Updating secret: {name} for linked account: {linked_account_id}")

    secret = get_secret(db_session, linked_account_id, name)
    if not secret:
        raise KeyError(f"No secret found for name '{name}'")

    secret.value = value

    db_session.flush()

    return secret


def delete_secret(db_session: Session, linked_account_id: UUID, name: str) -> None:
    """
    Delete a secret by linked_account_id and name.
    """
    logger.debug(f"Deleting secret: {name} for linked account: {linked_account_id}")

    secret = get_secret(db_session, linked_account_id, name)
    if not secret:
        raise KeyError(f"No secret found for name '{name}'")

    db_session.delete(secret)
    db_session.flush()
