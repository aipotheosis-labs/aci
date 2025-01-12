from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.logging import get_logger

logger = get_logger(__name__)


def get_linked_accounts(
    db_session: Session, project_id: UUID, app_id: UUID | None, linked_account_owner_id: str | None
) -> list[LinkedAccount]:
    """Get all linked accounts under a project, with optional filters"""
    statement = select(LinkedAccount).filter_by(project_id=project_id)
    if app_id:
        statement = statement.filter(LinkedAccount.app_id == app_id)
    if linked_account_owner_id:
        statement = statement.filter(
            LinkedAccount.linked_account_owner_id == linked_account_owner_id
        )

    linked_accounts: list[LinkedAccount] = db_session.execute(statement).scalars().all()
    return linked_accounts


def get_linked_account(
    db_session: Session, project_id: UUID, app_id: UUID, linked_account_owner_id: str
) -> LinkedAccount | None:
    statement = select(LinkedAccount).filter_by(
        project_id=project_id, app_id=app_id, linked_account_owner_id=linked_account_owner_id
    )
    linked_account: LinkedAccount | None = db_session.execute(statement).scalar_one_or_none()

    return linked_account


def get_linked_account_by_id(
    db_session: Session, linked_account_id: UUID, project_id: UUID
) -> LinkedAccount | None:
    """Get a linked account by its id, with optional project filter
    - linked_account_id uniquely identifies a linked account across the platform.
    - project_id is extra precaution useful for access control, the linked account must belong to the project.
    """
    statement = select(LinkedAccount).filter_by(id=linked_account_id, project_id=project_id)
    linked_account: LinkedAccount | None = db_session.execute(statement).scalar_one_or_none()
    return linked_account


def delete_linked_account(db_session: Session, linked_account: LinkedAccount) -> None:
    db_session.delete(linked_account)
    db_session.flush()


def create_linked_account(
    db_session: Session,
    project_id: UUID,
    app_id: UUID,
    linked_account_owner_id: str,
    security_scheme: SecurityScheme,
    security_credentials: dict,
    enabled: bool = True,
) -> LinkedAccount:
    linked_account = LinkedAccount(
        project_id=project_id,
        app_id=app_id,
        linked_account_owner_id=linked_account_owner_id,
        security_scheme=security_scheme,
        security_credentials=security_credentials,
        enabled=enabled,
    )
    db_session.add(linked_account)
    db_session.flush()
    db_session.refresh(linked_account)
    return linked_account


def update_linked_account(
    db_session: Session,
    linked_account: LinkedAccount,
    security_scheme: SecurityScheme,
    security_credentials: dict,
) -> LinkedAccount:
    linked_account.security_scheme = security_scheme
    linked_account.security_credentials = security_credentials
    db_session.flush()
    db_session.refresh(linked_account)
    return linked_account


def delete_linked_accounts(db_session: Session, project_id: UUID, app_id: UUID) -> int:
    statement = delete(LinkedAccount).filter_by(project_id=project_id, app_id=app_id)
    result = db_session.execute(statement)

    db_session.flush()
    return int(result.rowcount)
