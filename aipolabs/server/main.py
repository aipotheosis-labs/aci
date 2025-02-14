# import sentry_sdk
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from aipolabs.common.exceptions import AipolabsException
from aipolabs.common.logging import get_logger, setup_logging
from aipolabs.server import config
from aipolabs.server import dependencies as deps
from aipolabs.server.middleware.ratelimit import RateLimitMiddleware
from aipolabs.server.routes import (
    app_configurations,
    apps,
    auth,
    functions,
    health,
    linked_accounts,
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
    title=config.APP_TITLE,
    version=config.APP_VERSION,
    docs_url=config.APP_DOCS_URL,
    redoc_url=config.APP_REDOC_URL,
    openapi_url=config.APP_OPENAPI_URL,
    generate_unique_id_function=custom_generate_unique_id,
)

"""middlewares are executed in the reverse order"""
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=[config.APPLICATION_LOAD_BALANCER_DNS])
app.add_middleware(SessionMiddleware, secret_key=config.SIGNING_KEY)

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
    allow_origins=[config.SERVER_DEV_PORTAL_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "X-API-KEY"],
)


# NOTE: generic exception handler (type Exception) for all exceptions doesn't work
# https://github.com/fastapi/fastapi/discussions/9478
@app.exception_handler(AipolabsException)
async def global_exception_handler(request: Request, exc: AipolabsException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.error_code,
        content={"error": f"{exc.title}, {exc.message}" if exc.message else exc.title},
    )


# TODO: custom rate limiting on different routes
app.include_router(
    health.router,
    prefix=config.ROUTER_PREFIX_HEALTH,
    tags=[config.ROUTER_PREFIX_HEALTH.split("/")[-1]],
)
app.include_router(auth.router, prefix=config.ROUTER_PREFIX_AUTH, tags=["auth"])
app.include_router(
    projects.router,
    prefix=config.ROUTER_PREFIX_PROJECTS,
    tags=[config.ROUTER_PREFIX_PROJECTS.split("/")[-1]],
    dependencies=[Depends(deps.validate_http_bearer)],
)
# TODO: add validate_project_quota to all routes
app.include_router(
    apps.router,
    prefix=config.ROUTER_PREFIX_APPS,
    tags=[config.ROUTER_PREFIX_APPS.split("/")[-1]],
    dependencies=[Depends(deps.validate_api_key), Depends(deps.validate_project_quota)],
)
app.include_router(
    functions.router,
    prefix=config.ROUTER_PREFIX_FUNCTIONS,
    tags=[config.ROUTER_PREFIX_FUNCTIONS.split("/")[-1]],
    dependencies=[Depends(deps.validate_api_key), Depends(deps.validate_project_quota)],
)
app.include_router(
    app_configurations.router,
    prefix=config.ROUTER_PREFIX_APP_CONFIGURATIONS,
    tags=[config.ROUTER_PREFIX_APP_CONFIGURATIONS.split("/")[-1]],
    dependencies=[Depends(deps.validate_api_key)],
)
# TODO: project quota management for different routes
# similar to auth, it contains a callback route so can't use global dependencies here
app.include_router(
    linked_accounts.router,
    prefix=config.ROUTER_PREFIX_LINKED_ACCOUNTS,
    tags=[config.ROUTER_PREFIX_LINKED_ACCOUNTS.split("/")[-1]],
)
