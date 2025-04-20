from copy import deepcopy

import click
from rich.console import Console

from aci.cli import config
from aci.common import utils
from aci.common.db import crud

console = Console()


@click.command()
@click.option(
    "--current-name",
    "current_name",
    required=True,
    help="Current name of the app to rename",
)
@click.option(
    "--new-name",
    "new_name",
    required=True,
    help="New name for the app",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="Provide this flag to run the command and apply changes to the database",
)
def rename_app(
    current_name: str,
    new_name: str,
    skip_dry_run: bool,
) -> None:
    """
    Rename an app and update all related table entities.

    This command changes the app name and updates all functions that begin with the app name prefix.
    It also updates any references to the app in other tables like AppConfigurations and Agents.
    """
    # if skip dry run, warn user
    if skip_dry_run:
        console.print(
            "[bold red]WARNING: This operation will change the name of the app and all data "
            "associated with the app including functions, linked accounts, app configurations, "
            "and agents's allowed_apps and custom_instructions.[/bold red]"
        )
        if not click.confirm("Are you sure you want to continue?", default=False):
            raise click.Abort()

    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        # Check if old app exists
        app = crud.apps.get_app(
            db_session,
            current_name,
            public_only=False,
            active_only=False,
        )
        if app is None:
            raise click.ClickException(f"App '{current_name}' not found")

        # Check if new app name already exists
        new_app = crud.apps.get_app(
            db_session,
            new_name,
            public_only=False,
            active_only=False,
        )
        if new_app is not None:
            raise click.ClickException(f"App with name '{new_name}' already exists")

        # Get functions that need to be renamed
        functions = crud.functions.get_functions_by_app_id(db_session, app.id)

        # Get app configurations that need to be updated
        app_configurations = crud.app_configurations.get_app_configurations_by_app_id(
            db_session, app.id
        )

        # Get agents that include this app in allowed_apps
        agents = crud.projects.get_agents_whose_allowed_apps_contains(db_session, current_name)

        if not skip_dry_run:
            console.rule("[bold yellow]Dry run mode - no changes applied[/bold yellow]")

        try:
            # Update app name
            app.name = new_name
            console.print(f"Updating app name from '{current_name}' to '{new_name}'")

            # Update function names
            for function in functions:
                assert function.name.startswith(f"{current_name}__")
                new_function_name = function.name.replace(f"{current_name}__", f"{new_name}__", 1)
                console.print(
                    f"Updating function name from '{function.name}' to '{new_function_name}'"
                )
                function.name = new_function_name

            # Update app configurations's enabled_functions (if the functions are from the app)
            for app_config in app_configurations:
                # Update enabled_functions if they contain the old app name
                for i, func_name in enumerate(app_config.enabled_functions):
                    if func_name.startswith(f"{current_name}__"):
                        new_func_name = func_name.replace(f"{current_name}__", f"{new_name}__", 1)
                        app_config.enabled_functions[i] = new_func_name
                        console.print(
                            f"Updating enabled_functions from '{func_name}' to '{new_func_name}' for app configuration {app_config.id}"
                        )

            # Update agents allowed_apps
            for agent in agents:
                # Directly modify the allowed_apps list in place
                for i, app_name in enumerate(agent.allowed_apps):
                    if app_name == current_name:
                        agent.allowed_apps[i] = new_name
                        console.print(
                            f"Updating allowed_apps from '{app_name}' to '{new_name}' for agent {agent.id}"
                        )

                # Update custom_instructions if they reference the old app name
                new_custom_instructions = deepcopy(agent.custom_instructions)
                # Find keys that need to be updated before modifying the dictionary
                keys_to_update = [
                    key
                    for key in new_custom_instructions.keys()
                    if key.startswith(f"{current_name}__")
                ]
                for func_name in keys_to_update:
                    new_func_name = func_name.replace(f"{current_name}__", f"{new_name}__", 1)
                    new_custom_instructions[new_func_name] = new_custom_instructions[func_name]
                    del new_custom_instructions[func_name]
                    console.print(
                        f"Updating custom_instructions from '{func_name}' to '{new_func_name}' for agent {agent.id}"
                    )
                agent.custom_instructions = new_custom_instructions

            # Commit changes
            if not skip_dry_run:
                console.rule(
                    "[bold yellow]Run with [bold green]--skip-dry-run[/bold green] to apply these changes[/bold yellow]"
                )
            else:
                db_session.commit()
                console.rule(
                    f"[bold green]Successfully renamed app from '{current_name}' to '{new_name}'[/bold green]"
                )
        except Exception as e:
            db_session.rollback()
            console.print(f"[bold red]Error renaming app: {e}[/bold red]")
