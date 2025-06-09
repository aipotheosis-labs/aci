import logging
import uuid
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from aci.common import utils
from aci.common.db import crud
from aci.common.logging_setup import get_logger
from aci.server import config
from aci.server.context import (
    agent_id_ctx_var,
    api_key_id_ctx_var,
    org_id_ctx_var,
    project_id_ctx_var,
    request_id_ctx_var,
)

logger = get_logger(__name__)


class InterceptorMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging structured analytics data for every request/response.
    It generates a unique request ID and logs some baseline details.
    It also extracts and sets request context from the API key.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = datetime.now(UTC)
        request_id = str(uuid.uuid4())
        request_id_ctx_var.set(request_id)
        # TODO: Get request context from bearer token(propelauth)

        # Get request context from x-api-key header
        api_key = request.headers.get(config.ACI_API_KEY_HEADER)
        api_key_id = agent_id = project_id = org_id = None
        if api_key:
            logger.info(
                "api key found in header", extra={"api_key": api_key[:4] + "..." + api_key[-4:]}
            )
            try:
                with utils.create_db_session(config.DB_FULL_URL) as db_session:
                    api_key_id, agent_id, project_id, org_id = (
                        crud.projects.get_request_context_by_api_key(db_session, api_key)
                    )
                    if not api_key_id and not agent_id and not project_id and not org_id:
                        logger.warning(
                            "api key not found in db",
                            extra={"api_key": api_key[:4] + "..." + api_key[-4:]},
                        )
                        return JSONResponse(
                            status_code=401,
                            content={"error": "Unauthorized"},
                        )
                    context_vars = {
                        api_key_id_ctx_var: api_key_id,
                        agent_id_ctx_var: agent_id,
                        project_id_ctx_var: project_id,
                        org_id_ctx_var: org_id,
                    }
                    for var, value in context_vars.items():
                        var.set(str(value) if value else "unknown")

            except Exception as e:
                logger.exception(
                    f"Can't access database to query request context for API key: {e!s}"
                )

        # Skip logging for health check endpoints
        is_health_check = request.url.path == config.ROUTER_PREFIX_HEALTH

        if not is_health_check or config.ENVIRONMENT != "local":
            request_log_data = {
                "schema": request.url.scheme,
                "http_version": request.scope.get("http_version", "unknown"),
                "http_method": request.method,
                "url": str(request.url),
                "query_params": dict(request.query_params),
                "client_ip": self._get_client_ip(
                    request
                ),  # TODO: get from request.client.host if request.client else "unknown"
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "x-forwarded-proto": request.headers.get("X-Forwarded-Proto", "unknown"),
            }
            logger.info("received request", extra=request_log_data)

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(
                e,
                extra={"duration": (datetime.now(UTC) - start_time).total_seconds()},
            )
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"},
            )

        if not is_health_check or config.ENVIRONMENT != "local":
            response_log_data = {
                "status_code": response.status_code,
                "duration": (datetime.now(UTC) - start_time).total_seconds(),
                "content_length": response.headers.get("content-length"),
            }
            logger.info("response sent", extra=response_log_data)

        response.headers["X-Request-ID"] = request_id

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Get the actual client IP if the server is running behind a proxy.
        """

        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for is not None:
            # X-Forwarded-For is a list of IPs, the first one is the actual client IP
            return x_forwarded_for.split(",")[0].strip()

        else:
            return request.client.host if request.client else "unknown"


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Only add attributes when values are not None
        request_id = request_id_ctx_var.get()
        record.__dict__["request_id"] = request_id

        api_key_id = api_key_id_ctx_var.get()
        record.__dict__["api_key_id"] = api_key_id

        project_id = project_id_ctx_var.get()
        record.__dict__["project_id"] = project_id

        agent_id = agent_id_ctx_var.get()
        record.__dict__["agent_id"] = agent_id

        org_id = org_id_ctx_var.get()
        record.__dict__["org_id"] = org_id

        return True
