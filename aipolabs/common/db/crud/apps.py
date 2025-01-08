"""
CRUD operations for apps. (not including app_configurations)
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App
from aipolabs.common.enums import Visibility
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.app import AppCreate

logger = get_logger(__name__)


def create_app(
    db_session: Session,
    app: AppCreate,
    app_embedding: list[float],
) -> App:
    logger.debug(f"creating app: {app}")

    db_app = App(
        name=app.name,
        display_name=app.display_name,
        provider=app.provider,
        version=app.version,
        description=app.description,
        logo=app.logo,
        categories=app.categories,
        visibility=app.visibility,
        enabled=app.enabled,
        security_schemes=app.security_schemes,
        embedding=app_embedding,
    )

    db_session.add(db_app)
    db_session.flush()
    db_session.refresh(db_app)

    return db_app


def get_apps(db_session: Session, public_only: bool, limit: int, offset: int) -> list[App]:
    """Get all apps, order by App name"""
    statement = select(App)
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC)
    statement = statement.order_by(App.name).offset(offset).limit(limit)
    db_apps: list[App] = db_session.execute(statement).scalars().all()
    return db_apps


# TODO: remove access control outside crud
def search_apps(
    db_session: Session,
    api_key_id: UUID,
    categories: list[str] | None,
    intent_embedding: list[float] | None,
    limit: int,
    offset: int,
) -> list[tuple[App, float | None]]:
    """Get a list of apps with optional filtering by categories and sorting by vector similarity to intent. and pagination."""
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    statement = select(App)

    # filter out disabled apps
    statement = statement.filter(App.enabled)
    # if the corresponding project (api key belongs to) can only access public apps, filter out private apps
    if db_project.visibility_access == Visibility.PUBLIC:
        statement = statement.filter(App.visibility == Visibility.PUBLIC)
    # TODO: Is there any way to get typing for cosine_distance, label, overlap?
    if categories and len(categories) > 0:
        statement = statement.filter(App.categories.overlap(categories))
    if intent_embedding:
        similarity_score = App.embedding.cosine_distance(intent_embedding)
        statement = statement.add_columns(similarity_score.label("similarity_score"))
        statement = statement.order_by("similarity_score")

    statement = statement.offset(offset).limit(limit)

    logger.debug(f"Executing statement: {statement}")

    results = db_session.execute(statement).all()

    if intent_embedding:
        return [(app, score) for app, score in results]
    else:
        return [(app, None) for app, in results]


def set_app_enabled_status(db_session: Session, app_id: UUID, enabled: bool) -> None:
    statement = update(App).filter_by(id=app_id).values(enabled=enabled)
    db_session.execute(statement)


def set_app_visibility(db_session: Session, app_id: UUID, visibility: Visibility) -> None:
    statement = update(App).filter_by(id=app_id).values(visibility=visibility)
    db_session.execute(statement)


def get_app(db_session: Session, app_id: UUID) -> App | None:
    db_app: App | None = db_session.execute(select(App).filter_by(id=app_id)).scalar_one_or_none()
    return db_app


def get_app_by_name(db_session: Session, app_name: str) -> App | None:
    db_app: App | None = db_session.execute(
        select(App).filter_by(name=app_name)
    ).scalar_one_or_none()
    return db_app
