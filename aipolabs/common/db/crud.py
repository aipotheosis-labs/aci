"""
CRUD operations for the database.
Do NOT commit to db in these functions. Handle commit and rollback in the caller.
"""

import datetime
import secrets
from typing import Union
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from aipolabs.common import utils
from aipolabs.common.db import sql_models
from aipolabs.common.enums import (
    APIKeyStatus,
    ProjectOwnerType,
    SecurityScheme,
    Visibility,
)
from aipolabs.common.logging import get_logger
from aipolabs.common.schemas.agent import AgentCreate
from aipolabs.common.schemas.app import AppCreate
from aipolabs.common.schemas.function import FunctionCreate
from aipolabs.common.schemas.project import ProjectCreate
from aipolabs.common.schemas.user import UserCreate

logger = get_logger(__name__)


class UserNotFoundError(Exception):
    """Exception raised when a user is not found in the database."""

    pass


class ProjectNotFoundError(Exception):
    """Exception raised when a project is not found in the database."""

    pass


def add_integration(
    db_session: Session,
    project_id: UUID,
    app_id: UUID,
    security_scheme: SecurityScheme,
    security_config_overrides: dict,
    all_functions_enabled: bool,
    enabled_functions: list[UUID],
) -> sql_models.ProjectAppIntegration:
    """create a new project-app integration record"""
    if all_functions_enabled and len(enabled_functions) > 0:
        raise ValueError(
            "all_functions_enabled and enabled_functions cannot be both True and non-empty"
        )

    db_project_app_integration = sql_models.ProjectAppIntegration(
        project_id=project_id,
        app_id=app_id,
        security_scheme=security_scheme,
        security_config_overrides=security_config_overrides,
        enabled=True,
        all_functions_enabled=all_functions_enabled,
        enabled_functions=enabled_functions,
    )
    db_session.add(db_project_app_integration)
    db_session.flush()
    db_session.refresh(db_project_app_integration)
    return db_project_app_integration


def integration_exists(db_session: Session, project_id: UUID, app_id: UUID) -> bool:
    """Check if a project-app integration exists in the database."""
    return (
        db_session.execute(
            select(sql_models.ProjectAppIntegration).filter_by(project_id=project_id, app_id=app_id)
        ).scalar_one_or_none()
        is not None
    )


def user_exists(db_session: Session, user_id: UUID) -> bool:
    """Check if a user exists in the database."""
    return (
        db_session.execute(select(sql_models.User).filter_by(id=user_id)).scalar_one_or_none()
        is not None
    )


def create_user(db_session: Session, user: UserCreate) -> sql_models.User:
    db_user = sql_models.User(**user.model_dump())
    db_session.add(db_user)
    db_session.flush()
    db_session.refresh(db_user)
    return db_user


def get_or_create_user(db_session: Session, user: UserCreate) -> sql_models.User:
    # Step 1: Acquire a lock on the row to prevent race condition
    db_user: Union[sql_models.User, None] = db_session.execute(
        select(sql_models.User)
        .where(
            sql_models.User.auth_provider == user.auth_provider,
            sql_models.User.auth_user_id == user.auth_user_id,
        )
        .with_for_update()
    ).scalar_one_or_none()

    if db_user:
        return db_user  # Return the existing user if found

    # Step 2: Create the user if not found
    # TODO: compliance with PII data
    logger.info(f"Creating user: {user.name}")
    db_user = create_user(db_session, user)
    return db_user


def create_project(
    db_session: Session,
    project: ProjectCreate,
    # visibility_access can not be part of ProjectCreate otherwise users can create projects with private visibility
    visibility_access: Visibility = Visibility.PUBLIC,
) -> sql_models.Project:
    """
    Create a new project.
    Assume called has privilege to create project under the specified user or organization.
    """
    owner_user_id = project.owner_id if project.owner_type == ProjectOwnerType.USER else None
    owner_organization_id = (
        project.owner_id if project.owner_type == ProjectOwnerType.ORGANIZATION else None
    )
    db_project = sql_models.Project(
        name=project.name,
        owner_user_id=owner_user_id,
        owner_organization_id=owner_organization_id,
        created_by=project.created_by,
        visibility_access=visibility_access,
    )
    db_session.add(db_project)
    db_session.flush()
    db_session.refresh(db_project)

    return db_project


