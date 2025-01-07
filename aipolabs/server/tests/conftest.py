from unittest.mock import patch

# override the rate limit to a high number for testing before importing aipolabs modules
with patch.dict("os.environ", {"SERVER_RATE_LIMIT_IP_PER_SECOND": "999"}):
    from aipolabs.common import utils
    from aipolabs.common.db import crud
    from aipolabs.common.db.sql_models import Base, User, Project, App, Function
    from aipolabs.common.enums import Visibility
    from aipolabs.common.schemas.user import UserCreate
    from aipolabs.server import config
    from aipolabs.server.main import app as fastapi_app
    from aipolabs.server.routes.auth import create_access_token
    from aipolabs.server.tests import helper

import logging
from datetime import timedelta
from typing import Generator, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def db_setup_and_cleanup() -> Generator[None, None, None]:
    # Use 'with' to manage the session context
    with utils.create_db_session(config.DB_FULL_URL) as session:
        inspector = cast(Inspector, inspect(session.bind))

        # Check if all tables defined in models are created in the db
        for table in Base.metadata.tables.values():
            if not inspector.has_table(table.name):
                pytest.exit(f"Table {table} does not exist in the database.")

        # Go through all tables and make sure there are no records in the table
        # (skip alembic_version table)
        for table in Base.metadata.tables.values():
            if table.name != "alembic_version" and session.query(table).count() > 0:
                pytest.exit(f"Table {table} is not empty.")

        yield  # This allows the test to run

        # Clean up: Empty all tables after tests in reverse order of creation
        for table in reversed(Base.metadata.sorted_tables):
            if table.name != "alembic_version" and session.query(table).count() > 0:
                logger.warning(f"Deleting all records from table {table.name}")
                session.execute(table.delete())
        session.commit()


