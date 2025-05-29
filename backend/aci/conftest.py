import logging

import pytest

from aci.common import utils
from aci.common.db.sql_models import Base
from aci.server import config

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def clear_database_at_start() -> None:
    """
    Clear the database at the start of the test session.
    This fixture runs once before any tests.
    """
    # make sure we are connecting to the test database
    assert config.DB_HOST == "test-db", "Must use test-db for tests"

    # Create database session
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        # Clean up: Empty all tables in reverse order of creation
        for table in reversed(Base.metadata.sorted_tables):
            if table.name != "alembic_version" and db_session.query(table).count() > 0:
                logger.debug(f"Deleting all records from table {table.name}")
                db_session.execute(table.delete())
        db_session.commit()
        logger.info("Database cleared at start of test session")
