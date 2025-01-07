from fastapi import status
from fastapi.testclient import TestClient


# sending a request without a valid jwt token in Authorization header to /projects route should fail
def test_without_bearer_token(test_client: TestClient) -> None:
    body = {"name": "project test_without_bearer_token"}

    response = test_client.post("/v1/projects/", json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# sending a request with an invalid bearer token should fail
def test_with_invalid_bearer_token(test_client: TestClient) -> None:
    body = {"name": "project test_with_invalid_bearer_token"}

    response = test_client.post(
        "/v1/projects/",
        json=body,
        headers={"Authorization": "Bearer xxx"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# sending a request with a valid bearer token should succeed
def test_with_valid_bearer_token(test_client: TestClient, dummy_user_bearer_token: str) -> None:
    body = {"name": "project test_with_valid_bearer_token"}

    response = test_client.post(
        "/v1/projects/",
        json=body,
        headers={"Authorization": f"Bearer {dummy_user_bearer_token}"},
    )
    assert response.status_code == status.HTTP_200_OK
