from collections.abc import Generator

import pytest
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import (
    App,
    AppConfiguration,
    Function,
    LinkedAccount,
    Project,
    SecurityScheme,
)
from aci.common.schemas.app_configurations import (
    AppConfigurationCreate,
    AppConfigurationPublic,
)
from aci.common.schemas.security_scheme import NoAuthSchemeCredentials

AGENT_SECRETS_MANAGER_APP_NAME = "AGENT_SECRETS_MANAGER"


@pytest.fixture(scope="function")
def dummy_app_agent_secrets_manager(dummy_apps: list[App]) -> App:
    dummy_app_agent_secrets_manager = next(
        app for app in dummy_apps if app.name == AGENT_SECRETS_MANAGER_APP_NAME
    )
    assert dummy_app_agent_secrets_manager is not None
    return dummy_app_agent_secrets_manager


@pytest.fixture(scope="function")
def dummy_function_agent_secrets_manager__list_credentials(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_agent_secrets_manager__list_credentials = next(
        func for func in dummy_functions if func.name == "AGENT_SECRETS_MANAGER__LIST_CREDENTIALS"
    )
    assert dummy_function_agent_secrets_manager__list_credentials is not None
    return dummy_function_agent_secrets_manager__list_credentials


@pytest.fixture(scope="function")
def dummy_function_agent_secrets_manager__get_credential_for_domain(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_agent_secrets_manager__get_credential_for_domain = next(
        func
        for func in dummy_functions
        if func.name == "AGENT_SECRETS_MANAGER__GET_CREDENTIAL_FOR_DOMAIN"
    )
    assert dummy_function_agent_secrets_manager__get_credential_for_domain is not None
    return dummy_function_agent_secrets_manager__get_credential_for_domain


@pytest.fixture(scope="function")
def dummy_function_agent_secrets_manager__create_credential_for_domain(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_agent_secrets_manager__create_credential_for_domain = next(
        func
        for func in dummy_functions
        if func.name == "AGENT_SECRETS_MANAGER__CREATE_CREDENTIAL_FOR_DOMAIN"
    )
    assert dummy_function_agent_secrets_manager__create_credential_for_domain is not None
    return dummy_function_agent_secrets_manager__create_credential_for_domain


@pytest.fixture(scope="function")
def dummy_function_agent_secrets_manager__update_credential_for_domain(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_agent_secrets_manager__update_credential_for_domain = next(
        func
        for func in dummy_functions
        if func.name == "AGENT_SECRETS_MANAGER__UPDATE_CREDENTIAL_FOR_DOMAIN"
    )
    assert dummy_function_agent_secrets_manager__update_credential_for_domain is not None
    return dummy_function_agent_secrets_manager__update_credential_for_domain


@pytest.fixture(scope="function")
def dummy_function_agent_secrets_manager__delete_credential_for_domain(
    dummy_functions: list[Function],
) -> Function:
    dummy_function_agent_secrets_manager__delete_credential_for_domain = next(
        func
        for func in dummy_functions
        if func.name == "AGENT_SECRETS_MANAGER__DELETE_CREDENTIAL_FOR_DOMAIN"
    )
    assert dummy_function_agent_secrets_manager__delete_credential_for_domain is not None
    return dummy_function_agent_secrets_manager__delete_credential_for_domain


@pytest.fixture(scope="function")
def dummy_app_configuration_no_auth_agent_secrets_manager_project_1(
    db_session: Session,
    dummy_project_1: Project,
    dummy_app_agent_secrets_manager: App,
) -> AppConfiguration:
    app_configuration_create = AppConfigurationCreate(
        app_name=dummy_app_agent_secrets_manager.name, security_scheme=SecurityScheme.NO_AUTH
    )
    dummy_app_configuration_no_auth_agent_secrets_manager_project_1 = (
        crud.app_configurations.create_app_configuration(
            db_session,
            dummy_project_1.id,
            app_configuration_create,
        )
    )
    db_session.commit()
    return dummy_app_configuration_no_auth_agent_secrets_manager_project_1


@pytest.fixture(scope="function")
def dummy_linked_account_no_auth_agent_secrets_manager_project_1(
    db_session: Session,
    dummy_app_configuration_no_auth_agent_secrets_manager_project_1: AppConfigurationPublic,
) -> Generator[LinkedAccount, None, None]:
    dummy_linked_account_no_auth_agent_secrets_manager_project_1 = (
        crud.linked_accounts.create_linked_account(
            db_session,
            dummy_app_configuration_no_auth_agent_secrets_manager_project_1.project_id,
            dummy_app_configuration_no_auth_agent_secrets_manager_project_1.app_name,
            "dummy_linked_account_no_auth_agent_secrets_manager_project_1",
            dummy_app_configuration_no_auth_agent_secrets_manager_project_1.security_scheme,
            NoAuthSchemeCredentials(),
            enabled=True,
        )
    )
    db_session.commit()
    yield dummy_linked_account_no_auth_agent_secrets_manager_project_1
