from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.db.sql_models import App, Function
from aipolabs.common.enums import Visibility
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.function import FunctionCreate

logger = get_logger(__name__)


def create_functions(
    db_session: Session, functions: list[FunctionCreate], function_embeddings: list[list[float]]
) -> list[Function]:
    """Create functions of the same app"""
    logger.debug(f"upserting functions: {functions}")
    # each function name must be unique
    if len(functions) != len(set(function.name for function in functions)):
        raise ValueError("Function names must be unique")
    # all functions must belong to the same app
    app_names = set(
        [utils.parse_app_name_from_function_name(function.name) for function in functions]
    )
    if len(app_names) != 1:
        raise ValueError("All functions must belong to the same app")
    app_name = app_names.pop()
    # check if the app exists
    db_app = crud.apps.get_app_by_name(db_session, app_name)
    if not db_app:
        raise ValueError(f"App {app_name} does not exist")

    db_functions = []
    for i, function in enumerate(functions):
        db_function = Function(
            app_id=db_app.id,
            name=function.name,
            description=function.description,
            tags=function.tags,
            visibility=function.visibility,
            enabled=function.enabled,
            protocol=function.protocol,
            protocol_data=function.protocol_data.model_dump(),
            parameters=function.parameters,
            response=function.response,
            embedding=function_embeddings[i],
        )
        db_session.add(db_function)
        db_functions.append(db_function)

    db_session.flush()
    return db_functions


def search_functions(
    db_session: Session,
    api_key_id: UUID,
    app_ids: list[UUID] | None,
    intent_embedding: list[float] | None,
    limit: int,
    offset: int,
) -> list[Function]:
    """Get a list of functions with optional filtering by app names and sorting by vector similarity to intent."""
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    statement = select(Function)

    # filter out all functions of disabled apps and all disabled functions (where app is enabled buy specific functions can be disabled)
    statement = statement.join(App).filter(App.enabled).filter(Function.enabled)
    # if the corresponding project (api key belongs to) can only access public apps and functions, filter out all functions of private apps
    # and all private functions (where app is public but specific function is private)
    if db_project.visibility_access == Visibility.PUBLIC:
        statement = statement.filter(App.visibility == Visibility.PUBLIC).filter(
            Function.visibility == Visibility.PUBLIC
        )
    # filter out functions that are not in the specified apps
    if app_ids:
        statement = statement.filter(App.id.in_(app_ids))

    if intent_embedding:
        similarity_score = Function.embedding.cosine_distance(intent_embedding)
        statement = statement.order_by(similarity_score)

    statement = statement.offset(offset).limit(limit)
    logger.debug(f"Executing statement: {statement}")
    results: list[Function] = db_session.execute(statement).scalars().all()
    return results


def get_functions(
    db_session: Session, public_only: bool, app_ids: list[UUID] | None, limit: int, offset: int
) -> list[Function]:
    """Get a list of functions and their details. Sorted by function name."""
    # exclude private Apps's functions and private functions if public_only is True
    statement = select(Function).join(App)

    if app_ids:
        statement = statement.filter(App.id.in_(app_ids))

    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC).filter(
            Function.visibility == Visibility.PUBLIC
        )
    statement = statement.order_by(Function.name).offset(offset).limit(limit)
    results: list[Function] = db_session.execute(statement).scalars().all()
    return results


# TODO: remove access control outside crud
def get_function(db_session: Session, api_key_id: UUID, function_id: UUID) -> Function | None:
    """
    Get a function by name.
    Should filter out by function visibility, app visibility, and project visibility access.
    Should filter out by function enabled status.
    """
    db_project = crud.projects.get_project_by_api_key_id(db_session, api_key_id)
    statement = select(Function).filter_by(id=function_id)

    # filter out all functions of disabled apps and all disabled functions (where app is enabled buy specific functions can be disabled)
    statement = statement.join(App).filter(App.enabled).filter(Function.enabled)
    # if the corresponding project (api key belongs to) can only access public apps and functions, filter out all functions of private apps
    # and all private functions (where app is public but specific function is private)
    if db_project.visibility_access == Visibility.PUBLIC:
        statement = statement.filter(App.visibility == Visibility.PUBLIC).filter(
            Function.visibility == Visibility.PUBLIC
        )

    function: Function | None = db_session.execute(statement).scalar_one_or_none()

    return function


def get_function_by_name(db_session: Session, function_name: str) -> Function | None:
    db_function: Function | None = db_session.execute(
        select(Function).filter_by(name=function_name)
    ).scalar_one_or_none()
    return db_function


def set_function_enabled_status(db_session: Session, function_id: UUID, enabled: bool) -> None:
    statement = update(Function).filter_by(id=function_id).values(enabled=enabled)
    db_session.execute(statement)


def set_function_visibility(db_session: Session, function_id: UUID, visibility: Visibility) -> None:
    statement = update(Function).filter_by(id=function_id).values(visibility=visibility)
    db_session.execute(statement)
