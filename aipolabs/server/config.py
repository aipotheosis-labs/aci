from dotenv import load_dotenv

from aipolabs.common.utils import check_and_get_env_variable, construct_db_url

load_dotenv()


# LLM
OPENAI_API_KEY = check_and_get_env_variable("SERVER_OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = check_and_get_env_variable("SERVER_OPENAI_EMBEDDING_MODEL")
OPENAI_EMBEDDING_DIMENSION = int(check_and_get_env_variable("SERVER_OPENAI_EMBEDDING_DIMENSION"))

# JWT
JWT_SECRET_KEY = check_and_get_env_variable("SERVER_JWT_SECRET_KEY")
JWT_ALGORITHM = check_and_get_env_variable("SERVER_JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    check_and_get_env_variable("SERVER_JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
)
SESSION_SECRET_KEY = check_and_get_env_variable("SERVER_SESSION_SECRET_KEY")
AIPOLABS_REDIRECT_URI_BASE = check_and_get_env_variable("SERVER_AIPOLABS_REDIRECT_URI_BASE")

# Google Auth
GOOGLE_AUTH_CLIENT_ID = check_and_get_env_variable("SERVER_GOOGLE_AUTH_CLIENT_ID")
GOOGLE_AUTH_CLIENT_SECRET = check_and_get_env_variable("SERVER_GOOGLE_AUTH_CLIENT_SECRET")
GOOGLE_AUTH_SERVER_METADATA_URL = check_and_get_env_variable(
    "SERVER_GOOGLE_AUTH_SERVER_METADATA_URL"
)
GOOGLE_AUTH_CLIENT_KWARGS = {
    "scope": "openid email profile",
    "prompt": "consent",  # Force the user to consent again (help if need to get the refresh token)
}
DB_SCHEME = check_and_get_env_variable("SERVER_DB_SCHEME")
DB_USER = check_and_get_env_variable("SERVER_DB_USER")
DB_PASSWORD = check_and_get_env_variable("SERVER_DB_PASSWORD")
DB_HOST = check_and_get_env_variable("SERVER_DB_HOST")
DB_PORT = check_and_get_env_variable("SERVER_DB_PORT")
DB_NAME = check_and_get_env_variable("SERVER_DB_NAME")
# need to use "+psycopg" to use psycopg3 instead of psycopg2 (default)
DB_FULL_URL = construct_db_url(DB_SCHEME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

# RATE LIMITS
RATE_LIMIT_IP_PER_SECOND = int(check_and_get_env_variable("SERVER_RATE_LIMIT_IP_PER_SECOND"))
RATE_LIMIT_IP_PER_DAY = int(check_and_get_env_variable("SERVER_RATE_LIMIT_IP_PER_DAY"))
AOPOLABS_API_KEY_NAME = "X-API-KEY"

# PROJECT QUOTA
PROJECT_DAILY_QUOTA = int(check_and_get_env_variable("SERVER_PROJECT_DAILY_QUOTA"))

APPLICATION_LOAD_BALANCER_DNS = check_and_get_env_variable("SERVER_APPLICATION_LOAD_BALANCER_DNS")
