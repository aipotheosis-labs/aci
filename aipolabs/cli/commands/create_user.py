from uuid import UUID

import click

from aipolabs.cli import config
from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.enums import SubscriptionPlan
from aipolabs.common.logging import create_headline
from aipolabs.common.openai_service import OpenAIService
from aipolabs.common.schemas.user import UserCreate

openai_service = OpenAIService(config.OPENAI_API_KEY)


@click.command()
@click.option(
    "--auth-provider",
    "auth_provider",
    required=True,
    type=click.Choice(["google"]),  # TODO: update according to auth provider when db finalized
    help="Auth provider",
)
@click.option(
    "--auth-user-id",
    "auth_user_id",
    required=True,
    help="Auth user id",
)
@click.option(
    "--name",
    "name",
    required=True,
    help="user name",
)
@click.option(
    "--email",
    "email",
    required=True,
    help="user email",
)
@click.option(
    "--profile-picture",
    "profile_picture",
    help="url to user profile picture",
)
@click.option(
    "--plan",
    "plan",
    type=click.Choice(list(SubscriptionPlan)),
    help="subscription plan, default is free",
    default=SubscriptionPlan.FREE,
)
@click.option(
    "--skip-dry-run",
    is_flag=True,
    help="provide this flag to run the command and apply changes to the database",
)
def create_user(
    auth_provider: str,
    auth_user_id: str,
    name: str,
    email: str,
    profile_picture: str | None,
    plan: SubscriptionPlan,
    skip_dry_run: bool,
) -> UUID:
    """Create a user in db."""
    return create_user_helper(
        auth_provider, auth_user_id, name, email, profile_picture, plan, skip_dry_run
    )


def create_user_helper(
    auth_provider: str,
    auth_user_id: str,
    name: str,
    email: str,
    profile_picture: str | None,
    plan: SubscriptionPlan,
    skip_dry_run: bool,
) -> UUID:
    # no need to check if user exists, db will raise an error if user already exists
    # with same auth_provider and auth_user_id
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        user_create = UserCreate(
            auth_provider=auth_provider,
            auth_user_id=auth_user_id,
            name=name,
            email=email,
            profile_picture=profile_picture,
            plan=plan,
        )
        db_user = crud.users.create_user(db_session, user_create)

        if not skip_dry_run:
            click.echo(create_headline(f"will create new user {db_user.name}"))
            click.echo(db_user)
            click.echo(create_headline("provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"committing creation of user {db_user.name}"))
            click.echo(db_user)
            db_session.commit()

        return db_user.id  # type: ignore
