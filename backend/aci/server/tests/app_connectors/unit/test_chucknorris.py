import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from respx import MockRouter

from aci.common.db.sql_models import App as DBApp, Function as DBFunction, LinkedAccount as DBLinkedAccount, Project as DBProject
from aci.common.schemas import function as func_schema
from aci.common.schemas.app import AppCategory
from aci.common.schemas.function import FunctionExecutionResult, FunctionInputRequiredInvisible, FunctionParameterValue, FunctionProtocolDataREST, Visibility
from aci.common.schemas.security_scheme import NoAuthScheme, NoAuthSchemeCredentials
from aci.server.function_executors.rest_function_executor import RestFunctionExecutor
from aci.server.app_connectors.base import AppConnector # For type hinting if needed


# --- Fixtures ---

@pytest.fixture
def mock_project() -> DBProject:
    project = MagicMock(spec=DBProject)
    project.id = uuid4()
    project.org_id = uuid4()
    project.name = "Test Project"
    return project

@pytest.fixture
def mock_linked_account(mock_project: DBProject) -> DBLinkedAccount:
    linked_account = MagicMock(spec=DBLinkedAccount)
    linked_account.id = uuid4()
    linked_account.project_id = mock_project.id
    linked_account.project = mock_project
    linked_account.app_name = "CHUCKNORRIS"
    # linked_account_owner_id is a string, not UUID
    linked_account.linked_account_owner_id = f"owner_{uuid4().hex}" 
    linked_account.security_credentials_stored = True # Assuming NoAuth means creds are "stored"
    return linked_account

@pytest.fixture
def chucknorris_app_db() -> DBApp:
    app = MagicMock(spec=DBApp)
    app.name = "CHUCKNORRIS"
    app.display_name = "Chuck Norris Jokes"
    app.logo = "https://api.chucknorris.io/img/avatar/chuck-norris.png"
    app.provider = "chucknorris.io"
    app.version = "1.0.0"
    app.description = "Provides a random Chuck Norris joke."
    app.security_schemes = {"no_auth": NoAuthScheme()}
    app.default_security_credentials_by_scheme = {}
    app.categories = [AppCategory.ENTERTAINMENT]
    app.visibility = Visibility.PUBLIC
    app.active = True
    return app

@pytest.fixture
def no_auth_scheme() -> NoAuthScheme:
    return NoAuthScheme()

@pytest.fixture
def no_auth_credentials() -> NoAuthSchemeCredentials:
    return NoAuthSchemeCredentials()

@pytest.fixture
def get_random_joke_function_db(chucknorris_app_db: DBApp) -> DBFunction:
    func = MagicMock(spec=DBFunction)
    func.name = "CHUCKNORRIS__GET_RANDOM_JOKE"
    func.app_name = chucknorris_app_db.name
    func.app = chucknorris_app_db
    func.description = "Retrieves a random Chuck Norris joke."
    func.tags = ["jokes", "entertainment"]
    func.visibility = Visibility.PUBLIC
    func.active = True
    func.protocol = func_schema.Protocol.REST
    func.protocol_data = FunctionProtocolDataREST(
        method="GET",
        path="/jokes/random",
        server_url="https://api.chucknorris.io"
    )
    # Parameters from functions.json (simplified for this fixture)
    func.parameters = {
        "type": "object",
        "properties": {
            "header": {
                "type": "object",
                "properties": {
                    "Accept": {
                        "type": "string",
                        "default": "application/json"
                    }
                }
            }
        }
    }
    func.response_schema = None # Assuming no strict response schema validation for now
    return func


@pytest.fixture
def get_random_joke_from_category_function_db(chucknorris_app_db: DBApp) -> DBFunction:
    func = MagicMock(spec=DBFunction)
    func.name = "CHUCKNORRIS__GET_RANDOM_JOKE_FROM_CATEGORY"
    func.app_name = chucknorris_app_db.name
    func.app = chucknorris_app_db
    func.description = "Retrieves a random Chuck Norris joke from a given category."
    func.tags = ["jokes", "entertainment", "category"]
    func.visibility = Visibility.PUBLIC
    func.active = True
    func.protocol = func_schema.Protocol.REST
    func.protocol_data = FunctionProtocolDataREST(
        method="GET",
        path="/jokes/random", # Same path, but will have query param
        server_url="https://api.chucknorris.io"
    )
    func.parameters = { # From functions.json
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "The category to get a random joke from."
                    }
                },
                "required": ["category"]
            },
            "header": {
                "type": "object",
                "properties": {
                    "Accept": {
                        "type": "string",
                        "default": "application/json"
                    }
                }
            }
        },
        "required": ["query"]
    }
    func.response_schema = None
    return func

