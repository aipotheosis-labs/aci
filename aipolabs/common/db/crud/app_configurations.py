from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import AppConfiguration
from aipolabs.common.enums import SecurityScheme


def create_app_configuration(
    db_session: Session,
    project_id: UUID,
    app_id: UUID,
    security_scheme: SecurityScheme,
    security_config_overrides: dict,
    all_functions_enabled: bool,
    enabled_functions: list[UUID],
) -> AppConfiguration:
    """create a new app configuration record"""
    # TODO: use pydantic model to validate the input
    if all_functions_enabled and len(enabled_functions) > 0:
        raise ValueError(
            "all_functions_enabled and enabled_functions cannot be both True and non-empty"
        )

    db_app_configuration = AppConfiguration(
        project_id=project_id,
        app_id=app_id,
        security_scheme=security_scheme,
        security_config_overrides=security_config_overrides,
        enabled=True,
        all_functions_enabled=all_functions_enabled,
        enabled_functions=enabled_functions,
    )
    db_session.add(db_app_configuration)
    db_session.flush()
    db_session.refresh(db_app_configuration)
    return db_app_configuration


def delete_app_configuration(db_session: Session, project_id: UUID, app_id: UUID) -> int:
    statement = delete(AppConfiguration).filter_by(project_id=project_id, app_id=app_id)
    result = db_session.execute(statement)
    return int(result.rowcount)


def get_app_configurations(
    db_session: Session, project_id: UUID, app_id: UUID | None = None
) -> list[AppConfiguration]:
    """Get all app configurations for a project, optionally filtered by app id"""
    statement = select(AppConfiguration).filter_by(project_id=project_id)
    if app_id:
        statement = statement.filter_by(app_id=app_id)
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


def app_configuration_exists(db_session: Session, project_id: UUID, app_id: UUID) -> bool:
    """Check if an app configuration exists in the database."""
    return (
        db_session.execute(
            select(AppConfiguration).filter_by(project_id=project_id, app_id=app_id)
        ).scalar_one_or_none()
        is not None
    )
