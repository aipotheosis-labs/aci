import json
import logging
from collections.abc import Generator
from pathlib import Path
from typing import cast

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.orm import Session

# override the rate limit to a high number for testing before importing aipolabs modules
from aci.common.db.sql_models import Base
from aci.common.test_utils import clear_database, create_test_db_session

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    yield from create_test_db_session()


@pytest.fixture(scope="function", autouse=True)
def database_setup_and_cleanup(db_session: Session) -> Generator[None, None, None]:
    """
    Setup and cleanup the database for each test case.
    """

    inspector = cast(Inspector, inspect(db_session.bind))

    # Check if all tables defined in models are created in the db
    for table in Base.metadata.tables.values():
        if not inspector.has_table(table.name):
            pytest.exit(f"Table {table} does not exist in the database.")

    clear_database(db_session)
    yield  # This allows the test to run
    clear_database(db_session)


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
