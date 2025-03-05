import logging
import time
from collections.abc import Generator
from datetime import timedelta
from typing import cast
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

# override the rate limit to a high number for testing before importing aipolabs modules
with patch.dict("os.environ", {"SERVER_RATE_LIMIT_IP_PER_SECOND": "999"}):
    from aipolabs.common import utils
    from aipolabs.common.db import crud
    from aipolabs.common.db.sql_models import (
        Agent,
        App,
        Base,
        Function,
        LinkedAccount,
        Project,
        User,
    )
    from aipolabs.common.enums import SecurityScheme, Visibility
    from aipolabs.common.schemas.agent import AgentCreate
    from aipolabs.common.schemas.app_configurations import (
        AppConfigurationCreate,
        AppConfigurationPublic,
    )
    from aipolabs.common.schemas.security_scheme import (
        APIKeySchemeCredentials,
        OAuth2SchemeCredentials,
    )
    from aipolabs.common.schemas.user import UserCreate
    from aipolabs.server import config
    from aipolabs.server.main import app as fastapi_app
    from aipolabs.server.routes.auth import create_access_token
    from aipolabs.server.tests import helper

logger = logging.getLogger(__name__)

# call this one time for entire tests because it's slow and costs money (negligible) as it needs
# to generate embeddings using OpenAI for each app and function
dummy_apps_and_functions_to_be_inserted_into_db = helper.prepare_dummy_apps_and_functions()
GOOGLE_APP_NAME = "GOOGLE"
GITHUB_APP_NAME = "GITHUB"
AIPOLABS_TEST_APP_NAME = "AIPOLABS_TEST"


@pytest.fixture(scope="function")
def test_client() -> Generator[TestClient, None, None]:
    # disable following redirects for testing login
    # NOTE: need to set base_url to http://localhost because we set TrustedHostMiddleware in main.py
    with TestClient(fastapi_app, base_url="http://localhost", follow_redirects=False) as c:
        yield c


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        yield db_session


@pytest.fixture(scope="function", autouse=True)
def database_setup_and_cleanup(db_session: Session) -> Generator[None, None, None]:
    """
    Setup and cleanup the database for each test case.
    """
    # make sure we are connecting to the local db not the production db
    # TODO: it's part of the environment separation problem, need to properly set up failsafe prod isolation
    assert config.DB_HOST in ["localhost", "db"]

    # Use 'with' to manage the session context

    inspector = cast(Inspector, inspect(db_session.bind))

    # Check if all tables defined in models are created in the db
    for table in Base.metadata.tables.values():
        if not inspector.has_table(table.name):
            pytest.exit(f"Table {table} does not exist in the database.")

    # Go through all tables and make sure there are no records in the table
    # (skip alembic_version table)
    for table in Base.metadata.tables.values():
        if table.name != "alembic_version" and db_session.query(table).count() > 0:
            pytest.exit(f"Table {table} is not empty.")

    yield  # This allows the test to run

    # Clean up: Empty all tables after tests in reverse order of creation
    for table in reversed(Base.metadata.sorted_tables):
        if table.name != "alembic_version" and db_session.query(table).count() > 0:
            logger.debug(f"Deleting all records from table {table.name}")
            db_session.execute(table.delete())
    db_session.commit()


@pytest.fixture(scope="function")
def dummy_user(
    db_session: Session, database_setup_and_cleanup: None
) -> Generator[User, None, None]:
    dummy_user = crud.users.create_user(
        db_session,
        UserCreate(
            identity_provider="dummy_identity_provider",
            user_id_by_provider="dummy_user_id_by_provider",
            name="Dummy User",
            email="dummy@example.com",
        ),
    )
    db_session.commit()
    yield dummy_user


@pytest.fixture(scope="function")
def dummy_user_2(
    db_session: Session, database_setup_and_cleanup: None
) -> Generator[User, None, None]:
    dummy_user_2 = crud.users.create_user(
        db_session,
        UserCreate(
            identity_provider="dummy_identity_provider_2",
            user_id_by_provider="dummy_user_id_by_provider_2",
            name="Dummy User 2",
            email="dummy2@example.com",
        ),
    )
    db_session.commit()
    yield dummy_user_2


@pytest.fixture(scope="function")
def dummy_user_bearer_token(dummy_user: User) -> str:
    return create_access_token(str(dummy_user.id), timedelta(minutes=15))


@pytest.fixture(scope="function")
def dummy_user_2_bearer_token(dummy_user_2: User) -> str:
    return create_access_token(str(dummy_user_2.id), timedelta(minutes=15))


