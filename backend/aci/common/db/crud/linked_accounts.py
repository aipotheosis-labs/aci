from datetime import datetime
from uuid import UUID

from sqlalchemy import distinct, exists, func, select
from sqlalchemy.orm import Session

from aci.common import validators
from aci.common.db.sql_models import App, LinkedAccount, Project
from aci.common.enums import SecurityScheme
from aci.common.logging_setup import get_logger
from aci.common.schemas.linked_accounts import LinkedAccountUpdate
from aci.common.schemas.security_scheme import (
    APIKeySchemeCredentials,
    NoAuthSchemeCredentials,
    OAuth2SchemeCredentials,
)

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


def get_linked_accounts_by_app_id(db_session: Session, app_id: UUID) -> list[LinkedAccount]:
    statement = select(LinkedAccount).filter_by(app_id=app_id)
    linked_accounts: list[LinkedAccount] = list(db_session.execute(statement).scalars().all())
    return linked_accounts


# TODO: the access control (project_id check) should probably be done at the route level?
def get_linked_account_by_id_under_project(
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
    security_credentials: OAuth2SchemeCredentials
    | APIKeySchemeCredentials
    | NoAuthSchemeCredentials
    | None = None,
    enabled: bool = True,
) -> LinkedAccount:
    """Create a linked account
    when security_credentials is None, the linked account will be using App's default security credentials if exists
    # TODO: there is some ambiguity with "no auth" and "use app's default credentials", needs a refactor.
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
    security_credentials: OAuth2SchemeCredentials
    | APIKeySchemeCredentials
    | NoAuthSchemeCredentials,
) -> LinkedAccount:
    """
    Update the security credentials of a linked account.
    Removing the security credentials (setting it to empty dict) is not handled here.
    """
    # TODO: paranoid validation, should be removed if later the validation is done on the schema level
    validators.security_scheme.validate_scheme_and_credentials_type_match(
        linked_account.security_scheme, security_credentials
    )

    linked_account.security_credentials = security_credentials.model_dump(mode="json")
    db_session.flush()
    db_session.refresh(linked_account)
    return linked_account


def update_linked_account(
    db_session: Session,
    linked_account: LinkedAccount,
    linked_account_update: LinkedAccountUpdate,
) -> LinkedAccount:
    if linked_account_update.enabled is not None:
        linked_account.enabled = linked_account_update.enabled
    db_session.flush()
    db_session.refresh(linked_account)
    return linked_account


def update_linked_account_last_used_at(
    db_session: Session,
    last_used_at: datetime,
    linked_account: LinkedAccount,
) -> LinkedAccount:
    linked_account.last_used_at = last_used_at
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


def get_total_number_of_unique_linked_account_owner_ids(db_session: Session, org_id: UUID) -> int:
    """
    TODO: Add a lock to prevent the race condition.
    Get the total number of unique linked account owner IDs for an organization.

    WARNING: Race condition potential! This function is vulnerable to race conditions in
    concurrent environments. If this function is called concurrently with operations that
    add or remove linked accounts:

    1. Thread A starts counting unique linked_account_owner_ids
    2. Thread B adds a new linked account with a new owner_id
    3. Thread A completes its count, unaware of the newly added account
    """
    statement = select(func.count(distinct(LinkedAccount.linked_account_owner_id))).where(
        LinkedAccount.project_id.in_(select(Project.id).filter(Project.org_id == org_id))
    )
    return db_session.execute(statement).scalar_one()


def linked_account_owner_id_exists_in_org(
    db_session: Session, org_id: UUID, linked_account_owner_id: str
) -> bool:
    statement = select(
        exists().where(
            LinkedAccount.linked_account_owner_id == linked_account_owner_id,
            LinkedAccount.project_id.in_(select(Project.id).filter(Project.org_id == org_id)),
        )
    )
    return db_session.execute(statement).scalar() or False
