from aipolabs.common.logging import get_logger
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.app import AppEmbeddingFields
from aipolabs.common.schemas.function import FunctionCreate

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
    text_for_embedding = (
        f"{app.name}\n"
        f"{app.display_name}\n"
        f"{app.provider}\n"
        f"{app.description}\n"
        f"{' '.join(app.categories)}"
    )

    return openai_service.generate_embedding(
        text_for_embedding, embedding_model, embedding_dimension
    )


# TODO: batch generate function embeddings
# TODO: update app embedding to include function embeddings whenever functions are added/updated?
def generate_function_embeddings(
    functions_create: list[FunctionCreate],
    openai_service: OpenAIService,
    embedding_model: str,
    embedding_dimension: int,
) -> list[list[float]]:
    logger.debug(f"Generating embeddings for {len(functions_create)} functions...")
    function_embeddings: list[list[float]] = []
    for function_create in functions_create:
        function_embeddings.append(
            generate_function_embedding(
                function_create, openai_service, embedding_model, embedding_dimension
            )
        )

    return function_embeddings


# TODO: include response schema in the embedding if added
def generate_function_embedding(
    function_create: FunctionCreate,
    openai_service: OpenAIService,
    embedding_model: str,
    embedding_dimension: int,
) -> list[float]:
    logger.debug(f"Generating embedding for function: {function_create.name}...")
    text_for_embedding = (
        f"{function_create.name}\n{function_create.description}\n{function_create.parameters}"
    )

    return openai_service.generate_embedding(
        text_for_embedding, embedding_model, embedding_dimension
    )