@pytest.fixture(scope="function")
def dummy_project_1(db_session: Session, dummy_user: User) -> Generator[Project, None, None]:
    dummy_project_1 = crud.projects.create_project(
        db_session,
        owner_id=dummy_user.id,
        name="Dummy Project",
        visibility_access=Visibility.PUBLIC,
    )
    db_session.commit()
    yield dummy_project_1


@pytest.fixture(scope="function")
def dummy_api_key_1(db_session: Session, dummy_project_1: Project) -> Generator[str, None, None]:
    dummy_agent = crud.projects.create_agent(
        db_session,
        project_id=dummy_project_1.id,
        name="Dummy Agent",
        description="Dummy Agent",
        excluded_apps=[],
        excluded_functions=[],
        custom_instructions={},
    )
    db_session.commit()
    yield dummy_agent.api_keys[0].key


@pytest.fixture(scope="function")
def dummy_project_2(db_session: Session, dummy_user_2: User) -> Generator[Project, None, None]:
    dummy_project_2 = crud.projects.create_project(
        db_session,
        owner_id=dummy_user_2.id,
        name="Dummy Project 2",
        visibility_access=Visibility.PUBLIC,
    )
    db_session.commit()
    yield dummy_project_2


@pytest.fixture(scope="function")
def dummy_api_key_2(db_session: Session, dummy_project_2: Project) -> Generator[str, None, None]:
    dummy_agent = crud.projects.create_agent(
        db_session,
        project_id=dummy_project_2.id,
        name="Dummy Agent 2",
        description="Dummy Agent 2",
        excluded_apps=[],
        excluded_functions=[],
        custom_instructions={},
    )
    db_session.commit()
    yield dummy_agent.api_keys[0].key


@pytest.fixture(scope="function")
def dummy_agent_1(db_session: Session, dummy_project_1: Project) -> Generator[Agent, None, None]:
    dummy_agent_1 = crud.projects.create_agent(
        db_session,
        project_id=dummy_project_1.id,
        name="Dummy Agent 1",
        description="Dummy Agent 1",
        excluded_apps=[],
        excluded_functions=[],
        custom_instructions={},
    )
    db_session.commit()
    yield dummy_agent_1


@pytest.fixture(scope="function")
def dummy_agent_with_github_apple_instructions(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_github: App,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
) -> Generator[Agent, None, None]:
    body = AgentCreate(
        name="Dummy Agent with GitHub Instructions",
        description="Agent with custom GitHub instructions",
        custom_instructions={
            dummy_app_github.name: "Don't create any repositories with the word apple in the name"
        },
    )
    dummy_agent = crud.projects.create_agent(
        db_session,
        project_id=dummy_project_1.id,
        name=body.name,
        description=body.description,
        excluded_apps=body.excluded_apps,
        excluded_functions=body.excluded_functions,
        custom_instructions=body.model_dump(mode="json")["custom_instructions"],
    )
    db_session.commit()
    yield dummy_agent


################################################################################
# Dummy Apps
################################################################################


@pytest.fixture(scope="function")
def dummy_apps(
    db_session: Session, database_setup_and_cleanup: None
) -> Generator[list[App], None, None]:
    dummy_apps: list[App] = []
    for (
        app_upsert,
        functions_upsert,
        app_embedding,
        functions_embeddings,
    ) in dummy_apps_and_functions_to_be_inserted_into_db:
        app = crud.apps.create_app(db_session, app_upsert, app_embedding)
        crud.functions.create_functions(db_session, functions_upsert, functions_embeddings)
        db_session.commit()
        dummy_apps.append(app)

    yield dummy_apps


@pytest.fixture(scope="function")
def dummy_app_google(dummy_apps: list[App]) -> App:
    dummy_app_google = next(app for app in dummy_apps if app.name == GOOGLE_APP_NAME)
    assert dummy_app_google is not None
    return dummy_app_google


@pytest.fixture(scope="function")
def dummy_app_github(dummy_apps: list[App]) -> App:
    dummy_app_github = next(app for app in dummy_apps if app.name == GITHUB_APP_NAME)
    assert dummy_app_github is not None
    return dummy_app_github


@pytest.fixture(scope="function")
def dummy_app_aipolabs_test(dummy_apps: list[App]) -> App:
    dummy_app_aipolabs_test = next(app for app in dummy_apps if app.name == AIPOLABS_TEST_APP_NAME)
    assert dummy_app_aipolabs_test is not None
    return dummy_app_aipolabs_test


################################################################################
# Dummy Functions
################################################################################


