import json
import logging
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

from aci.cli import config

# override the rate limit to a high number for testing before importing aipolabs modules
from aci.common import utils
from aci.common.db.sql_models import Base

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


@pytest.fixture
def dummy_app_data() -> dict:
    return {
        "name": "GOOGLE_CALENDAR",
        "display_name": "Google Calendar",
        "logo": "https://example.com/google-logo.png",
        "provider": "Google",
        "version": "3.0.0",
        "description": "The Google Calendar API is a RESTful API that can be accessed through explicit HTTP calls. The API exposes most of the features available in the Google Calendar Web interface.",
        "security_schemes": {
            "oauth2": {
                "location": "header",
                "name": "Authorization",
                "prefix": "Bearer",
                "client_id": "{{ AIPOLABS_GOOGLE_APP_CLIENT_ID }}",
                "client_secret": "{{ AIPOLABS_GOOGLE_APP_CLIENT_SECRET }}",
                "scope": "openid email profile https://www.googleapis.com/auth/calendar",
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "access_token_url": "https://oauth2.googleapis.com/token",
                "refresh_token_url": "https://oauth2.googleapis.com/token",
            }
        },
        "default_security_credentials_by_scheme": {},
        "categories": ["calendar"],
        "visibility": "public",
        "active": True,
    }


@pytest.fixture
def dummy_app_secrets_data() -> dict:
    return {
        "AIPOLABS_GOOGLE_APP_CLIENT_ID": "dummy_client_id",
        "AIPOLABS_GOOGLE_APP_CLIENT_SECRET": "dummy_client_secret",
    }


@pytest.fixture
def dummy_functions_data() -> list[dict]:
    return [
        {
            "name": "GOOGLE_CALENDAR__CALENDARLIST_LIST",
            "description": "Returns the calendars on the user's calendar list",
            "tags": ["calendar"],
            "visibility": "public",
            "active": True,
            "protocol": "rest",
            "protocol_data": {
                "method": "GET",
                "path": "/users/me/calendarList",
                "server_url": "https://www.googleapis.com/calendar/v3",
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "object",
                        "description": "query parameters",
                        "properties": {
                            "maxResults": {
                                "type": "integer",
                                "description": "Maximum number of entries returned on one result page. By default the value is 100 entries. The page size can never exceed 250 entries.",
                                "default": 100,
                            }
                        },
                        "required": [],
                        "visible": ["maxResults"],
                        "additionalProperties": False,
                    },
                },
                "required": [],
                "visible": ["query"],
                "additionalProperties": False,
            },
        }
    ]


@pytest.fixture
def dummy_app_file(tmp_path: Path, dummy_app_data: dict) -> Path:
    dummy_app_file = tmp_path / "app.json"
    dummy_app_file.write_text(json.dumps(dummy_app_data))
    return dummy_app_file


@pytest.fixture
def dummy_app_secrets_file(tmp_path: Path, dummy_app_secrets_data: dict) -> Path:
    dummy_app_secrets_file = tmp_path / ".app.secrets.json"
    dummy_app_secrets_file.write_text(json.dumps(dummy_app_secrets_data))
    return dummy_app_secrets_file


@pytest.fixture
def dummy_functions_file(tmp_path: Path, dummy_functions_data: list[dict]) -> Path:
    dummy_functions_file = tmp_path / "functions.json"
    dummy_functions_file.write_text(json.dumps(dummy_functions_data))
    return dummy_functions_file
