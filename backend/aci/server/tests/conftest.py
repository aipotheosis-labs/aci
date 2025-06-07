import logging
import time
import uuid
from collections.abc import Generator
from dataclasses import dataclass
from typing import cast
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from propelauth_fastapi import User
from propelauth_py.types.login_method import SocialLoginProvider, SocialSsoLoginMethod
from propelauth_py.types.user import OrgMemberInfo
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from aci.common.db.sql_models import Plan
from aci.common.enums import OrganizationRole
from aci.common.schemas.plans import PlanFeatures
from aci.common.test_utils import clear_database, create_test_db_session
from aci.server import acl

# override the rate limit to a high number for testing before importing aci modules
with patch.dict("os.environ", {"SERVER_RATE_LIMIT_IP_PER_SECOND": "999"}):
    from aci.common.db import crud
    from aci.common.db.sql_models import (
        Agent,
        App,
        AppConfiguration,
        Base,
        Function,
        LinkedAccount,
        Project,
    )
    from aci.common.enums import SecurityScheme, Visibility
    from aci.common.schemas.app_configurations import (
        AppConfigurationCreate,
        AppConfigurationPublic,
    )
    from aci.common.schemas.security_scheme import (
        APIKeySchemeCredentials,
        NoAuthSchemeCredentials,
        OAuth2SchemeCredentials,
    )
    from aci.server.main import app as fastapi_app
    from aci.server.tests import helper

logger = logging.getLogger(__name__)

auth = acl.get_propelauth()

# call this one time for entire tests because it's slow and costs money (negligible) as it needs
# to generate embeddings using OpenAI for each app and function
dummy_apps_and_functions_to_be_inserted_into_db = helper.prepare_dummy_apps_and_functions()
GOOGLE_APP_NAME = "GOOGLE"
GITHUB_APP_NAME = "GITHUB"
ACI_TEST_APP_NAME = "ACI_TEST"
MOCK_APP_CONNECTOR_APP_NAME = "MOCK_APP_CONNECTOR"


@dataclass
class DummyUser:
    propel_auth_user: User
    access_token: str
    org_id: uuid.UUID


@pytest.fixture(scope="function")
def dummy_user(database_setup_and_cleanup: None) -> DummyUser:
    org_id = uuid.uuid4()
    return DummyUser(
        propel_auth_user=User(
            user_id="dummy_user",
            org_id_to_org_member_info={
                # NOTE: propelauth uses str for org_id, where as the Project model uses UUID
                str(org_id): OrgMemberInfo(
                    org_id=str(org_id),
                    org_name="dummy_org",
                    user_assigned_role=OrganizationRole.OWNER,
                    org_metadata={},
                    user_inherited_roles_plus_current_role=[
                        OrganizationRole.OWNER,
                        OrganizationRole.ADMIN,
                        OrganizationRole.MEMBER,
                    ],
                    user_permissions=[],
                ),
            },
            email="dummy_user@example.com",
            login_method=SocialSsoLoginMethod(
                provider=SocialLoginProvider.GOOGLE,
            ),
        ),
        access_token="dummy_access_token",
        org_id=org_id,
    )


@pytest.fixture(scope="function")
def dummy_user_2(database_setup_and_cleanup: None) -> DummyUser:
    return DummyUser(
        propel_auth_user=User(
            user_id="dummy_user_2",
            org_id_to_org_member_info={},
            email="dummy_user_2@example.com",
            login_method=SocialSsoLoginMethod(
                provider=SocialLoginProvider.GOOGLE,
            ),
        ),
        access_token="dummy_access_token_2",
        org_id=uuid.uuid4(),
    )


@pytest.fixture(scope="function")
def test_client(dummy_user: DummyUser) -> Generator[TestClient, None, None]:
    fastapi_app.dependency_overrides[auth.require_user] = lambda: dummy_user.propel_auth_user
    # disable following redirects for testing login
    # NOTE: need to set base_url to http://localhost because we set TrustedHostMiddleware in main.py
    with TestClient(fastapi_app, base_url="http://localhost", follow_redirects=False) as c:
        yield c


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    yield from create_test_db_session()


@pytest.fixture(scope="function", autouse=True)
def database_setup_and_cleanup(db_session: Session) -> Generator[None, None, None]:
    """
    Setup and cleanup the database for each test case.
    """
    inspector = cast(Inspector, inspect(db_session.bind))

    # Check if all tables defined in models are created in the db
    for table in Base.metadata.tables.values():
        if not inspector.has_table(table.name):
            pytest.exit(f"Table {table} does not exist in the database.")

    clear_database(db_session)
    yield  # This allows the test to run
    clear_database(db_session)


@pytest.fixture(scope="function")
def dummy_project_1(db_session: Session, dummy_user: DummyUser) -> Generator[Project, None, None]:
    dummy_project_1 = crud.projects.create_project(
        db_session,
        org_id=dummy_user.org_id,
        name="Dummy Project",
        visibility_access=Visibility.PUBLIC,
    )
    db_session.commit()
    yield dummy_project_1


