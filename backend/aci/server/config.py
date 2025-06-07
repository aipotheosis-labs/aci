from aci.common.utils import check_and_get_env_variable, construct_db_url

ENVIRONMENT = check_and_get_env_variable("SERVER_ENVIRONMENT")

# LLM
OPENAI_API_KEY = check_and_get_env_variable("SERVER_OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = check_and_get_env_variable("SERVER_OPENAI_EMBEDDING_MODEL")
OPENAI_EMBEDDING_DIMENSION = int(check_and_get_env_variable("SERVER_OPENAI_EMBEDDING_DIMENSION"))

# JWT
SIGNING_KEY = check_and_get_env_variable("SERVER_SIGNING_KEY")
JWT_ALGORITHM = check_and_get_env_variable("SERVER_JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    check_and_get_env_variable("SERVER_JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
)
REDIRECT_URI_BASE = check_and_get_env_variable("SERVER_REDIRECT_URI_BASE")
COOKIE_KEY_FOR_AUTH_TOKEN = "accessToken"

# Google Auth
GOOGLE_AUTH_CLIENT_SCOPE = "openid email profile"
DB_SCHEME = check_and_get_env_variable("SERVER_DB_SCHEME")
DB_USER = check_and_get_env_variable("SERVER_DB_USER")
DB_PASSWORD = check_and_get_env_variable("SERVER_DB_PASSWORD")
DB_HOST = check_and_get_env_variable("SERVER_DB_HOST")
DB_PORT = check_and_get_env_variable("SERVER_DB_PORT")
DB_NAME = check_and_get_env_variable("SERVER_DB_NAME")
# need to use "+psycopg" to use psycopg3 instead of psycopg2 (default)
DB_FULL_URL = construct_db_url(DB_SCHEME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

# PropelAuth
PROPELAUTH_AUTH_URL = check_and_get_env_variable("SERVER_PROPELAUTH_AUTH_URL")
PROPELAUTH_API_KEY = check_and_get_env_variable("SERVER_PROPELAUTH_API_KEY")

# SVIX
SVIX_SIGNING_SECRET = check_and_get_env_variable("SERVER_SVIX_SIGNING_SECRET")

# RATE LIMITS
RATE_LIMIT_IP_PER_SECOND = int(check_and_get_env_variable("SERVER_RATE_LIMIT_IP_PER_SECOND"))
RATE_LIMIT_IP_PER_DAY = int(check_and_get_env_variable("SERVER_RATE_LIMIT_IP_PER_DAY"))

# QUOTA
PROJECT_DAILY_QUOTA = int(check_and_get_env_variable("SERVER_PROJECT_DAILY_QUOTA"))
MAX_AGENTS_PER_PROJECT = int(check_and_get_env_variable("SERVER_MAX_AGENTS_PER_PROJECT"))
APPLICATION_LOAD_BALANCER_DNS = check_and_get_env_variable("SERVER_APPLICATION_LOAD_BALANCER_DNS")

# APP
APP_TITLE = "ACI"
APP_VERSION = "0.0.1-beta.4"
APP_DOCS_URL = "/v1/notforhuman-docs"
APP_REDOC_URL = "/v1/notforhuman-redoc"
APP_OPENAPI_URL = "/v1/notforhuman-openapi.json"

# ROUTERS
ROUTER_PREFIX_HEALTH = "/v1/health"
ROUTER_PREFIX_AUTH = "/v1/auth"
ROUTER_PREFIX_PROJECTS = "/v1/projects"
ROUTER_PREFIX_APPS = "/v1/apps"
ROUTER_PREFIX_FUNCTIONS = "/v1/functions"
ROUTER_PREFIX_APP_CONFIGURATIONS = "/v1/app-configurations"
ROUTER_PREFIX_LINKED_ACCOUNTS = "/v1/linked-accounts"
ROUTER_PREFIX_AGENT = "/v1/agent"
ROUTER_PREFIX_ANALYTICS = "/v1/analytics"
ROUTER_PREFIX_WEBHOOKS = "/v1/webhooks"
ROUTER_PREFIX_BILLING = "/v1/billing"
ROUTER_PREFIX_ORGANIZATIONS = "/v1/organizations"

# DEV PORTAL
DEV_PORTAL_URL = check_and_get_env_variable("SERVER_DEV_PORTAL_URL")

# LOGFIRE
LOGFIRE_WRITE_TOKEN = check_and_get_env_variable("SERVER_LOGFIRE_WRITE_TOKEN")
LOGFIRE_READ_TOKEN = check_and_get_env_variable("SERVER_LOGFIRE_READ_TOKEN")

# STRIPE
STRIPE_SECRET_KEY = check_and_get_env_variable("SERVER_STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SIGNING_SECRET = check_and_get_env_variable("SERVER_STRIPE_WEBHOOK_SIGNING_SECRET")

# HEADERS
ACI_ORG_ID_HEADER = "X-ACI-ORG-ID"
ACI_API_KEY_HEADER = "X-API-KEY"
