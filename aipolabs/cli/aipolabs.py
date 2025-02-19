import click

from aipolabs.cli.commands import (
    create_agent,
    create_project,
    create_random_api_key,
    create_user,
    fuzzy_test_function_execution,
    update_agent,
    upsert_app,
    upsert_functions,
)
from aipolabs.common.logging import setup_logging


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """AIPO CLI Tool"""
    pass


# Add commands to the group
cli.add_command(create_user.create_user)
cli.add_command(create_project.create_project)
cli.add_command(create_agent.create_agent)
cli.add_command(update_agent.update_agent)
cli.add_command(upsert_app.upsert_app)
cli.add_command(upsert_functions.upsert_functions)
cli.add_command(create_random_api_key.create_random_api_key)
cli.add_command(fuzzy_test_function_execution.fuzzy_test_function_execution)
if __name__ == "__main__":
    setup_logging()
    cli()
