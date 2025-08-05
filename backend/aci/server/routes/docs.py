import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from langchain_openai import OpenAIEmbeddings
from pgvector.sqlalchemy import Vector
from pydantic import SecretStr
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from aci.common import utils
from aci.common.exceptions import ACIException, UnexpectedError
from aci.common.logging_setup import get_logger
from aci.server import config
from aci.server import dependencies as deps

router = APIRouter()
logger = get_logger(__name__)

Base: Any = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    embedding: Column[Vector] = Column(
        Vector(1536), nullable=False
    )  # OpenAI text-embedding-3-small has 1536 dimensions
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def _get_embedding_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=config.OPENAI_EMBEDDING_MODEL, api_key=SecretStr(config.OPENAI_API_KEY)
    )


@router.get("")
async def query(
    q: Annotated[str, Query(min_length=1, max_length=1000, description="Search query")],
    context: Annotated[deps.RequestContext, Depends(deps.get_request_context)],
) -> dict:
    if not q or not q.strip():
        raise ACIException(title="Invalid query", message="Query cannot be empty", error_code=400)

    try:
        with utils.create_db_session(config.VECTOR_DB_FULL_URL) as db_session:
            try:
                embedding_model = _get_embedding_model()
                query_embedding = embedding_model.embed_query(q.strip())
                docs = search_documents(db_session, query_embedding)
                data = "\n".join([str(doc.content) for doc in docs])

                return {
                    "success": True,
                    "data": data,
                    "error": None,
                }
            except SQLAlchemyError as e:
                logger.error(f"Database error in docs query: {e}")
                return {
                    "success": False,
                    "data": None,
                    "error": "Database query failed",
                }
            except Exception as e:
                logger.error(f"Error generating embeddings or searching documents: {e}")
                return {
                    "success": False,
                    "data": None,
                    "error": "Failed to generate embeddings or search documents",
                }
    except Exception as e:
        logger.error(f"Unexpected error in docs query: {e}")
        raise UnexpectedError(
            "An unexpected error occurred while processing the documentation query"
        ) from e


def search_documents(
    db_session: Session, query_embedding: list[float], k: int = 5
) -> list[Document]:
    documents = (
        db_session.query(Document)
        .order_by(Document.embedding.cosine_distance(query_embedding))
        .limit(k)
        .all()
    )
    return documents
