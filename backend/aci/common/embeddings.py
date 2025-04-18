from openai import OpenAI

from aci.common.logging_setup import get_logger
from aci.common.schemas.app import AppEmbeddingFields
from aci.common.schemas.function import FunctionEmbeddingFields

logger = get_logger(__name__)


def generate_app_embedding(
    app: AppEmbeddingFields,
    openai_client: OpenAI,
    embedding_model: str,
    embedding_dimension: int,
) -> list[float]:
    """
    Generate embedding for app.
    TODO: what else should be included or not in the embedding?
    """
    logger.debug(f"Generating embedding for app: {app.name}...")
    # generate app embeddings based on app config's name, display_name, provider, description, categories
    text_for_embedding = app.model_dump_json()
    logger.debug(f"Text for app embedding: {text_for_embedding}")
    return generate_embedding(
        openai_client, embedding_model, embedding_dimension, text_for_embedding
    )


# TODO: batch generate function embeddings
# TODO: update app embedding to include function embeddings whenever functions are added/updated?
def generate_function_embeddings(
    functions: list[FunctionEmbeddingFields],
    openai_client: OpenAI,
    embedding_model: str,
    embedding_dimension: int,
) -> list[list[float]]:
    logger.debug(f"Generating embeddings for {len(functions)} functions...")
    function_embeddings: list[list[float]] = []
    for function in functions:
        function_embeddings.append(
            generate_function_embedding(
                function, openai_client, embedding_model, embedding_dimension
            )
        )

    return function_embeddings


def generate_function_embedding(
    function: FunctionEmbeddingFields,
    openai_client: OpenAI,
    embedding_model: str,
    embedding_dimension: int,
) -> list[float]:
    logger.debug(f"Generating embedding for function: {function.name}...")
    text_for_embedding = function.model_dump_json()
    logger.debug(f"Text for function embedding: {text_for_embedding}")
    return generate_embedding(
        openai_client, embedding_model, embedding_dimension, text_for_embedding
    )


# TODO: allow different inference providers
# TODO: exponential backoff?
def generate_embedding(
    openai_client: OpenAI, embedding_model: str, embedding_dimension: int, text: str
) -> list[float]:
    """
    Generate an embedding for the given text using OpenAI's model.
    """
    logger.debug(f"Generating embedding for text: {text}")
    try:
        response = openai_client.embeddings.create(
            input=[text],
            model=embedding_model,
            dimensions=embedding_dimension,
        )
        embedding: list[float] = response.data[0].embedding
        return embedding
    except Exception:
        logger.error("Error generating embedding", exc_info=True)
        raise
