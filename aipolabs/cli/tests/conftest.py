import logging
from typing import Generator, cast

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from aipolabs.cli import config

# override the rate limit to a high number for testing before importing aipolabs modules
from aipolabs.common import utils
from aipolabs.common.db.sql_models import Base

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        yield db_session


@pytest.fixture(scope="function", autouse=True)
def database_setup_and_cleanup(db_session: Session) -> Generator[None, None, None]:
    """
    Setup and cleanup the database for each test case.
    """
    # make sure we are connecting to the local db not the production db
    # TODO: it's part of the environment separation problem, need to properly set up failsafe prod isolation
    assert config.DB_HOST in ["localhost", "db"]

    # Use 'with' to manage the session context

    inspector = cast(Inspector, inspect(db_session.bind))

    # Check if all tables defined in models are created in the db
    for table in Base.metadata.tables.values():
        if not inspector.has_table(table.name):
            pytest.exit(f"Table {table} does not exist in the database.")

    # Go through all tables and make sure there are no records in the table
    # (skip alembic_version table)
    for table in Base.metadata.tables.values():
        if table.name != "alembic_version" and db_session.query(table).count() > 0:
            pytest.exit(f"Table {table} is not empty.")

    yield  # This allows the test to run

    # Clean up: Empty all tables after tests in reverse order of creation
    for table in reversed(Base.metadata.sorted_tables):
        if table.name != "alembic_version" and db_session.query(table).count() > 0:
            logger.debug(f"Deleting all records from table {table.name}")
            db_session.execute(table.delete())
    db_session.commit()
