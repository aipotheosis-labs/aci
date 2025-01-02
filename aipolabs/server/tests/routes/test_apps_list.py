from typing import Any

from fastapi.testclient import TestClient

from aipolabs.common.db import sql_models
from aipolabs.common.schemas.app import AppDetails

AIPOLABS_TEST = "AIPOLABS_TEST"
GITHUB = "GITHUB"
GOOGLE = "GOOGLE"


def test_list_apps(
    test_client: TestClient,
    dummy_apps: list[sql_models.App],
    dummy_functions: list[sql_models.Function],
    dummy_api_key: str,
) -> None:
    query_params = {
        "limit": 100,
        "offset": 0,
    }
    response = test_client.get(
        "/v1/apps/",
        params=query_params,
        headers={"x-api-key": dummy_api_key},
    )
    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps)
    # assert each app has the correct functions
    for app in apps:
        assert len(app.functions) == len([f for f in dummy_functions if f.app_id == app.id])


def test_get_apps_pagination(
    test_client: TestClient, dummy_apps: list[sql_models.App], dummy_api_key: str
) -> None:
    assert len(dummy_apps) > 2

    query_params: dict[str, Any] = {
        "limit": len(dummy_apps) - 1,
        "offset": 0,
    }

    response = test_client.get(
        "/v1/apps/", params=query_params, headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == len(dummy_apps) - 1

    query_params["offset"] = len(dummy_apps) - 1
    response = test_client.get(
        "/v1/apps/", params=query_params, headers={"x-api-key": dummy_api_key}
    )

    assert response.status_code == 200, response.json()
    apps = [AppDetails.model_validate(response_app) for response_app in response.json()]
    assert len(apps) == 1