@pytest.fixture(scope="function")
def dummy_api_key_1(dummy_agent_1_with_no_apps_allowed: Agent) -> Generator[str, None, None]:
    yield dummy_agent_1_with_no_apps_allowed.api_keys[0].key


@pytest.fixture(scope="function")
def dummy_project_2(db_session: Session, dummy_user: DummyUser) -> Generator[Project, None, None]:
    dummy_project_2 = crud.projects.create_project(
        db_session,
        org_id=dummy_user.org_id,
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
        allowed_apps=[],
        custom_instructions={},
    )
    db_session.commit()
    yield dummy_agent.api_keys[0].key


@pytest.fixture(scope="function")
def dummy_agent_1_with_no_apps_allowed(
    db_session: Session, dummy_project_1: Project
) -> Generator[Agent, None, None]:
    dummy_agent_1_with_no_apps_allowed = crud.projects.create_agent(
        db_session,
        project_id=dummy_project_1.id,
        name="Dummy Agent 1",
        description="Dummy Agent 1",
        allowed_apps=[],
        custom_instructions={},
    )
    db_session.commit()
    yield dummy_agent_1_with_no_apps_allowed


@pytest.fixture(scope="function")
def dummy_agent_1_with_all_apps_allowed(
    db_session: Session, dummy_agent_1_with_no_apps_allowed: Agent, dummy_apps: list[App]
) -> Generator[Agent, None, None]:
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [app.name for app in dummy_apps]
    db_session.commit()
    yield dummy_agent_1_with_no_apps_allowed


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
def dummy_app_aci_test(dummy_apps: list[App]) -> App:
    dummy_app_aci_test = next(app for app in dummy_apps if app.name == ACI_TEST_APP_NAME)
    assert dummy_app_aci_test is not None
    return dummy_app_aci_test


@pytest.fixture(scope="function")
def dummy_app_mock_app_connector(dummy_apps: list[App]) -> App:
    dummy_app_mock_app_connector = next(
        app for app in dummy_apps if app.name == MOCK_APP_CONNECTOR_APP_NAME
    )
    assert dummy_app_mock_app_connector is not None
    return dummy_app_mock_app_connector


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
def dummy_function_aci_test__hello_world_nested_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aci_test__hello_world_nested_args = next(
        func for func in dummy_functions if func.name == "ACI_TEST__HELLO_WORLD_NESTED_ARGS"
    )
    assert dummy_function_aci_test__hello_world_nested_args is not None
    return dummy_function_aci_test__hello_world_nested_args


@pytest.fixture(scope="function")
def dummy_function_aci_test__hello_world_no_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aci_test__hello_world_no_args = next(
        func for func in dummy_functions if func.name == "ACI_TEST__HELLO_WORLD_NO_ARGS"
    )
    assert dummy_function_aci_test__hello_world_no_args is not None
    return dummy_function_aci_test__hello_world_no_args


@pytest.fixture(scope="function")
def dummy_function_aci_test__hello_world_with_args(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_aci_test__hello_world_with_args = next(
        func for func in dummy_functions if func.name == "ACI_TEST__HELLO_WORLD_WITH_ARGS"
    )
    assert dummy_function_aci_test__hello_world_with_args is not None
    return dummy_function_aci_test__hello_world_with_args


@pytest.fixture(scope="function")
def dummy_function_mock_app_connector__echo(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_mock_app_connector__echo = next(
        func for func in dummy_functions if func.name == "MOCK_APP_CONNECTOR__ECHO"
    )
    assert dummy_function_mock_app_connector__echo is not None
    return dummy_function_mock_app_connector__echo


@pytest.fixture(scope="function")
def dummy_function_mock_app_connector__fail(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_mock_app_connector__fail = next(
        func for func in dummy_functions if func.name == "MOCK_APP_CONNECTOR__FAIL"
    )
    assert dummy_function_mock_app_connector__fail is not None
    return dummy_function_mock_app_connector__fail


################################################################################
# Dummy App Configurations
# Naming Convention: dummy_app_configuration_<security_scheme>_<app>_<project>
################################################################################


@pytest.fixture(scope="function")
def dummy_app_configuration_oauth2_google_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_google: App,
) -> AppConfiguration:
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
) -> AppConfiguration:
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
) -> AppConfiguration:
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
) -> AppConfiguration:
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
def dummy_app_configuration_api_key_aci_test_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_aci_test: App,
) -> AppConfiguration:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_aci_test.name, security_scheme=SecurityScheme.API_KEY
    )

    dummy_app_configuration_api_key_aci_test_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_api_key_aci_test_project_1


@pytest.fixture(scope="function")
def dummy_app_configuration_oauth2_aci_test_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_aci_test: App,
) -> AppConfiguration:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_aci_test.name, security_scheme=SecurityScheme.OAUTH2
    )

    dummy_app_configuration_oauth2_aci_test_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_oauth2_aci_test_project_1


@pytest.fixture(scope="function")
def dummy_app_configuration_oauth2_mock_app_connector_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_mock_app_connector: App,
) -> AppConfiguration:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_mock_app_connector.name, security_scheme=SecurityScheme.OAUTH2
    )
    dummy_app_configuration_oauth2_mock_app_connector_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_oauth2_mock_app_connector_project_1


