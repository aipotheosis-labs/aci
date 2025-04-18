import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from aci.common.db import crud
from aci.common.db.sql_models import Agent, App, Function, Project
from aci.common.enums import FunctionDefinitionFormat, Visibility
from aci.common.schemas.app_configurations import AppConfigurationPublic
from aci.common.schemas.function import (
    AnthropicFunctionDefinition,
    BasicFunctionDefinition,
    FunctionsSearch,
    OpenAIFunctionDefinition,
)
from aci.server import config


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_inactive_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    # inactive functions should not be returned
    crud.functions.set_function_active_status(db_session, dummy_functions[0].name, False)
    db_session.commit()

    function_search = FunctionsSearch(format=format)

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]

    assert len(functions) == len(dummy_functions) - 1


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_inactive_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    # all functions (active or not) under inactive apps should not be returned
    crud.apps.set_app_active_status(db_session, dummy_functions[0].app.name, False)
    db_session.commit()

    function_search = FunctionsSearch(format=format)

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]

    inactive_functions_count = sum(
        function.app.name == dummy_functions[0].app.name for function in dummy_functions
    )
    assert inactive_functions_count > 0, "there should be at least one inactive function"
    assert len(functions) == len(dummy_functions) - inactive_functions_count, (
        "no functions should be returned under inactive apps"
    )


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_private_functions(
    db_session: Session,
    test_client: TestClient,
    dummy_project_1: Project,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    # private functions should not be reachable for project with only public access
    crud.functions.set_function_visibility(db_session, dummy_functions[0].name, Visibility.PRIVATE)
    db_session.commit()

    function_search = FunctionsSearch(format=format)
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]

    # private functions should be reachable for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]

    assert len(functions) == len(dummy_functions)


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_private_apps(
    db_session: Session,
    test_client: TestClient,
    dummy_project_1: Project,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    # all functions (public and private) under private apps should not be
    # reachable for project with only public access
    crud.apps.set_app_visibility(db_session, dummy_functions[0].app.name, Visibility.PRIVATE)
    db_session.commit()

    function_search = FunctionsSearch(format=format)
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]

    private_functions_count = sum(
        function.app.name == dummy_functions[0].app.name for function in dummy_functions
    )
    assert private_functions_count > 0, "there should be at least one private function"
    assert len(functions) == len(dummy_functions) - private_functions_count, (
        "all functions under private apps should not be returned"
    )

    # all functions (public and private) under private apps should be reachable
    # for project with private access
    crud.projects.set_project_visibility_access(db_session, dummy_project_1.id, Visibility.PRIVATE)
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_app_names(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    function_search = FunctionsSearch(
        app_names=[dummy_functions[0].app.name, dummy_functions[1].app.name],
        limit=100,
        offset=0,
        format=format,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    # only functions from the given app ids should be returned
    for function in functions:
        function_name = _get_function_name_from_definition(function)
        assert function_name.startswith(dummy_functions[0].app.name) or function_name.startswith(
            dummy_functions[1].app.name
        )
    # total number of functions should be the sum of functions from the given app ids
    assert len(functions) == sum(
        function.app.name in [dummy_functions[0].app.name, dummy_functions[1].app.name]
        for function in dummy_functions
    )


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_intent(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_function_github__create_repository: Function,
    dummy_function_google__calendar_create_event: Function,
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    # intent1: create repo
    function_search = FunctionsSearch(
        intent="i want to create a new code repo for my project",
        limit=100,
        offset=0,
        format=format,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)
    function_name = _get_function_name_from_definition(functions[0])
    assert function_name == dummy_function_github__create_repository.name

    # intent2: upload file
    function_search.intent = "add this meeting to my calendar"

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions)
    function_name = _get_function_name_from_definition(functions[0])
    assert function_name == dummy_function_google__calendar_create_event.name


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_app_names_and_intent(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    dummy_app_github: App,
    format: FunctionDefinitionFormat,
) -> None:
    function_search = FunctionsSearch(
        app_names=[dummy_app_github.name],
        intent="i want to create a new code repo for my project",
        limit=100,
        offset=0,
        format=format,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )

    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    # only functions from the given app ids should be returned
    for function in functions:
        function_name = _get_function_name_from_definition(function)
        assert function_name.startswith(dummy_app_github.name)
    # total number of functions should be the sum of functions from the given app ids
    assert len(functions) == sum(
        function.app.name == dummy_app_github.name for function in dummy_functions
    )


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_pagination(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_api_key_1: str,
    format: FunctionDefinitionFormat,
) -> None:
    assert len(dummy_functions) > 2

    function_search = FunctionsSearch(
        limit=len(dummy_functions) - 1,
        offset=0,
        format=format,
    )

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions) - 1

    function_search.offset = len(dummy_functions) - 1

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_api_key_1},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == 1


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_allowed_apps_only_true(
    db_session: Session,
    test_client: TestClient,
    dummy_app_configuration_oauth2_aci_test_project_1: AppConfigurationPublic,
    dummy_app_aci_test: App,
    dummy_agent_1_with_no_apps_allowed: Agent,
    format: FunctionDefinitionFormat,
) -> None:
    function_search = FunctionsSearch(
        allowed_apps_only=True,
        format=format,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == 0, (
        "no functions should be returned because the agent is not allowed to access any app"
    )

    # update the agent to allow access to the app
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [dummy_app_aci_test.name]
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_app_aci_test.functions), (
        "should return all functions from the allowed app"
    )
    dummy_app_function_names = [function.name for function in dummy_app_aci_test.functions]
    for function in functions:
        function_name = _get_function_name_from_definition(function)
        assert function_name in dummy_app_function_names


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_allowed_apps_only_false(
    test_client: TestClient,
    dummy_functions: list[Function],
    dummy_agent_1_with_no_apps_allowed: Agent,
    format: FunctionDefinitionFormat,
) -> None:
    function_search = FunctionsSearch(
        allowed_apps_only=False,
        format=format,
    )
    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_functions), (
        "should return all functions because allowed_apps_only is False"
    )


