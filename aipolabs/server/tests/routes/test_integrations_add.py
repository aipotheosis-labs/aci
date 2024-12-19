from fastapi.testclient import TestClient

from aipolabs.common.enums import SecurityScheme


def test_add_integration(
    test_client: TestClient,
    dummy_api_key: str,
) -> None:
    payload = {"app_name": "GOOGLE", "security_scheme": SecurityScheme.OAUTH2}

    response = test_client.post(
        "/v1/integrations/", json=payload, headers={"x-api-key": dummy_api_key}
    )
    assert response.status_code == 200, response.json()
    assert response.json()["integration_id"] is not None, response.json()
