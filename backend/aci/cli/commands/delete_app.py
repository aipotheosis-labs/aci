import click
from rich.console import Console

from aci.cli import config
from aci.common import utils
from aci.common.db import crud

console = Console()


@click.command()
@click.option(
    "--app-name",
    "app_name",
    required=True,
    help="Name of the app to delete",
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="Provide this flag to run the command and apply changes to the database",
)
def delete_app(
    app_name: str,
    skip_dry_run: bool,
) -> None:
    """
    Delete an app and all its references from the database.

    This command will:
    1. Delete all functions associated with the app
    2. Delete linked accounts associated with the app
    3. Delete app configurations referencing the app
    4. Update agents that reference the app in allowed_apps or custom_instructions
    5. Delete the app itself

    WARNING: This operation cannot be undone.
    """
    # if skip dry run, warn user
    if skip_dry_run:
        console.print(
            "[bold red]WARNING: This operation will delete all data associated with the app "
            "including functions, linked accounts, app configurations, and agents's allowed_apps "
            "and custom_instructions.[/bold red]"
        )
        if not click.confirm("Are you sure you want to continue?", default=False):
            raise click.Abort()

    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        # Check if app exists
        app = crud.apps.get_app(
            db_session,
            app_name,
            public_only=False,
            active_only=False,
        )
        if app is None:
            raise click.ClickException(f"App '{app_name}' not found")

        # Get associated data that will be affected
        functions = crud.functions.get_functions_by_app_id(db_session, app.id)
        app_configurations = crud.app_configurations.get_app_configurations_by_app_id(
            db_session, app.id
        )
        agents = crud.projects.get_agents_whose_allowed_apps_contains(db_session, app_name)

        # Get linked accounts
        linked_accounts = crud.linked_accounts.get_linked_accounts_by_app_id(db_session, app.id)

        if not skip_dry_run:
            console.rule("[bold yellow]Dry run mode - no changes applied[/bold yellow]")

        try:
            # 1. Update agents - remove from allowed_apps and custom_instructions
            for agent in agents:
                # Remove app from allowed_apps
                agent.allowed_apps = [app for app in agent.allowed_apps if app != app_name]
                console.print(f"Removed '{app_name}' from allowed_apps for agent {agent.id}")

                # Remove custom instructions for this app
                keys_to_remove = [
                    key for key in agent.custom_instructions if key.startswith(f"{app_name}__")
                ]
                for key in keys_to_remove:
                    del agent.custom_instructions[key]
                    console.print(f"Removed custom instruction '{key}' for agent {agent.id}")

            # 2. Delete linked accounts
            for linked_account in linked_accounts:
                db_session.delete(linked_account)
                console.print(
                    f"Deleted linked account {linked_account.id} for project {linked_account.project_id}"
                )

            # 3. Delete app configurations
            for app_config in app_configurations:
                db_session.delete(app_config)
                console.print(
                    f"Deleted app configuration of {app_config.app_name} for project {app_config.project_id}"
                )

            # 4. Delete functions (SQLAlchemy will handle this via cascade)
            for function in functions:
                console.print(f"Function '{function.name}' will be deleted with app")

            # 5. Delete the app (will cascade to functions)
            db_session.delete(app)
            console.print(f"Deleted app '{app_name}'")

            # Commit changes
            if skip_dry_run:
                db_session.commit()
                console.rule(f"[bold green]Successfully deleted app '{app_name}'[/bold green]")
            else:
                console.rule(
                    "[bold yellow]Run with [bold green]--skip-dry-run[/bold green] to apply these changes[/bold yellow]"
                )
                db_session.rollback()

        except Exception as e:
            db_session.rollback()
            console.print(f"[bold red]Error deleting app: {e}[/bold red]")