@pytest.fixture(scope="function")
def dummy_functions(dummy_apps: list[App]) -> list[Function]:
    dummy_functions: list[Function] = []
    for dummy_app in dummy_apps:
        dummy_functions.extend(dummy_app.functions)
    return dummy_functions


@pytest.fixture(scope="function")
def dummy_function_github__create_repository(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_github__create_repository = next(
        func for func in dummy_functions if func.name == "GITHUB__CREATE_REPOSITORY"
    )
    assert dummy_function_github__create_repository is not None
    return dummy_function_github__create_repository


@pytest.fixture(scope="function")
def dummy_function_google__calendar_create_event(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_google__calendar_create_event = next(
        func for func in dummy_functions if func.name == "GOOGLE__CALENDAR_CREATE_EVENT"
    )
    assert dummy_function_google__calendar_create_event is not None
    return dummy_function_google__calendar_create_event


@pytest.fixture(scope="function")
def dummy_function_aipolabs_test__hello_world_nested_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__hello_world_nested_args = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST__HELLO_WORLD_NESTED_ARGS"
    )
    assert dummy_function_aipolabs_test__hello_world_nested_args is not None
    return dummy_function_aipolabs_test__hello_world_nested_args


@pytest.fixture(scope="function")
def dummy_function_aipolabs_test__hello_world_no_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__hello_world_no_args = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST__HELLO_WORLD_NO_ARGS"
    )
    assert dummy_function_aipolabs_test__hello_world_no_args is not None
    return dummy_function_aipolabs_test__hello_world_no_args


@pytest.fixture(scope="function")
def dummy_function_aipolabs_test__hello_world_with_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aipolabs_test__hello_world_with_args = next(
        func for func in dummy_functions if func.name == "AIPOLABS_TEST__HELLO_WORLD_WITH_ARGS"
    )
    assert dummy_function_aipolabs_test__hello_world_with_args is not None
    return dummy_function_aipolabs_test__hello_world_with_args


################################################################################
# Dummy App Configurations
# Naming Convention: dummy_app_configuration_<security_scheme>_<app>_<project>
################################################################################


@pytest.fixture(scope="function")
def dummy_app_configuration_oauth2_google_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_google: App,
) -> AppConfigurationPublic:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_google.name, security_scheme=SecurityScheme.OAUTH2
    )
    dummy_app_configuration_oauth2_google_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()

    return dummy_app_configuration_oauth2_google_project_1


@pytest.fixture(scope="function")
def dummy_app_configuration_oauth2_google_project_2(
    db_session: Session,
    dummy_project_2: Project,
    dummy_app_google: App,
) -> AppConfigurationPublic:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_google.name, security_scheme=SecurityScheme.OAUTH2
    )

    dummy_app_configuration_oauth2_google_project_2 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_2.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_oauth2_google_project_2


@pytest.fixture(scope="function")
def dummy_app_configuration_api_key_github_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_github: App,
) -> AppConfigurationPublic:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_github.name, security_scheme=SecurityScheme.API_KEY
    )
    dummy_app_configuration_api_key_github_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_api_key_github_project_1


@pytest.fixture(scope="function")
def dummy_app_configuration_api_key_github_project_2(
    db_session: Session,
    dummy_project_2: Project,
    dummy_app_github: App,
) -> AppConfigurationPublic:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_github.name, security_scheme=SecurityScheme.API_KEY
    )
    dummy_app_configuration_api_key_github_project_2 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_2.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_api_key_github_project_2


@pytest.fixture(scope="function")
def dummy_app_configuration_api_key_aipolabs_test_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_aipolabs_test: App,
) -> AppConfigurationPublic:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_aipolabs_test.name, security_scheme=SecurityScheme.API_KEY
    )

    dummy_app_configuration_api_key_aipolabs_test_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_api_key_aipolabs_test_project_1


@pytest.fixture(scope="function")
def dummy_app_configuration_oauth2_aipolabs_test_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_aipolabs_test: App,
) -> AppConfigurationPublic:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_aipolabs_test.name, security_scheme=SecurityScheme.OAUTH2
    )

    dummy_app_configuration_oauth2_aipolabs_test_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_oauth2_aipolabs_test_project_1


################################################################################
# Dummy Linked Accounts Security Credentials
################################################################################
@pytest.fixture(scope="function")
def dummy_linked_account_api_key_credentials() -> APIKeySchemeCredentials:
    return APIKeySchemeCredentials(
        secret_key="dummy_linked_account_api_key_credentials_secret_key",
    )


