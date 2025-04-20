import json

import click
from rich.console import Console
from rich.syntax import Syntax

from aci.cli import config
from aci.common import utils
from aci.common.db import crud

console = Console()


@click.command()
@click.option(
    "--app-name",
    "app_name",
    required=True,
    help="Name of the app to retrieve",
)
def get_app(
    app_name: str,
) -> None:
    """
    Get an app by name from the database.
    """
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        app = crud.apps.get_app(
            db_session,
            app_name,
            public_only=False,
            active_only=False,
        )

        if app is None:
            console.rule(f"[bold red]App '{app_name}' not found[/bold red]")
            return

        console.rule(f"[bold green]App: {app.name}[/bold green]")

        # print without excluded fields
        excluded_fields = ["functions", "_sa_instance_state"]
        app_dict = {}
        for key, value in vars(app).items():
            if key not in excluded_fields:
                app_dict[key] = value

        # Add function count
        app_dict["function_count"] = len(app.functions) if hasattr(app, "functions") else 0

        # Convert to JSON string with nice formatting
        json_str = json.dumps(app_dict, indent=2, default=str)

        # Print with syntax highlighting
        console.print(Syntax(json_str, "json", theme="monokai"))
