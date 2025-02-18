import json
import logging
import uuid
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from aipolabs.common.logging import get_logger
from aipolabs.server.context import request_id_ctx_var

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging structured analytics data for every request/response.
    It generates a unique request ID and logs some baseline details.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = datetime.now(UTC)
        request_id = str(uuid.uuid4())
        request_id_ctx_var.set(request_id)

        # Log the incoming request
        request_log_data = {
            "message": "Request received",
            "method": request.method,
            "url": str(request.url),
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown"),
        }
        logger.info(json.dumps(request_log_data))

        try:
            response = await call_next(request)
        except Exception as e:
            # Log the exception details if something goes wrong
            error_log_data = {
                "message": "Exception occurred",
                "error": str(e),
                "duration": (datetime.now(UTC) - start_time).total_seconds(),
            }
            logger.exception(json.dumps(error_log_data))
            raise

        # Log the response details
        response_log_data = {
            "message": "Response sent",
            "status_code": response.status_code,
            "duration": (datetime.now(UTC) - start_time).total_seconds(),
            "content_length": response.headers.get("content-length"),
        }
        logger.info(json.dumps(response_log_data))

        response.headers["X-Request-ID"] = request_id

        return response


class RequestIDLogFilter(logging.Filter):
    """Logging filter that injects the current request ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.__dict__["request_id"] = request_id_ctx_var.get()
        return True