@pytest.mark.parametrize(
    "format",
    [
        FunctionDefinitionFormat.BASIC,
        FunctionDefinitionFormat.OPENAI,
        FunctionDefinitionFormat.ANTHROPIC,
    ],
)
def test_search_functions_with_app_names_and_allowed_apps_only(
    db_session: Session,
    test_client: TestClient,
    dummy_app_configuration_api_key_github_project_1: AppConfigurationPublic,
    dummy_app_github: App,
    dummy_app_google: App,
    dummy_agent_1_with_no_apps_allowed: Agent,
    format: FunctionDefinitionFormat,
) -> None:
    # set the agent to allow access to one of the apps
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [dummy_app_github.name]
    db_session.commit()

    function_search = FunctionsSearch(
        app_names=[dummy_app_github.name, dummy_app_google.name],
        allowed_apps_only=True,
        format=format,
    )

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_app_github.functions), (
        "should only return functions from the allowed app"
    )
    dummy_app_github_function_names = [function.name for function in dummy_app_github.functions]
    for function in functions:
        function_name = _get_function_name_from_definition(function)
        assert function_name in dummy_app_github_function_names, (
            "returned functions should be from the allowed app"
        )

    # set the agent to allow access to both apps
    dummy_agent_1_with_no_apps_allowed.allowed_apps = [dummy_app_github.name, dummy_app_google.name]
    db_session.commit()

    response = test_client.get(
        f"{config.ROUTER_PREFIX_FUNCTIONS}/search",
        params=function_search.model_dump(exclude_none=True),
        headers={"x-api-key": dummy_agent_1_with_no_apps_allowed.api_keys[0].key},
    )
    assert response.status_code == status.HTTP_200_OK
    functions = [
        _validate_function_definition(response_function, format)
        for response_function in response.json()
    ]
    assert len(functions) == len(dummy_app_google.functions) + len(dummy_app_github.functions), (
        "should return functions from both allowed apps"
    )


def _validate_function_definition(
    function: dict, format: FunctionDefinitionFormat
) -> BasicFunctionDefinition | OpenAIFunctionDefinition | AnthropicFunctionDefinition:
    match format:
        case FunctionDefinitionFormat.BASIC:
            return BasicFunctionDefinition.model_validate(function)
        case FunctionDefinitionFormat.OPENAI:
            return OpenAIFunctionDefinition.model_validate(function)
        case FunctionDefinitionFormat.ANTHROPIC:
            return AnthropicFunctionDefinition.model_validate(function)
        case _:
            raise AssertionError(f"Invalid format: {format}")


def _get_function_name_from_definition(
    function_definition: BasicFunctionDefinition
    | OpenAIFunctionDefinition
    | AnthropicFunctionDefinition,
) -> str:
    match function_definition:
        case BasicFunctionDefinition():
            return function_definition.name
        case OpenAIFunctionDefinition():
            return function_definition.function.name
        case AnthropicFunctionDefinition():
            return function_definition.name
        case _:
            raise AssertionError(f"Invalid function definition: {function_definition}")
