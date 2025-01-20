from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import AppConfiguration
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationUpdate,
)

logger = get_logger(__name__)


def create_app_configuration(
    db_session: Session,
    project_id: UUID,
    app_configuration_create: AppConfigurationCreate,
) -> AppConfiguration:
    """
    Create a new app configuration record
    """
    app_configuration = AppConfiguration(
        project_id=project_id,
        app_id=app_configuration_create.app_id,
        security_scheme=app_configuration_create.security_scheme,
        security_scheme_overrides=app_configuration_create.security_scheme_overrides,
        enabled=True,
        all_functions_enabled=app_configuration_create.all_functions_enabled,
        enabled_functions=app_configuration_create.enabled_functions,
    )
    db_session.add(app_configuration)
    db_session.flush()
    db_session.refresh(app_configuration)

    return app_configuration


def update_app_configuration(
    db_session: Session,
    app_configuration: AppConfiguration,
    update: AppConfigurationUpdate,
) -> AppConfiguration:
    """
    Update an app configuration by app id.
    If a field is None, it will not be changed.
    """
    # TODO: a better way to do update?
    if update.security_scheme is not None:
        app_configuration.security_scheme = update.security_scheme
    if update.security_scheme_overrides is not None:
        app_configuration.security_scheme_overrides = update.security_scheme_overrides
    if update.enabled is not None:
        app_configuration.enabled = update.enabled
    if update.all_functions_enabled is not None:
        app_configuration.all_functions_enabled = update.all_functions_enabled
    if update.enabled_functions is not None:
        app_configuration.enabled_functions = update.enabled_functions

    db_session.flush()
    db_session.refresh(app_configuration)

    return app_configuration


def delete_app_configuration(db_session: Session, project_id: UUID, app_id: UUID) -> int:
    statement = delete(AppConfiguration).filter_by(project_id=project_id, app_id=app_id)
    result = db_session.execute(statement)
    db_session.flush()
    return int(result.rowcount)


def get_app_configurations(
    db_session: Session, project_id: UUID, app_id: UUID | None, limit: int, offset: int
) -> list[AppConfiguration]:
    """Get all app configurations for a project, optionally filtered by app id"""
    logger.error(
        f"Getting app configurations for project={project_id}, app_id={app_id}, limit={limit}, offset={offset}"
    )
    statement = select(AppConfiguration).filter_by(project_id=project_id)
    if app_id:
        statement = statement.filter_by(app_id=app_id)
    statement = statement.offset(offset).limit(limit)
    app_configurations: list[AppConfiguration] = db_session.execute(statement).scalars().all()
    return app_configurations


def get_app_configuration(
    db_session: Session, project_id: UUID, app_id: UUID
) -> AppConfiguration | None:
    """Get an app configuration by project id and app id"""
    app_configuration: AppConfiguration | None = db_session.execute(
        select(AppConfiguration).filter_by(project_id=project_id, app_id=app_id)
    ).scalar_one_or_none()
    return app_configuration


def get_configured_app_ids(
    db_session: Session,
    project_id: UUID,
) -> list[UUID]:
    """Get just the app IDs that have configurations for a project."""
    return [
        r[0]
        for r in db_session.query(AppConfiguration.app_id)
        .filter(AppConfiguration.project_id == project_id)
        .distinct()
        .all()
    ]


def app_configuration_exists(db_session: Session, project_id: UUID, app_id: UUID) -> bool:
    """Check if an app configuration exists in the database."""
    return (
        db_session.execute(
            select(AppConfiguration).filter_by(project_id=project_id, app_id=app_id)
        ).scalar_one_or_none()
        is not None
    )
