from aipolabs.common.logging import get_logger
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import AppEmbeddingFields
from aipolabs.common.schemas.function import FunctionEmbeddingFields

logger = get_logger(__name__)


def generate_app_embedding(
    app: AppEmbeddingFields,
    openai_service: OpenAIService,
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
    return openai_service.generate_embedding(
        text_for_embedding, embedding_model, embedding_dimension
    )


# TODO: batch generate function embeddings
# TODO: update app embedding to include function embeddings whenever functions are added/updated?
def generate_function_embeddings(
    functions: list[FunctionEmbeddingFields],
    openai_service: OpenAIService,
    embedding_model: str,
    embedding_dimension: int,
) -> list[list[float]]:
    logger.debug(f"Generating embeddings for {len(functions)} functions...")
    function_embeddings: list[list[float]] = []
    for function in functions:
        function_embeddings.append(
            generate_function_embedding(
                function, openai_service, embedding_model, embedding_dimension
            )
        )

    return function_embeddings


def generate_function_embedding(
    function: FunctionEmbeddingFields,
    openai_service: OpenAIService,
    embedding_model: str,
    embedding_dimension: int,
) -> list[float]:
    logger.debug(f"Generating embedding for function: {function.name}...")
    text_for_embedding = function.model_dump_json()
    logger.debug(f"Text for function embedding: {text_for_embedding}")
    return openai_service.generate_embedding(
        text_for_embedding, embedding_model, embedding_dimension
    )
