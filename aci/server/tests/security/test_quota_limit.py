import logging
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from aci.server import config

logger = logging.getLogger(__name__)


"""
need to mock some object otherwise the other tests might fail because of we set the real quota
"""


def test_validate_project_quota_valid(test_client: TestClient, dummy_api_key_1: str) -> None:
    project = MagicMock()
    project.daily_quota_reset_at = datetime.now(UTC)
    project.daily_quota_used = config.PROJECT_DAILY_QUOTA - 1
    project.id = uuid4()
    with (
        patch(
            "aci.server.dependencies.crud.projects.get_project_by_api_key_id",
            return_value=project,
        ),
        patch("aci.server.dependencies.crud.projects.increase_project_quota_usage"),
    ):
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            params={"limit": 1},
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_200_OK


def test_validate_project_quota_exceeded(test_client: TestClient, dummy_api_key_1: str) -> None:
    project = MagicMock()
    project.daily_quota_reset_at = datetime.now(UTC)
    project.daily_quota_used = config.PROJECT_DAILY_QUOTA

    with patch(
        "aci.server.dependencies.crud.projects.get_project_by_api_key_id",
        return_value=project,
    ):
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            params={"limit": 1},
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert str(response.json()["error"]).startswith("Daily quota exceeded")
