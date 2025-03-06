from uuid import UUID

import click

from aipolabs.cli import config
from aipolabs.common import utils
from aipolabs.common.db import crud
from aipolabs.common.enums import SubscriptionPlan
from aipolabs.common.logging import create_headline
from aipolabs.common.schemas.user import UserCreate


@click.command()
@click.option(
    "--auth-provider",
    "identity_provider",
    required=True,
    type=click.Choice(["google"]),  # TODO: update according to identity provider when db finalized
    help="identity provider",
)
@click.option(
    "--auth-user-id",
    "user_id_by_provider",
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
    identity_provider: str,
    user_id_by_provider: str,
    name: str,
    email: str,
    profile_picture: str | None,
    plan: SubscriptionPlan,
    skip_dry_run: bool,
) -> UUID:
    """Create a user in db."""
    return create_user_helper(
        identity_provider,
        user_id_by_provider,
        name,
        email,
        profile_picture,
        plan,
        skip_dry_run,
    )


def create_user_helper(
    identity_provider: str,
    user_id_by_provider: str,
    name: str,
    email: str,
    profile_picture: str | None,
    plan: SubscriptionPlan,
    skip_dry_run: bool,
) -> UUID:
    # no need to check if user exists, db will raise an error if user already exists
    # with same identity_provider and user_id_by_provider
    with utils.create_db_session(config.DB_FULL_URL) as db_session:
        user_create = UserCreate(
            identity_provider=identity_provider,
            user_id_by_provider=user_id_by_provider,
            name=name,
            email=email,
            profile_picture=profile_picture,
            plan=plan,
        )
        user = crud.users.create_user(db_session, user_create)

        if not skip_dry_run:
            click.echo(create_headline(f"will create new user {user.name}"))
            click.echo(user)
            click.echo(create_headline("provide --skip-dry-run to commit changes"))
            db_session.rollback()
        else:
            click.echo(create_headline(f"committing creation of user {user.name}"))
            click.echo(user)
            db_session.commit()

        return user.id
