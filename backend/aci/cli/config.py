from dotenv import load_dotenv

from aci.common.utils import check_and_get_env_variable, construct_db_url

load_dotenv()

OPENAI_API_KEY = check_and_get_env_variable("CLI_OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = check_and_get_env_variable("CLI_OPENAI_EMBEDDING_MODEL")
OPENAI_EMBEDDING_DIMENSION = int(check_and_get_env_variable("CLI_OPENAI_EMBEDDING_DIMENSION"))
DB_SCHEME = check_and_get_env_variable("CLI_DB_SCHEME")
DB_USER = check_and_get_env_variable("CLI_DB_USER")
DB_PASSWORD = check_and_get_env_variable("CLI_DB_PASSWORD")
DB_HOST = check_and_get_env_variable("CLI_DB_HOST")
DB_PORT = check_and_get_env_variable("CLI_DB_PORT")
DB_NAME = check_and_get_env_variable("CLI_DB_NAME")
DB_FULL_URL = construct_db_url(DB_SCHEME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)
SERVER_URL = check_and_get_env_variable("CLI_SERVER_URL")