@pytest.fixture(scope="session")
def test_client() -> Generator[TestClient, None, None]:
    # disable following redirects for testing login
    # NOTE: need to set base_url to http://localhost because we set TrustedHostMiddleware in main.py
    with TestClient(fastapi_app, base_url="http://localhost", follow_redirects=False) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def dummy_user() -> Generator[User, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as fixture_db_session:
        dummy_user = crud.get_or_create_user(
            fixture_db_session,
            UserCreate(
                auth_provider="dummy_auth_provider",
                auth_user_id="dummy_user_id",
                name="Dummy User",
                email="dummy@example.com",
            ),
        )
        fixture_db_session.commit()
        yield dummy_user


@pytest.fixture(scope="session", autouse=True)
def dummy_user_bearer_token(dummy_user: User) -> str:
    return create_access_token(str(dummy_user.id), timedelta(minutes=15))


@pytest.fixture(scope="session", autouse=True)
def dummy_project(dummy_user: User) -> Generator[Project, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as fixture_db_session:
        dummy_project = crud.create_project(
            fixture_db_session,
            owner_id=dummy_user.id,
            name="Dummy Project",
            visibility_access=Visibility.PUBLIC,
        )
        fixture_db_session.commit()
        yield dummy_project


@pytest.fixture(scope="session", autouse=True)
def dummy_api_key(dummy_project: Project) -> Generator[str, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as fixture_db_session:
        dummy_agent = crud.create_agent(
            fixture_db_session,
            project_id=dummy_project.id,
            name="Dummy Agent",
            description="Dummy Agent",
            excluded_apps=[],
            excluded_functions=[],
        )
        fixture_db_session.commit()
        yield dummy_agent.api_keys[0].key


@pytest.fixture(scope="session", autouse=True)
def dummy_project_2(dummy_user: User) -> Generator[Project, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as fixture_db_session:
        dummy_project = crud.create_project(
            fixture_db_session,
            owner_id=dummy_user.id,
            name="Dummy Project 2",
            visibility_access=Visibility.PUBLIC,
        )
        fixture_db_session.commit()
        yield dummy_project


@pytest.fixture(scope="session", autouse=True)
def dummy_api_key_2(dummy_project_2: Project, dummy_user: User) -> Generator[str, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as fixture_db_session:
        dummy_agent = crud.create_agent(
            fixture_db_session,
            project_id=dummy_project_2.id,
            name="Dummy Agent 2",
            description="Dummy Agent 2",
            excluded_apps=[],
            excluded_functions=[],
        )
        fixture_db_session.commit()
        yield dummy_agent.api_keys[0].key


@pytest.fixture(scope="session", autouse=True)
def dummy_apps() -> Generator[list[App], None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as fixture_db_session:
        dummy_apps = helper.create_dummy_apps_and_functions(fixture_db_session)
        yield dummy_apps


@pytest.fixture(scope="session")
def dummy_app_google(dummy_apps: list[App]) -> App:
    dummy_app_google = next(app for app in dummy_apps if app.name == "GOOGLE")
    assert dummy_app_google is not None
    return dummy_app_google


@pytest.fixture(scope="session")
def dummy_app_github(dummy_apps: list[App]) -> App:
    dummy_app_github = next(app for app in dummy_apps if app.name == "GITHUB")
    assert dummy_app_github is not None
    return dummy_app_github


@pytest.fixture(scope="session")
def dummy_app_aipolabs_test(dummy_apps: list[App]) -> App:
    dummy_app_aipolabs_test = next(app for app in dummy_apps if app.name == "AIPOLABS_TEST")
    assert dummy_app_aipolabs_test is not None
    return dummy_app_aipolabs_test


@pytest.fixture(scope="session")
def dummy_functions(dummy_apps: list[App]) -> list[Function]:
    dummy_functions: list[Function] = []
    for dummy_app in dummy_apps:
        dummy_functions.extend(dummy_app.functions)
    return dummy_functions


@pytest.fixture(scope="session")
def dummy_function_github__create_repository(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_github__create_repository = next(
        func for func in dummy_functions if func.name == "GITHUB__CREATE_REPOSITORY"
    )
    assert dummy_function_github__create_repository is not None
    return dummy_function_github__create_repository


@pytest.fixture(scope="session")
def dummy_function_google__calendar_create_event(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_google__calendar_create_event = next(
        func for func in dummy_functions if func.name == "GOOGLE__CALENDAR_CREATE_EVENT"
    )
    assert dummy_function_google__calendar_create_event is not None
    return dummy_function_google__calendar_create_event


@pytest.fixture(scope="session")
def dummy_function_aipolabs_test__hello_world_nested_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__hello_world_nested_args = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST__HELLO_WORLD_NESTED_ARGS"
    )
    assert dummy_function_aipolabs_test__hello_world_nested_args is not None
    return dummy_function_aipolabs_test__hello_world_nested_args


@pytest.fixture(scope="session")
def dummy_function_aipolabs_test__hello_world_no_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__hello_world_no_args = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST__HELLO_WORLD_NO_ARGS"
    )
    assert dummy_function_aipolabs_test__hello_world_no_args is not None
    return dummy_function_aipolabs_test__hello_world_no_args


@pytest.fixture(scope="session")
def dummy_function_aipolabs_test__http_bearer__hello_world(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__http_bearer__hello_world = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST_HTTP_BEARER__HELLO_WORLD"
    )
    assert dummy_function_aipolabs_test__http_bearer__hello_world is not None
    return dummy_function_aipolabs_test__http_bearer__hello_world


@pytest.fixture(scope="session")
def dummy_function_aipolabs_test__hello_world_with_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__hello_world_with_args = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST__HELLO_WORLD_WITH_ARGS"
    )
    assert dummy_function_aipolabs_test__hello_world_with_args is not None
    return dummy_function_aipolabs_test__hello_world_with_args


@pytest.fixture(scope="module")
def db_session() -> Generator[Session, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        yield db_session
