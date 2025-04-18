import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from sqlalchemy.orm import Session

from aci.cli.commands.upsert_functions import upsert_functions
from aci.cli.tests.test_upsert_app import test_create_app
from aci.common.db import crud
from aci.common.db.sql_models import Function
from aci.common.schemas.function import FunctionUpsert


@pytest.mark.usefixtures(
    "dummy_app_data",
    "dummy_app_file",
    "dummy_app_secrets_data",
    "dummy_app_secrets_file",
    "dummy_functions_data",
    "dummy_functions_file",
)
@pytest.mark.parametrize("skip_dry_run", [True, False])
def test_create_functions(
    db_session: Session,
    dummy_app_data: dict,
    dummy_app_file: Path,
    dummy_app_secrets_data: dict,
    dummy_app_secrets_file: Path,
    dummy_functions_data: list[dict],
    dummy_functions_file: Path,
    skip_dry_run: bool,
) -> None:
    # create the app first
    test_create_app(
        db_session,
        dummy_app_data,
        dummy_app_file,
        dummy_app_secrets_data,
        dummy_app_secrets_file,
        skip_dry_run=True,
    )

    # create the functions
    runner = CliRunner()
    command = [
        "--functions-file",
        dummy_functions_file,
    ]
    if skip_dry_run:
        command.append("--skip-dry-run")

    result = runner.invoke(upsert_functions, command)  # type: ignore
    assert result.exit_code == 0, result.output

    # check the functions are created
    db_session.expire_all()
    functions = [
        crud.functions.get_function(
            db_session, function_data["name"], public_only=False, active_only=False
        )
        for function_data in dummy_functions_data
    ]
    functions = [f for f in functions if f is not None]
    if skip_dry_run:
        assert len(functions) > 0
        assert len(functions) == len(dummy_functions_data)
        for i, function in enumerate(functions):
            assert FunctionUpsert.model_validate(
                function, from_attributes=True
            ) == FunctionUpsert.model_validate(dummy_functions_data[i])
    else:
        assert len(functions) == 0, "Functions should not be created for dry run"


@pytest.mark.parametrize("skip_dry_run", [True, False])
def test_update_functions(
    db_session: Session,
    dummy_app_data: dict,
    dummy_app_file: Path,
    dummy_app_secrets_data: dict,
    dummy_app_secrets_file: Path,
    dummy_functions_data: list[dict],
    dummy_functions_file: Path,
    skip_dry_run: bool,
) -> None:
    # create the functions first
    test_create_functions(
        db_session,
        dummy_app_data,
        dummy_app_file,
        dummy_app_secrets_data,
        dummy_app_secrets_file,
        dummy_functions_data,
        dummy_functions_file,
        skip_dry_run=True,
    )

    # modify the functions data
    new_description = "UPDATED_DESCRIPTION"
    new_parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "object",
                "description": "UPDATED_DESCRIPTION",
                "properties": {
                    "UPDATED_PROPERTY": {
                        "type": "string",
                        "description": "UPDATED_DESCRIPTION",
                        "default": "UPDATED_DEFAULT",
                    },
                },
                "required": [],
                "visible": ["UPDATED_PROPERTY"],
                "additionalProperties": False,
            },
        },
        "required": [],
        "visible": ["query"],
        "additionalProperties": False,
    }
    for function_data in dummy_functions_data:
        function_data["description"] = new_description
        function_data["parameters"] = new_parameters

    # write the modified functions data to the file
    dummy_functions_file.write_text(json.dumps(dummy_functions_data))

    # update the functions
    runner = CliRunner()
    command = [
        "--functions-file",
        dummy_functions_file,
    ]
    if skip_dry_run:
        command.append("--skip-dry-run")

    result = runner.invoke(upsert_functions, command)  # type: ignore
    assert result.exit_code == 0, result.output

    db_session.expire_all()
    functions: list[Function] = []
    for function_data in dummy_functions_data:
        function = crud.functions.get_function(
            db_session, function_data["name"], public_only=False, active_only=False
        )
        if function is not None:
            functions.append(function)

    assert len(functions) > 0
    assert len(functions) == len(dummy_functions_data)
    if skip_dry_run:
        for function in functions:
            assert function.description == new_description
            assert function.parameters == new_parameters
    else:
        for function in functions:
            assert function.description != new_description
            assert function.parameters != new_parameters


# TODO:
# - test throw error if app does not exist
# - test throw error if functions file contains functions for different apps
# - test embedding is updated if app embedding fields are changed
# - test embedding is not updated if app embedding fields are not changed
# - test functions file contains both new and existing functions
# - test functions file contains invalid function data
