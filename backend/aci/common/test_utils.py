import logging
from collections.abc import Generator

from sqlalchemy.orm import Session

from aci.common import utils
from aci.common.db.sql_models import Base
from aci.server import config

logger = logging.getLogger(__name__)


def clear_database(db_session: Session) -> None:
    """
    Clear all tables in the database except alembic_version.
    """
    for table in reversed(Base.metadata.sorted_tables):
        if table.name != "alembic_version" and db_session.query(table).count() > 0:
            logger.debug(f"Deleting all records from table {table.name}")
            db_session.execute(table.delete())
    db_session.commit()


def create_test_db_session() -> Generator[Session, None, None]:
    """
    Create a database session for testing.
    Ensures we're using the test database.
    Each test gets its own database session for better isolation.
    """
    assert config.DB_HOST == "test-db", "Must use test-db for tests"
    assert "test" in config.DB_FULL_URL.lower(), "Database URL must contain 'test' for safety"

    with utils.create_db_session(config.DB_FULL_URL) as session:
        yield session
