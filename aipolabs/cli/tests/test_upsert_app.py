import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy.orm import Session

from aipolabs.cli.commands.upsert_app import upsert_app
from aipolabs.common.db import crud


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
                "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
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
def dummy_app_file(tmp_path: Path, dummy_app_data: dict) -> Path:
    dummy_app_file = tmp_path / "app.json"
    dummy_app_file.write_text(json.dumps(dummy_app_data))
    return dummy_app_file


@pytest.fixture
def dummy_app_secrets_file(tmp_path: Path, dummy_app_secrets_data: dict) -> Path:
    dummy_app_secrets_file = tmp_path / ".app.secrets.json"
    dummy_app_secrets_file.write_text(json.dumps(dummy_app_secrets_data))
    return dummy_app_secrets_file


@pytest.mark.parametrize("skip_dry_run", [True, False])
def test_create_app(
    db_session: Session,
    dummy_app_data: dict,
    dummy_app_file: Path,
    dummy_app_secrets_data: dict,
    dummy_app_secrets_file: Path,
    skip_dry_run: bool,
) -> None:
    runner = CliRunner()
    command = [
        "--app-file",
        dummy_app_file,
        "--secrets-file",
        dummy_app_secrets_file,
    ]
    if skip_dry_run:
        command.append("--skip-dry-run")

    result = runner.invoke(upsert_app, command)
    assert result.exit_code == 0, result.output
    # new record is created by a different db session, so we need to
    # expire the injected db_session to see the new record
    db_session.expire_all()
    app = crud.apps.get_app(
        db_session, dummy_app_data["name"], public_only=False, active_only=False
    )

    if skip_dry_run:
        assert app is not None
        assert app.name == dummy_app_data["name"]
        assert (
            app.security_schemes["oauth2"]["client_id"]
            == dummy_app_secrets_data["AIPOLABS_GOOGLE_APP_CLIENT_ID"]
        )
        assert (
            app.security_schemes["oauth2"]["client_secret"]
            == dummy_app_secrets_data["AIPOLABS_GOOGLE_APP_CLIENT_SECRET"]
        )
    else:
        assert app is None, "App should not be created for dry run"


@pytest.mark.parametrize("skip_dry_run", [True, False])
def test_update_app(
    db_session: Session,
    dummy_app_data: dict,
    dummy_app_file: Path,
    dummy_app_secrets_data: dict,
    dummy_app_secrets_file: Path,
    skip_dry_run: bool,
) -> None:
    # create the app first
    test_create_app(
        db_session,
        dummy_app_data,
        dummy_app_file,
        dummy_app_secrets_data,
        dummy_app_secrets_file,
        True,
    )

    # modify the app data
    new_oauth2_scope = "updated_scope"
    new_oauth2_client_id = "updated_client_id"
    new_api_key = {"location": "header", "name": "X-API-KEY"}

    dummy_app_data["security_schemes"]["oauth2"]["scope"] = new_oauth2_scope
    dummy_app_secrets_data["AIPOLABS_GOOGLE_APP_CLIENT_ID"] = new_oauth2_client_id
    dummy_app_data["security_schemes"]["api_key"] = new_api_key

    # write the modified app data and secrets to the files
    dummy_app_file.write_text(json.dumps(dummy_app_data))
    dummy_app_secrets_file.write_text(json.dumps(dummy_app_secrets_data))

    # update the app
    runner = CliRunner()
    command = [
        "--app-file",
        dummy_app_file,
        "--secrets-file",
        dummy_app_secrets_file,
    ]
    if skip_dry_run:
        command.append("--skip-dry-run")

    result = runner.invoke(upsert_app, command)
    assert result.exit_code == 0, result.output

    db_session.expire_all()
    app = crud.apps.get_app(
        db_session, dummy_app_data["name"], public_only=False, active_only=False
    )

    if skip_dry_run:
        assert app is not None
        assert app.name == dummy_app_data["name"]
        assert app.security_schemes["oauth2"]["scope"] == new_oauth2_scope
        assert app.security_schemes["oauth2"]["client_id"] == new_oauth2_client_id
        assert app.security_schemes["api_key"] == new_api_key
    else:
        # nothing should change for dry run
        assert app is not None
        assert app.name == dummy_app_data["name"]
        assert (
            app.security_schemes["oauth2"]["scope"]
            == "openid email profile https://www.googleapis.com/auth/calendar"
        )
        assert app.security_schemes["oauth2"]["client_id"] == "dummy_client_id"
        assert "api_key" not in app.security_schemes