def create_agent(db_session: Session, agent: AgentCreate) -> sql_models.Agent:
    """
    Create a new agent under a project, and create a new API key for the agent.
    Assume user's access to the project has been checked.
    TODO: a more unified way to handle access control?
    TODO: handle agent exclusion of apps and functions
    """
    # Create the agent
    db_agent = sql_models.Agent(**agent.model_dump())
    db_session.add(db_agent)
    db_session.flush()  # Flush to get the agent's ID

    # Create the API key for the agent
    api_key = sql_models.APIKey(
        key=secrets.token_hex(32), agent_id=db_agent.id, status=APIKeyStatus.ACTIVE
    )
    db_session.add(api_key)
    db_session.flush()

    db_session.refresh(db_agent)
    return db_agent


def get_agent_by_id(db_session: Session, agent_id: UUID) -> sql_models.Agent | None:
    db_agent: sql_models.Agent | None = db_session.execute(
        select(sql_models.Agent).filter_by(id=agent_id)
    ).scalar_one_or_none()

    return db_agent


def get_api_key_by_agent_id(db_session: Session, agent_id: UUID) -> sql_models.APIKey | None:
    db_api_key: sql_models.APIKey | None = db_session.execute(
        select(sql_models.APIKey).filter_by(agent_id=agent_id)
    ).scalar_one_or_none()

    return db_api_key


def user_has_admin_access_to_org(db_session: Session, user_id: UUID, org_id: UUID) -> bool:
    """Check if a user has admin access to an organization."""
    # TODO: implement this
    return True


def user_has_admin_access_to_project(db_session: Session, user_id: UUID, project_id: UUID) -> bool:
    """Check if a user has admin access to a project."""
    # TODO: implement properly with organization and project access control
    # for now, just check if project owner is the user
    db_project = db_session.execute(
        select(sql_models.Project).filter_by(id=project_id)
    ).scalar_one_or_none()
    if not db_project:
        raise ProjectNotFoundError(f"Project with ID {project_id} not found")

    return db_project.owner_user_id is not None and db_project.owner_user_id == user_id


def get_api_key(db_session: Session, key: str) -> sql_models.APIKey | None:
    db_api_key: sql_models.APIKey | None = db_session.execute(
        select(sql_models.APIKey).filter_by(key=key)
    ).scalar_one_or_none()

    return db_api_key


# TODO: remove access control outside crud
def search_apps(
    db_session: Session,
    api_key_id: UUID,
    categories: list[str] | None,
    intent_embedding: list[float] | None,
    limit: int,
    offset: int,
) -> list[tuple[sql_models.App, float | None]]:
    """Get a list of apps with optional filtering by categories and sorting by vector similarity to intent. and pagination."""
    db_project = get_project_by_api_key_id(db_session, api_key_id)
    statement = select(sql_models.App)

    # filter out disabled apps
    statement = statement.filter(sql_models.App.enabled)
    # if the corresponding project (api key belongs to) can only access public apps, filter out private apps
    if db_project.visibility_access == Visibility.PUBLIC:
        statement = statement.filter(sql_models.App.visibility == Visibility.PUBLIC)
    # TODO: Is there any way to get typing for cosine_distance, label, overlap?
    if categories and len(categories) > 0:
        statement = statement.filter(sql_models.App.categories.overlap(categories))
    if intent_embedding:
        similarity_score = sql_models.App.embedding.cosine_distance(intent_embedding)
        statement = statement.add_columns(similarity_score.label("similarity_score"))
        statement = statement.order_by("similarity_score")

    statement = statement.offset(offset).limit(limit)

    logger.debug(f"Executing statement: {statement}")

    results = db_session.execute(statement).all()

    if intent_embedding:
        return [(app, score) for app, score in results]
    else:
        return [(app, None) for app, in results]