# --- Tests ---

@pytest.mark.asyncio
async def test_get_random_joke(
    respx_router: MockRouter,
    mock_linked_account: DBLinkedAccount,
    get_random_joke_function_db: DBFunction,
    no_auth_scheme: NoAuthScheme,
    no_auth_credentials: NoAuthSchemeCredentials,
):
    # Arrange
    executor = RestFunctionExecutor(
        linked_account=mock_linked_account,
        app=get_random_joke_function_db.app, # type: ignore
        function=get_random_joke_function_db, # type: ignore
        security_scheme=no_auth_scheme,
        security_credentials=no_auth_credentials,
        db_session=MagicMock(), # Not used by REST executor for basic GET
    )

    mock_api_response = {
        "icon_url": "https://assets.chucknorris.host/img/avatar/chuck-norris.png",
        "id": "some_joke_id",
        "url": "http://example.com/joke_id",
        "value": "Chuck Norris can unit test entire applications with a single assert."
    }

    respx_router.get("https://api.chucknorris.io/jokes/random").mock(return_value=MagicMock(
        status_code=200,
        json=lambda: mock_api_response
    ))

    function_input_params = FunctionInputRequiredInvisible(
        # Default Accept header will be used by the executor
    )

    # Act
    result: FunctionExecutionResult = await executor.execute(input_params=function_input_params)

    # Assert
    assert result.success
    assert result.data == mock_api_response
    assert respx_router.calls.call_count == 1
    call = respx_router.calls.last
    assert call is not None
    assert str(call.request.url) == "https://api.chucknorris.io/jokes/random"
    assert call.request.headers["accept"] == "application/json"

# Placeholder for other tests
@pytest.mark.asyncio
async def test_get_random_joke_from_category(
    respx_router: MockRouter,
    mock_linked_account: DBLinkedAccount,
    get_random_joke_from_category_function_db: DBFunction,
    no_auth_scheme: NoAuthScheme,
    no_auth_credentials: NoAuthSchemeCredentials,
):
    # Arrange
    executor = RestFunctionExecutor(
        linked_account=mock_linked_account,
        app=get_random_joke_from_category_function_db.app, # type: ignore
        function=get_random_joke_from_category_function_db, # type: ignore
        security_scheme=no_auth_scheme,
        security_credentials=no_auth_credentials,
        db_session=MagicMock(),
    )

    category_to_test = "dev"
    mock_api_response = {
        "icon_url": "https://assets.chucknorris.host/img/avatar/chuck-norris.png",
        "id": "dev_joke_id",
        "url": f"http://example.com/joke_id?category={category_to_test}",
        "value": f"Chuck Norris writes code that writes itself. And it's always category: {category_to_test}."
    }

    respx_router.get(
        "https://api.chucknorris.io/jokes/random",
        params={"category": category_to_test}
    ).mock(return_value=MagicMock(
        status_code=200,
        json=lambda: mock_api_response
    ))

    function_input_params = FunctionInputRequiredInvisible(
        query=FunctionParameterValue(value={"category": category_to_test})
    )

    # Act
    result: FunctionExecutionResult = await executor.execute(input_params=function_input_params)

    # Assert
    assert result.success
    assert result.data == mock_api_response
    assert respx_router.calls.call_count == 1
    call = respx_router.calls.last
    assert call is not None
    assert str(call.request.url) == f"https://api.chucknorris.io/jokes/random?category={category_to_test}"
    assert call.request.headers["accept"] == "application/json"

@pytest.fixture
def get_categories_function_db(chucknorris_app_db: DBApp) -> DBFunction:
    func = MagicMock(spec=DBFunction)
    func.name = "CHUCKNORRIS__GET_CATEGORIES"
    func.app_name = chucknorris_app_db.name
    func.app = chucknorris_app_db
    func.description = "Retrieves a list of available joke categories."
    func.tags = ["jokes", "entertainment", "category"]
    func.visibility = Visibility.PUBLIC
    func.active = True
    func.protocol = func_schema.Protocol.REST
    func.protocol_data = FunctionProtocolDataREST(
        method="GET",
        path="/jokes/categories",
        server_url="https://api.chucknorris.io"
    )
    func.parameters = { # From functions.json
        "type": "object",
        "properties": {
            "header": {
                "type": "object",
                "properties": {
                    "Accept": {
                        "type": "string",
                        "default": "application/json"
                    }
                }
            }
        }
    }
    func.response_schema = None
    return func

