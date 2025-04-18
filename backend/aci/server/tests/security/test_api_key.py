from fastapi import status
from fastapi.testclient import TestClient

from aci.server import config


# sending a request without a valid api key in x-api-key header to /apps route should fail
def test_without_api_key(test_client: TestClient) -> None:
    search_params: dict[str, str | list[str] | int] = {
        "intent": "i want to create a new code repo for my project",
        "categories": [],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# sending a request with a invalid api key should fail
def test_with_invalid_api_key(test_client: TestClient, dummy_api_key_1: str) -> None:
    search_params: dict[str, str | list[str] | int] = {
        "intent": "i want to create a new code repo for my project",
        "categories": [],
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        f"{config.ROUTER_PREFIX_APPS}/search",
        params=search_params,
        headers={"x-api-key": "invalid_api_key"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# TODO: test disabled/deleted api key
