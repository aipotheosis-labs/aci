from aci.common.logging_setup import get_logger
from aci.server import config
from openai import AzureOpenAI, OpenAI

logger = get_logger(__name__)

# cache clients with different api keys
_clients = {}

def _get_client_hashed_key(client_type: str, openai_api_key = None)-> str:
    """
    Generates a hashed key for an OpenAI client based on the provided type and API key.
    Args:
        client_type (str): The type of the client (e.g., 'openai', 'azure', etc.).
        openai_api_key (str, optional): The OpenAI API key. If not provided, 'default' is used.
    Returns:
        str: A string in the format '{type}-{api_key}' used as a hashed key for the client.
    
    """
    api_key = openai_api_key or "default"
    return f"{client_type or 'openai'}-{api_key}"
    
def create_openai_client(api_key: str = config.OPENAI_API_KEY) -> OpenAI:
    """
    Creates and returns an OpenAI or Azure OpenAI client Singleton instance based on configuration.
    This function checks if a client with the given API key and client type already exists in the internal cache.
    If so, it returns the existing client. Otherwise, it creates a new client instance (either OpenAI or AzureOpenAI)
    using the provided or default API key and configuration settings, stores it in the cache, and returns it.
    Args:
        api_key (str, optional): The API key to use for authentication. If not provided, uses the default from server config.
    Returns:
        OpenAI: An instance of the OpenAI or AzureOpenAI client, depending on configuration.
    """
    _api_key=api_key or config.OPENAI_API_KEY
    _client_type = config.OPENAI_CLIENT_TYPE or "openai"
    hashed_key= _get_client_hashed_key(_client_type, _api_key)
    _openai_client = _clients.get(hashed_key)
    
    logger.debug(f"create_openai_client - [ client_type: {_client_type}, api_version: {config.OPENAI_API_VERSION}, base_url: {config.OPENAI_BASE_URL}, azure_endpoint: {config.AZURE_OPENAI_ENDPOINT} ]")
      
    if _openai_client: 
       return _openai_client
   
    if config.OPENAI_CLIENT_TYPE == "azure":
        _openai_client = AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=api_key or config.OPENAI_API_KEY,
            api_version=config.OPENAI_API_VERSION,
        )
    else:
        _openai_client =  OpenAI(
            base_url=config.OPENAI_BASE_URL,
            api_key=api_key or config.OPENAI_API_KEY,
            organization=config.OPENAI_ORG_ID,
            project=config.OPENAI_PROJECT_ID,
        )
    _clients[hashed_key] = _openai_client
    return _clients[hashed_key]


#(pre-cache) create the server openai client based on the provided configuration 
# openai_client: OpenAI = create_openai_client(api_key=config.OPENAI_API_KEY)