def search_functions(
    db_session: Session,
    api_key_id: UUID,
    app_names: list[str] | None,
    intent_embedding: list[float] | None,
    limit: int,
    offset: int,
) -> list[sql_models.Function]:
    """Get a list of functions with optional filtering by app names and sorting by vector similarity to intent."""
    db_project = get_project_by_api_key_id(db_session, api_key_id)
    statement = select(sql_models.Function)

    # filter out all functions of disabled apps and all disabled functions (where app is enabled buy specific functions can be disabled)
    statement = (
        statement.join(sql_models.App)
        .filter(sql_models.App.enabled)
        .filter(sql_models.Function.enabled)
    )
    # if the corresponding project (api key belongs to) can only access public apps and functions, filter out all functions of private apps
    # and all private functions (where app is public but specific function is private)
    if db_project.visibility_access == Visibility.PUBLIC:
        statement = statement.filter(sql_models.App.visibility == Visibility.PUBLIC).filter(
            sql_models.Function.visibility == Visibility.PUBLIC
        )
    # filter out functions that are not in the specified apps
    if app_names and len(app_names) > 0:
        statement = statement.filter(sql_models.App.name.in_(app_names))

    if intent_embedding:
        similarity_score = sql_models.Function.embedding.cosine_distance(intent_embedding)
        statement = statement.order_by(similarity_score)

    statement = statement.offset(offset).limit(limit)
    logger.debug(f"Executing statement: {statement}")
    results: list[sql_models.Function] = db_session.execute(statement).scalars().all()
    return results


def get_function(
    db_session: Session, api_key_id: UUID, function_name: str
) -> sql_models.Function | None:
    """
    Get a function by name.
    Should filter out by function visibility, app visibility, and project visibility access.
    Should filter out by function enabled status.
    """
    # function: sql_models.Function | None = db_session.execute(
    #     select(sql_models.Function).filter_by(name=function_name)
    # ).scalar_one_or_none()
    db_project = get_project_by_api_key_id(db_session, api_key_id)
    statement = select(sql_models.Function).filter_by(name=function_name)

    # filter out all functions of disabled apps and all disabled functions (where app is enabled buy specific functions can be disabled)
    statement = (
        statement.join(sql_models.App)
        .filter(sql_models.App.enabled)
        .filter(sql_models.Function.enabled)
    )
    # if the corresponding project (api key belongs to) can only access public apps and functions, filter out all functions of private apps
    # and all private functions (where app is public but specific function is private)
    if db_project.visibility_access == Visibility.PUBLIC:
        statement = statement.filter(sql_models.App.visibility == Visibility.PUBLIC).filter(
            sql_models.Function.visibility == Visibility.PUBLIC
        )

    function: sql_models.Function | None = db_session.execute(statement).scalar_one_or_none()

    return function


