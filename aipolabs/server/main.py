# import sentry_sdk
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from aipolabs.common.logging import get_logger, setup_logging
from aipolabs.server import config
from aipolabs.server import dependencies as deps
from aipolabs.server.middleware.ratelimit import RateLimitMiddleware
from aipolabs.server.routes import (
    accounts,
    app_configurations,
    apps,
    auth,
    functions,
    health,
    projects,
)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


# TODO: Sentry
# if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
#     sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

# Configure logging
setup_logging()
logger = get_logger(__name__)

# TODO: move to config
app = FastAPI(
    title="Aipolabs",
    version="0.0.1-beta.3",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

"""middlewares are executed in the reverse order"""
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=[config.APPLICATION_LOAD_BALANCER_DNS])
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET_KEY)

# TODO: for now, we don't use TrustedHostMiddleware because it blocks health check from AWS ALB:
# When ALB send health check request, it uses the task IP as the host, instead of the DNS name.
# ALB health check headers example: Headers({'host': '10.0.164.143:8000', 'user-agent': 'ELB-HealthChecker/2.0'})
# where 10.0.164.143 is the the host IP of the fargate task, in which case TrustedHostMiddleware will block the request.
# It should be fine to remove TrustedHostMiddleware as we are running the service in a private subnet behind ALB with WAF integration.
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=[
#         "localhost",
#         "127.0.0.1",
#         config.AIPOLABS_DNS,
#     ],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO: global exception handler. can switch to use middleware?
@app.exception_handler(ValidationError)
def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    logger.error(f"Validation error, request: {request}, error: {exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Internal validation error"},
    )


# TODO: custom rate limiting on different routes
app.include_router(health.router, prefix="/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(
    projects.router,
    prefix="/v1/projects",
    tags=["projects"],
    dependencies=[Depends(deps.validate_http_bearer)],
)
app.include_router(
    apps.router,
    prefix="/v1/apps",
    tags=["apps"],
    dependencies=[Depends(deps.validate_api_key), Depends(deps.validate_project_quota)],
)
app.include_router(
    functions.router,
    prefix="/v1/functions",
    tags=["functions"],
    dependencies=[Depends(deps.validate_api_key), Depends(deps.validate_project_quota)],
)
app.include_router(
    app_configurations.router,
    prefix="/v1/app-configurations",
    tags=["app-configurations"],
    dependencies=[Depends(deps.validate_api_key)],
)
# TODO: project quota management for different routes
# similar to auth, it contains a callback route so can't use global dependencies here
app.include_router(accounts.router, prefix="/v1/accounts", tags=["accounts"])