@pytest.fixture(scope="function")
def dummy_linked_account_oauth2_credentials() -> OAuth2SchemeCredentials:
    return OAuth2SchemeCredentials(
        access_token="dummy_linked_account_oauth2_credentials_access_token",
        token_type="Bearer",
        expires_at=int(time.time()) + 3600,
        refresh_token="dummy_linked_account_oauth2_credentials_refresh_token",
    )


################################################################################
# Dummy Linked Accounts
# Naming Convention: dummy_linked_account_<security_scheme>_<app>_<project>
################################################################################


@pytest.fixture(scope="function")
def dummy_linked_account_oauth2_google_project_1(
    db_session: Session,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
    dummy_app_configuration_oauth2_google_project_1: AppConfigurationPublic,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_oauth2_google_project_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_configuration_oauth2_google_project_1.project_id,
        dummy_app_configuration_oauth2_google_project_1.app_name,
        "dummy_linked_account_oauth2_google_project_1",
        dummy_app_configuration_oauth2_google_project_1.security_scheme,
        dummy_linked_account_oauth2_credentials,
        enabled=True,
    )
    db_session.commit()
    yield dummy_linked_account_oauth2_google_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_api_key_github_project_1(
    db_session: Session,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    dummy_linked_account_api_key_credentials: APIKeySchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_api_key_github_project_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_configuration_api_key_github_project_1.project_id,
        dummy_app_configuration_api_key_github_project_1.app_name,
        "dummy_linked_account_api_key_github_project_1",
        dummy_app_configuration_api_key_github_project_1.security_scheme,
        dummy_linked_account_api_key_credentials,
        enabled=True,
    )
    db_session.commit()
    yield dummy_linked_account_api_key_github_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_oauth2_google_project_2(
    db_session: Session,
    dummy_app_configuration_oauth2_google_project_2: AppConfigurationPublic,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_oauth2_google_project_2 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_configuration_oauth2_google_project_2.project_id,
        dummy_app_configuration_oauth2_google_project_2.app_name,
        "dummy_linked_account_oauth2_google_project_2",
        dummy_app_configuration_oauth2_google_project_2.security_scheme,
        dummy_linked_account_oauth2_credentials,
        enabled=True,
    )
    db_session.commit()
    yield dummy_linked_account_oauth2_google_project_2


@pytest.fixture(scope="function")
def dummy_linked_account_api_key_aipolabs_test_project_1(
    db_session: Session,
    dummy_app_configuration_api_key_aipolabs_test_project_1: AppConfigurationPublic,
    dummy_linked_account_api_key_credentials: APIKeySchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_api_key_aipolabs_test_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_api_key_aipolabs_test_project_1.project_id,
            dummy_app_configuration_api_key_aipolabs_test_project_1.app_name,
            "dummy_linked_account_api_key_aipolabs_test_project_1",
            dummy_app_configuration_api_key_aipolabs_test_project_1.security_scheme,
            dummy_linked_account_api_key_credentials,
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_api_key_aipolabs_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_default_api_key_aipolabs_test_project_1(
    db_session: Session,
    dummy_app_configuration_api_key_aipolabs_test_project_1: AppConfigurationPublic,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_default_api_key_aipolabs_test_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_api_key_aipolabs_test_project_1.project_id,
            dummy_app_configuration_api_key_aipolabs_test_project_1.app_name,
            "dummy_linked_account_default_api_key_aipolabs_test_project_1",
            dummy_app_configuration_api_key_aipolabs_test_project_1.security_scheme,
            security_credentials=None,  # assign None to use the app's default security credentials
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_default_api_key_aipolabs_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_oauth2_aipolabs_test_project_1(
    db_session: Session,
    dummy_app_configuration_oauth2_aipolabs_test_project_1: AppConfigurationPublic,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_oauth2_aipolabs_test_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_oauth2_aipolabs_test_project_1.project_id,
            dummy_app_configuration_oauth2_aipolabs_test_project_1.app_name,
            "dummy_linked_account_oauth2_aipolabs_test_project_1",
            dummy_app_configuration_oauth2_aipolabs_test_project_1.security_scheme,
            dummy_linked_account_oauth2_credentials,
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_oauth2_aipolabs_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_default_aipolabs_test_project_1(
    db_session: Session,
    dummy_app_configuration_oauth2_aipolabs_test_project_1: AppConfigurationPublic,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_default_aipolabs_test_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_oauth2_aipolabs_test_project_1.project_id,
            dummy_app_configuration_oauth2_aipolabs_test_project_1.app_name,
            "dummy_linked_account_default_aipolabs_test_project_1",
            dummy_app_configuration_oauth2_aipolabs_test_project_1.security_scheme,
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_default_aipolabs_test_project_1
