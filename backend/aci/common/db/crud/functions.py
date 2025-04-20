from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aci.common import utils
from aci.common.db import crud
from aci.common.db.sql_models import App, Function
from aci.common.enums import Visibility
from aci.common.logging_setup import get_logger
from aci.common.schemas.function import FunctionUpsert

logger = get_logger(__name__)


def create_functions(
    db_session: Session,
    functions_upsert: list[FunctionUpsert],
    functions_embeddings: list[list[float]],
) -> list[Function]:
    """
    Create functions.
    Note: each function might be of different app.
    """
    logger.debug(f"creating functions: {functions_upsert}")

    functions = []
    for i, function_upsert in enumerate(functions_upsert):
        app_name = utils.parse_app_name_from_function_name(function_upsert.name)
        app = crud.apps.get_app(db_session, app_name, False, False)
        if not app:
            logger.error(f"App={app_name} does not exist for function={function_upsert.name}")
            raise ValueError(f"App={app_name} does not exist for function={function_upsert.name}")
        function_data = function_upsert.model_dump(mode="json", exclude_none=True)
        function = Function(
            app_id=app.id,
            **function_data,
            embedding=functions_embeddings[i],
        )
        db_session.add(function)
        functions.append(function)

    db_session.flush()

    return functions


def update_functions(
    db_session: Session,
    functions_upsert: list[FunctionUpsert],
    functions_embeddings: list[list[float] | None],
) -> list[Function]:
    """
    Update functions.
    Note: each function might be of different app.
    With the option to update the function embedding. (needed if FunctionEmbeddingFields are updated)
    """
    logger.debug(f"updating functions: {functions_upsert}")
    functions = []
    for i, function_upsert in enumerate(functions_upsert):
        function = crud.functions.get_function(db_session, function_upsert.name, False, False)
        if not function:
            logger.error(f"Function={function_upsert.name} does not exist")
            raise ValueError(f"Function={function_upsert.name} does not exist")

        function_data = function_upsert.model_dump(mode="json", exclude_unset=True)
        for field, value in function_data.items():
            setattr(function, field, value)
        if functions_embeddings[i] is not None:
            function.embedding = functions_embeddings[i]  # type: ignore
        functions.append(function)

    db_session.flush()

    return functions


def search_functions(
    db_session: Session,
    public_only: bool,
    active_only: bool,
    app_names: list[str] | None,
    intent_embedding: list[float] | None,
    limit: int,
    offset: int,
) -> list[Function]:
    """Get a list of functions with optional filtering by app names and sorting by vector similarity to intent."""
    statement = select(Function).join(App, Function.app_id == App.id)

    # filter out all functions of inactive apps and all inactive functions
    # (where app is active buy specific functions can be inactive)
    if active_only:
        statement = statement.filter(App.active).filter(Function.active)
    # if the corresponding project (api key belongs to) can only access public apps and functions,
    # filter out all functions of private apps and all private functions (where app is public but specific function is private)
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC).filter(
            Function.visibility == Visibility.PUBLIC
        )
    # filter out functions that are not in the specified apps
    if app_names is not None:
        statement = statement.filter(App.name.in_(app_names))

    if intent_embedding is not None:
        similarity_score = Function.embedding.cosine_distance(intent_embedding)
        statement = statement.order_by(similarity_score)

    statement = statement.offset(offset).limit(limit)
    logger.debug(f"Executing statement: {statement}")

    return list(db_session.execute(statement).scalars().all())


def get_functions(
    db_session: Session,
    public_only: bool,
    active_only: bool,
    app_names: list[str] | None,
    limit: int,
    offset: int,
) -> list[Function]:
    """Get a list of functions and their details. Sorted by function name."""
    statement = select(Function).join(App, Function.app_id == App.id)

    if app_names is not None:
        statement = statement.filter(App.name.in_(app_names))

    # exclude private Apps's functions and private functions if public_only is True
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC).filter(
            Function.visibility == Visibility.PUBLIC
        )
    # exclude inactive functions (including all functions if apps are inactive)
    if active_only:
        statement = statement.filter(App.active).filter(Function.active)

    statement = statement.order_by(Function.name).offset(offset).limit(limit)

    return list(db_session.execute(statement).scalars().all())


def get_functions_by_app_id(db_session: Session, app_id: UUID) -> list[Function]:
    statement = select(Function).filter(Function.app_id == app_id)

    return list(db_session.execute(statement).scalars().all())


def get_function(
    db_session: Session, function_name: str, public_only: bool, active_only: bool
) -> Function | None:
    statement = select(Function).filter(Function.name == function_name)

    # filter out all functions of inactive apps and all inactive functions
    # (where app is active buy specific functions can be inactive)
    if active_only:
        statement = (
            statement.join(App, Function.app_id == App.id)
            .filter(App.active)
            .filter(Function.active)
        )
    # if the corresponding project (api key belongs to) can only access public apps and functions,
    # filter out all functions of private apps and all private functions (where app is public but specific function is private)
    if public_only:
        statement = statement.filter(App.visibility == Visibility.PUBLIC).filter(
            Function.visibility == Visibility.PUBLIC
        )

    return db_session.execute(statement).scalar_one_or_none()


def set_function_active_status(db_session: Session, function_name: str, active: bool) -> None:
    statement = update(Function).filter_by(name=function_name).values(active=active)
    db_session.execute(statement)


def set_function_visibility(
    db_session: Session, function_name: str, visibility: Visibility
) -> None:
    statement = update(Function).filter_by(name=function_name).values(visibility=visibility)
    db_session.execute(statement)