@pytest.fixture(scope="function")
def dummy_app_configuration_no_auth_mock_app_connector_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_mock_app_connector: App,
) -> AppConfiguration:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_mock_app_connector.name, security_scheme=SecurityScheme.NO_AUTH
    )
    dummy_app_configuration_no_auth_mock_app_connector_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_no_auth_mock_app_connector_project_1


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
        client_id="dummy_linked_account_oauth2_credentials_client_id",
        client_secret="dummy_linked_account_oauth2_credentials_client_secret",
        scope="dummy_scope_1 dummy_scope_2",
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
def dummy_linked_account_api_key_aci_test_project_1(
    db_session: Session,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfigurationPublic,
    dummy_linked_account_api_key_credentials: APIKeySchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_api_key_aci_test_project_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_configuration_api_key_aci_test_project_1.project_id,
        dummy_app_configuration_api_key_aci_test_project_1.app_name,
        "dummy_linked_account_api_key_aci_test_project_1",
        dummy_app_configuration_api_key_aci_test_project_1.security_scheme,
        dummy_linked_account_api_key_credentials,
        enabled=True,
    )
    db_session.commit()
    yield dummy_linked_account_api_key_aci_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_default_api_key_aci_test_project_1(
    db_session: Session,
    dummy_app_configuration_api_key_aci_test_project_1: AppConfigurationPublic,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_default_api_key_aci_test_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_api_key_aci_test_project_1.project_id,
            dummy_app_configuration_api_key_aci_test_project_1.app_name,
            "dummy_linked_account_default_api_key_aci_test_project_1",
            dummy_app_configuration_api_key_aci_test_project_1.security_scheme,
            security_credentials=None,  # assign None to use the app's default security credentials
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_default_api_key_aci_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_oauth2_aci_test_project_1(
    db_session: Session,
    dummy_app_configuration_oauth2_aci_test_project_1: AppConfigurationPublic,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_oauth2_aci_test_project_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_configuration_oauth2_aci_test_project_1.project_id,
        dummy_app_configuration_oauth2_aci_test_project_1.app_name,
        "dummy_linked_account_oauth2_aci_test_project_1",
        dummy_app_configuration_oauth2_aci_test_project_1.security_scheme,
        dummy_linked_account_oauth2_credentials,
        enabled=True,
    )
    db_session.commit()
    yield dummy_linked_account_oauth2_aci_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_default_aci_test_project_1(
    db_session: Session,
    dummy_app_configuration_oauth2_aci_test_project_1: AppConfigurationPublic,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_default_aci_test_project_1 = crud.linked_accounts.create_linked_account(
        db_session,
        dummy_app_configuration_oauth2_aci_test_project_1.project_id,
        dummy_app_configuration_oauth2_aci_test_project_1.app_name,
        "dummy_linked_account_default_aci_test_project_1",
        dummy_app_configuration_oauth2_aci_test_project_1.security_scheme,
        enabled=True,
    )
    db_session.commit()
    yield dummy_linked_account_default_aci_test_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_oauth2_mock_app_connector_project_1(
    db_session: Session,
    dummy_app_configuration_oauth2_mock_app_connector_project_1: AppConfigurationPublic,
    dummy_linked_account_oauth2_credentials: OAuth2SchemeCredentials,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_oauth2_mock_app_connector_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_oauth2_mock_app_connector_project_1.project_id,
            dummy_app_configuration_oauth2_mock_app_connector_project_1.app_name,
            "dummy_linked_account_oauth2_mock_app_connector_project_1",
            dummy_app_configuration_oauth2_mock_app_connector_project_1.security_scheme,
            dummy_linked_account_oauth2_credentials,
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_oauth2_mock_app_connector_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_no_auth_mock_app_connector_project_1(
    db_session: Session,
    dummy_app_configuration_no_auth_mock_app_connector_project_1: AppConfigurationPublic,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_no_auth_mock_app_connector_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_no_auth_mock_app_connector_project_1.project_id,
            dummy_app_configuration_no_auth_mock_app_connector_project_1.app_name,
            "dummy_linked_account_no_auth_mock_app_connector_project_1",
            dummy_app_configuration_no_auth_mock_app_connector_project_1.security_scheme,
            NoAuthSchemeCredentials(),
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_no_auth_mock_app_connector_project_1


@pytest.fixture(scope="function", autouse=True)
def free_plan(db_session: Session) -> Plan:
    plan = crud.plans.create(
        db=db_session,
        name="free",
        stripe_product_id="prod_FREE_placeholder",
        stripe_monthly_price_id="price_FREE_monthly_placeholder",
        stripe_yearly_price_id="price_FREE_yearly_placeholder",
        features=PlanFeatures(
            linked_accounts=3,
            api_calls_monthly=1000,
            agent_credentials=5,
            developer_seats=1,
            custom_oauth=False,
            log_retention_days=7,
            projects=1,
        ),
        is_public=True,
    )
    db_session.commit()
    return plan
