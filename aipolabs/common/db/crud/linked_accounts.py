from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import App, LinkedAccount
from aipolabs.common.enums import SecurityScheme
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.security_scheme import APIKeySchemeCredentials, OAuth2SchemeCredentials

logger = get_logger(__name__)


def get_linked_accounts(
    db_session: Session,
    project_id: UUID,
    app_name: str | None,
    linked_account_owner_id: str | None,
) -> list[LinkedAccount]:
    """Get all linked accounts under a project, with optional filters"""
    statement = select(LinkedAccount).filter_by(project_id=project_id)
    if app_name:
        statement = statement.join(App, LinkedAccount.app_id == App.id).filter(App.name == app_name)
    if linked_account_owner_id:
        statement = statement.filter(
            LinkedAccount.linked_account_owner_id == linked_account_owner_id
        )

    return list(db_session.execute(statement).scalars().all())


def get_linked_account(
    db_session: Session, project_id: UUID, app_name: str, linked_account_owner_id: str
) -> LinkedAccount | None:
    statement = (
        select(LinkedAccount)
        .join(App, LinkedAccount.app_id == App.id)
        .filter(
            LinkedAccount.project_id == project_id,
            App.name == app_name,
            LinkedAccount.linked_account_owner_id == linked_account_owner_id,
        )
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
    app_name: str,
    linked_account_owner_id: str,
    security_scheme: SecurityScheme,
    security_credentials: OAuth2SchemeCredentials | APIKeySchemeCredentials | None = None,
    enabled: bool = True,
) -> LinkedAccount:
    """Create a linked account
    when security_credentials is None, the linked account will be using App's default security credentials if exists
    """
    app_id = db_session.execute(select(App.id).filter_by(name=app_name)).scalar_one()
    linked_account = LinkedAccount(
        project_id=project_id,
        app_id=app_id,
        linked_account_owner_id=linked_account_owner_id,
        security_scheme=security_scheme,
        security_credentials=(
            security_credentials.model_dump(mode="json") if security_credentials else {}
        ),
        enabled=enabled,
    )
    db_session.add(linked_account)
    db_session.flush()
    db_session.refresh(linked_account)
    return linked_account


def update_linked_account_credentials(
    db_session: Session,
    linked_account: LinkedAccount,
    security_credentials: OAuth2SchemeCredentials | APIKeySchemeCredentials,
) -> LinkedAccount:
    """
    Update the security credentials of a linked account.
    Removing the security credentials (setting it to empty dict) is not handled here.
    """
    if security_credentials is not None:
        linked_account.security_credentials = security_credentials.model_dump(mode="json")

    # Technically we don't need to call the flush() and refresh() here, but it's more robust to do so
    # in case there are other dependencies on the linked account object that need to be updated in the future
    db_session.flush()
    db_session.refresh(linked_account)
    return linked_account


def delete_linked_accounts(db_session: Session, project_id: UUID, app_name: str) -> int:
    statement = (
        select(LinkedAccount)
        .join(App, LinkedAccount.app_id == App.id)
        .filter(LinkedAccount.project_id == project_id, App.name == app_name)
    )
    linked_accounts_to_delete = db_session.execute(statement).scalars().all()
    for linked_account in linked_accounts_to_delete:
        db_session.delete(linked_account)
    db_session.flush()
    return len(linked_accounts_to_delete)
