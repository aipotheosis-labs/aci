import click

from aci.cli.commands import (
    create_agent,
    create_project,
    create_random_api_key,
    delete_app,
    fuzzy_test_function_execution,
    get_app,
    rename_app,
    update_agent,
    upsert_app,
    upsert_functions,
)
from aci.common.logging_setup import setup_logging


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """AIPO CLI Tool"""
    setup_logging()


# Add commands to the group
cli.add_command(create_project.create_project)
cli.add_command(create_agent.create_agent)
cli.add_command(update_agent.update_agent)
cli.add_command(upsert_app.upsert_app)
cli.add_command(get_app.get_app)
cli.add_command(rename_app.rename_app)
cli.add_command(delete_app.delete_app)
cli.add_command(upsert_functions.upsert_functions)
cli.add_command(create_random_api_key.create_random_api_key)
cli.add_command(fuzzy_test_function_execution.fuzzy_test_function_execution)

if __name__ == "__main__":
    cli()