@pytest.mark.asyncio
async def test_get_categories(
    respx_router: MockRouter,
    mock_linked_account: DBLinkedAccount,
    get_categories_function_db: DBFunction,
    no_auth_scheme: NoAuthScheme,
    no_auth_credentials: NoAuthSchemeCredentials,
):
    # Arrange
    executor = RestFunctionExecutor(
        linked_account=mock_linked_account,
        app=get_categories_function_db.app, # type: ignore
        function=get_categories_function_db, # type: ignore
        security_scheme=no_auth_scheme,
        security_credentials=no_auth_credentials,
        db_session=MagicMock(),
    )

    mock_api_response = ["animal", "career", "celebrity", "dev", "explicit", "fashion", "food", "history", "money", "movie", "music", "political", "religion", "science", "sport", "travel"]

    respx_router.get("https://api.chucknorris.io/jokes/categories").mock(return_value=MagicMock(
        status_code=200,
        json=lambda: mock_api_response
    ))

    function_input_params = FunctionInputRequiredInvisible()

    # Act
    result: FunctionExecutionResult = await executor.execute(input_params=function_input_params)

    # Assert
    assert result.success
    assert result.data == mock_api_response
    assert respx_router.calls.call_count == 1
    call = respx_router.calls.last
    assert call is not None
    assert str(call.request.url) == "https://api.chucknorris.io/jokes/categories"
    assert call.request.headers["accept"] == "application/json"

@pytest.fixture
def search_jokes_function_db(chucknorris_app_db: DBApp) -> DBFunction:
    func = MagicMock(spec=DBFunction)
    func.name = "CHUCKNORRIS__SEARCH_JOKES"
    func.app_name = chucknorris_app_db.name
    func.app = chucknorris_app_db
    func.description = "Searches for Chuck Norris jokes based on a query string."
    func.tags = ["jokes", "entertainment", "search"]
    func.visibility = Visibility.PUBLIC
    func.active = True
    func.protocol = func_schema.Protocol.REST
    func.protocol_data = FunctionProtocolDataREST(
        method="GET",
        path="/jokes/search",
        server_url="https://api.chucknorris.io"
    )
    func.parameters = { # From functions.json
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "properties": {
                    "query": { # Note: nested "query"
                        "type": "string",
                        "description": "The text to search for."
                    }
                },
                "required": ["query"]
            },
            "header": {
                "type": "object",
                "properties": {
                    "Accept": {
                        "type": "string",
                        "default": "application/json"
                    }
                }
            }
        },
        "required": ["query"]
    }
    func.response_schema = None
    return func

@pytest.mark.asyncio
async def test_search_jokes(
    respx_router: MockRouter,
    mock_linked_account: DBLinkedAccount,
    search_jokes_function_db: DBFunction,
    no_auth_scheme: NoAuthScheme,
    no_auth_credentials: NoAuthSchemeCredentials,
):
    # Arrange
    executor = RestFunctionExecutor(
        linked_account=mock_linked_account,
        app=search_jokes_function_db.app, # type: ignore
        function=search_jokes_function_db, # type: ignore
        security_scheme=no_auth_scheme,
        security_credentials=no_auth_credentials,
        db_session=MagicMock(),
    )

    query_to_test = "computer"
    mock_api_response = {
        "total": 1,
        "result": [
            {
                "icon_url": "https://assets.chucknorris.host/img/avatar/chuck-norris.png",
                "id": "computer_joke_id",
                "url": f"http://example.com/joke_id?query={query_to_test}",
                "value": "Chuck Norris's keyboard doesn't have a Ctrl key because nothing controls Chuck Norris."
            }
        ]
    }

    respx_router.get(
        "https://api.chucknorris.io/jokes/search",
        params={"query": query_to_test}
    ).mock(return_value=MagicMock(
        status_code=200,
        json=lambda: mock_api_response
    ))

    function_input_params = FunctionInputRequiredInvisible(
        query=FunctionParameterValue(value={"query": query_to_test}) # Matches the nested structure in parameters
    )

    # Act
    result: FunctionExecutionResult = await executor.execute(input_params=function_input_params)

    # Assert
    assert result.success
    assert result.data == mock_api_response
    assert respx_router.calls.call_count == 1
    call = respx_router.calls.last
    assert call is not None
    assert str(call.request.url) == f"https://api.chucknorris.io/jokes/search?query={query_to_test}"
    assert call.request.headers["accept"] == "application/json"
