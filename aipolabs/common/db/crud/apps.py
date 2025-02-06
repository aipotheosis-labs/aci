"""
CRUD operations for apps. (not including app_configurations)
"""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aipolabs.common.db.sql_models import App
from aipolabs.common.enums import SecurityScheme, Visibility
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.app import AppCreate

logger = get_logger(__name__)


def create_app(
    db_session: Session,
    app_create: AppCreate,
    app_embedding: list[float],
) -> App:
    logger.debug(f"creating app: {app_create}")

    app_create_dict = app_create.model_dump(mode="json", exclude_none=True)
    app = App(
        **app_create_dict,
        embedding=app_embedding,
    )

    db_session.add(app)
    db_session.flush()
    db_session.refresh(app)
    return app


def update_app_default_security_credentials(
    db_session: Session,
    app: App,
    security_scheme: SecurityScheme,
    security_credentials: dict,
) -> None:
    # Note: this update works because of the MutableDict.as_mutable(JSON) in the sql_models.py
    # TODO: check if this is the best practice and double confirm that nested dict update does NOT work
    app.default_security_credentials_by_scheme[security_scheme] = security_credentials


def get_app(db_session: Session, app_id: UUID, public_only: bool, active_only: bool) -> App | None:
    statement = select(App).filter_by(id=app_id)
    if active_only:
        statement = statement.filter(App.active)
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC)
    app: App | None = db_session.execute(statement).scalar_one_or_none()
    return app


def get_app_by_name(
    db_session: Session, app_name: str, public_only: bool, active_only: bool
) -> App | None:
    statement = select(App).filter_by(name=app_name)
    if active_only:
        statement = statement.filter(App.active)
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC)
    app: App | None = db_session.execute(statement).scalar_one_or_none()
    return app


def get_apps(
    db_session: Session,
    public_only: bool,
    active_only: bool,
    app_ids: list[UUID] | None,
    limit: int | None,
    offset: int | None,
) -> list[App]:
    statement = select(App)
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC)
    if active_only:
        statement = statement.filter(App.active)
    if app_ids is not None:
        statement = statement.filter(App.id.in_(app_ids))
    if offset is not None:
        statement = statement.offset(offset)
    if limit is not None:
        statement = statement.limit(limit)
    apps: list[App] = db_session.execute(statement).scalars().all()
    return apps


def search_apps(
    db_session: Session,
    public_only: bool,
    active_only: bool,
    app_ids: list[UUID] | None,
    categories: list[str] | None,
    intent_embedding: list[float] | None,
    limit: int,
    offset: int,
) -> list[tuple[App, float | None]]:
    """Get a list of apps with optional filtering by categories and sorting by vector similarity to intent. and pagination."""
    statement = select(App)

    # filter out private apps
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC)

    # filter out inactive apps
    if active_only:
        statement = statement.filter(App.active)

    # filter out apps by app_ids
    if app_ids:
        statement = statement.filter(App.id.in_(app_ids))

    # filter out apps by categories
    # TODO: Is there any way to get typing for cosine_distance, label, overlap?
    if categories and len(categories) > 0:
        statement = statement.filter(App.categories.overlap(categories))

    # sort by similarity to intent
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


def set_app_active_status(db_session: Session, app_id: UUID, active: bool) -> None:
    statement = update(App).filter_by(id=app_id).values(active=active)
    db_session.execute(statement)


def set_app_visibility(db_session: Session, app_id: UUID, visibility: Visibility) -> None:
    statement = update(App).filter_by(id=app_id).values(visibility=visibility)
    db_session.execute(statement)
