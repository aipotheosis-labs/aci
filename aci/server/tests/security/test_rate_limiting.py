import logging
import time
from typing import cast
from unittest.mock import patch

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from limits import RateLimitItemPerDay, RateLimitItemPerSecond

from aci.server import config
from aci.server.main import app as fastapi_app
from aci.server.middleware.ratelimit import RateLimitMiddleware

logger = logging.getLogger(__name__)


# TODO: not sure if there is a better way to test rate limiting (without meaningless mocking)
def get_ratelimit_middleware_instance(fastapi_app: FastAPI) -> RateLimitMiddleware:
    """find the RateLimitMiddleware instance in the middleware stack"""
    layer = fastapi_app.middleware_stack
    while layer is not None:
        if layer.__class__.__name__ == RateLimitMiddleware.__name__:
            return cast(RateLimitMiddleware, layer)
        layer = getattr(layer, "app", None)

    assert False, f"{RateLimitMiddleware.__name__} instance not found"  # noqa: B011


def test_rate_limiting_ip_per_second(test_client: TestClient, dummy_api_key_1: str) -> None:
    OVERRIDE_RATE_LIMIT_IP_PER_SECOND = 1

    rate_limit_middleware_instance = get_ratelimit_middleware_instance(fastapi_app)
    patched_rate_limits = {
        "ip-per-second": RateLimitItemPerSecond(OVERRIDE_RATE_LIMIT_IP_PER_SECOND),
        "ip-per-day": RateLimitItemPerDay(9999),
    }

    with patch.object(rate_limit_middleware_instance, "rate_limits", patched_rate_limits):
        # Test successful requests
        for _ in range(OVERRIDE_RATE_LIMIT_IP_PER_SECOND):
            response = test_client.get(
                f"{config.ROUTER_PREFIX_APPS}/search",
                headers={"x-api-key": dummy_api_key_1},
            )
            assert response.status_code == status.HTTP_200_OK

        # Test rate limit exceeded
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Verify rate limit headers
        assert "X-RateLimit-Limit-ip-per-second" in response.headers
        assert "X-RateLimit-Remaining-ip-per-second" in response.headers
        assert "X-RateLimit-Reset-ip-per-second" in response.headers
        assert response.headers["x-ratelimit-remaining-ip-per-second"] == "0"

        # sleep to reset rate limit, should succeed
        time.sleep(2)
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_200_OK


def test_rate_limiting_ip_per_day(test_client: TestClient, dummy_api_key_1: str) -> None:
    OVERRIDE_RATE_LIMIT_IP_PER_DAY = 1

    rate_limit_middleware_instance = get_ratelimit_middleware_instance(fastapi_app)
    patched_rate_limits = {
        "ip-per-second": RateLimitItemPerSecond(9999),
        "ip-per-day": RateLimitItemPerDay(OVERRIDE_RATE_LIMIT_IP_PER_DAY),
    }

    with patch.object(rate_limit_middleware_instance, "rate_limits", patched_rate_limits):
        # Test successful requests
        for _ in range(OVERRIDE_RATE_LIMIT_IP_PER_DAY):
            response = test_client.get(
                f"{config.ROUTER_PREFIX_APPS}/search",
                headers={"x-api-key": dummy_api_key_1},
            )
            assert response.status_code == status.HTTP_200_OK

        # Test rate limit exceeded
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Verify rate limit headers
        assert "X-RateLimit-Limit-ip-per-day" in response.headers
        assert "X-RateLimit-Remaining-ip-per-day" in response.headers
        assert "X-RateLimit-Reset-ip-per-day" in response.headers
        assert response.headers["x-ratelimit-remaining-ip-per-day"] == "0"

        # sleep for seconds should NOT reset daily rate limit, so should fail
        time.sleep(2)
        response = test_client.get(
            f"{config.ROUTER_PREFIX_APPS}/search",
            headers={"x-api-key": dummy_api_key_1},
        )
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