def create_app(
    db_session: Session,
    app: AppCreate,
    app_embedding: list[float],
) -> sql_models.App:
    logger.debug(f"creating app: {app}")

    # Check if app already exists
    existing_app = db_session.execute(
        select(sql_models.App).filter_by(name=app.name)
    ).scalar_one_or_none()

    if existing_app:
        raise ValueError(f"App {app.name} already exists")

    # Create new app
    db_app = sql_models.App(
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


def create_functions(
    db_session: Session, functions: list[FunctionCreate], function_embeddings: list[list[float]]
) -> list[sql_models.Function]:
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
    db_app = get_app_by_name(db_session, app_name)
    if not db_app:
        raise ValueError(f"App {app_name} does not exist")

    db_functions = []
    for i, function in enumerate(functions):
        db_function = sql_models.Function(
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


def set_app_enabled_status(db_session: Session, app_id: UUID, enabled: bool) -> None:
    statement = update(sql_models.App).filter_by(id=app_id).values(enabled=enabled)
    db_session.execute(statement)


def set_app_enabled_status_by_name(db_session: Session, app_name: str, enabled: bool) -> None:
    statement = update(sql_models.App).filter_by(name=app_name).values(enabled=enabled)
    db_session.execute(statement)


def set_app_visibility(db_session: Session, app_id: UUID, visibility: Visibility) -> None:
    statement = update(sql_models.App).filter_by(id=app_id).values(visibility=visibility)
    db_session.execute(statement)


def set_app_visibility_by_name(db_session: Session, app_name: str, visibility: Visibility) -> None:
    statement = update(sql_models.App).filter_by(name=app_name).values(visibility=visibility)
    db_session.execute(statement)


def get_app_by_id(db_session: Session, app_id: UUID) -> sql_models.App | None:
    db_app: sql_models.App | None = db_session.execute(
        select(sql_models.App).filter_by(id=app_id)
    ).scalar_one_or_none()
    return db_app


def get_app_by_name(db_session: Session, app_name: str) -> sql_models.App | None:
    db_app: sql_models.App | None = db_session.execute(
        select(sql_models.App).filter_by(name=app_name)
    ).scalar_one_or_none()
    return db_app


def get_function_by_name(db_session: Session, function_name: str) -> sql_models.Function | None:
    db_function: sql_models.Function | None = db_session.execute(
        select(sql_models.Function).filter_by(name=function_name)
    ).scalar_one_or_none()
    return db_function


def set_function_enabled_status(db_session: Session, function_id: UUID, enabled: bool) -> None:
    statement = update(sql_models.Function).filter_by(id=function_id).values(enabled=enabled)
    db_session.execute(statement)


def set_function_visibility(db_session: Session, function_id: UUID, visibility: Visibility) -> None:
    statement = update(sql_models.Function).filter_by(id=function_id).values(visibility=visibility)
    db_session.execute(statement)


def set_project_visibility_access(
    db_session: Session, project_id: UUID, visibility_access: Visibility
) -> None:
    statement = (
        update(sql_models.Project)
        .filter_by(id=project_id)
        .values(visibility_access=visibility_access)
    )
    db_session.execute(statement)


def get_project_by_api_key_id(db_session: Session, api_key_id: UUID) -> sql_models.Project:
    # api key id -> agent id -> project id
    db_project: sql_models.Project = db_session.execute(
        select(sql_models.Project)
        .join(sql_models.Agent, sql_models.Project.id == sql_models.Agent.project_id)
        .join(sql_models.APIKey, sql_models.Agent.id == sql_models.APIKey.agent_id)
        .filter(sql_models.APIKey.id == api_key_id)
    ).scalar_one()

    return db_project


def increase_project_quota_usage(db_session: Session, project: sql_models.Project) -> None:
    now: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    need_reset = now >= project.daily_quota_reset_at.replace(
        tzinfo=datetime.timezone.utc
    ) + datetime.timedelta(days=1)

    if need_reset:
        # Reset the daily quota
        statement = (
            update(sql_models.Project)
            .where(sql_models.Project.id == project.id)
            .values(
                {
                    sql_models.Project.daily_quota_used: 1,
                    sql_models.Project.daily_quota_reset_at: now,
                    sql_models.Project.total_quota_used: project.total_quota_used + 1,
                }
            )
        )
    else:
        # Increment the daily quota
        statement = (
            update(sql_models.Project)
            .where(sql_models.Project.id == project.id)
            .values(
                {
                    sql_models.Project.daily_quota_used: project.daily_quota_used + 1,
                    sql_models.Project.total_quota_used: project.total_quota_used + 1,
                }
            )
        )

    db_session.execute(statement)
