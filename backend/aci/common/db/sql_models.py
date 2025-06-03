"""
TODO:
Note: try to keep dependencies on other internal packages to a minimum.
Note: at the time of writing, it's still too early to do optimizations on the database schema,
but we should keep an eye on it and be prepared for potential future optimizations.
for example,
1. should enum where possible, such as Plan, Visibility, etc
2. create index on embedding and other fields that are frequently used for filtering
3. materialized views for frequently queried data
4. limit string length for fields that have string type
5. Note we might need to set up index for embedding manually for customizing the similarity search algorithm
   (https://github.com/pgvector/pgvector)
"""

# TODO: ideally shouldn't need it in python 3.12 for forward reference?
from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import Enum as SqlEnum

# Note: need to use postgresqlr ARRAY in order to use overlap operator
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column, relationship

from aci.common.db.custom_sql_types import (
    EncryptedSecurityCredentials,
    EncryptedSecurityScheme,
    Key,
)
from aci.common.enums import (
    APIKeyStatus,
    Protocol,
    SecurityScheme,
    StripeSubscriptionInterval,
    StripeSubscriptionStatus,
    Visibility,
)

EMBEDDING_DIMENSION = 1024
APP_DEFAULT_VERSION = "1.0.0"
# need app to be shorter because it's used as prefix for function name
APP_NAME_MAX_LENGTH = 100
MAX_STRING_LENGTH = 255


class Base(MappedAsDataclass, DeclarativeBase):
    pass


# TODO: might need to limit number of projects a user can create
class Project(Base):
    """
    Project is a logical container for isolating and managing API keys, selected apps, and other data
    Each project can have multiple agents (associated with API keys), which are logical actors that access our platform
    """

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )

    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    # if public, the project can only access public apps and functions
    # if private, the project can access all apps and functions, useful for A/B testing and internal testing before releasing
    # newly added apps and functions to public
    visibility_access: Mapped[Visibility] = mapped_column(SqlEnum(Visibility), nullable=False)

    """ quota related fields: TODO: TBD how to implement quota system """
    daily_quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, init=False)
    daily_quota_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    total_quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, init=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # deleting project will delete all associated resources under the project
    agents: Mapped[list[Agent]] = relationship(
        "Agent", lazy="select", cascade="all, delete-orphan", init=False
    )
    app_configurations: Mapped[list[AppConfiguration]] = relationship(
        "AppConfiguration", lazy="select", cascade="all, delete-orphan", init=False
    )
    linked_accounts: Mapped[list[LinkedAccount]] = relationship(
        "LinkedAccount", lazy="select", cascade="all, delete-orphan", init=False
    )


class Agent(Base):
    """
    Agent is an actor under a project, each project can have multiple agents.
    It's the logical entity that access our platform, as a result, api keys are associated with agents.
    This is an opinionated design, intented for a multi-agent system, but subject to change.
    """

    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # agent level control of what apps are accessible by the agent, should be asubset of project configured apps
    # we store a list of app names.
    # TODO: reconsider if this should be in a separate table to enforce data integrity, or use periodic task to clean up
    allowed_apps: Mapped[list[str]] = mapped_column(
        ARRAY(String(MAX_STRING_LENGTH)), nullable=False
    )
    # TODO: should we use JSONB instead? As this will be frequently queried
    # TODO: reconsider if this should be in a separate table to enforce data integrity, or use periodic task to clean up
    # Custom instructions for the agent to follow. The key is the function name, and the value is the instruction.
    custom_instructions: Mapped[dict[str, str]] = mapped_column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # Note: for now each agent has one API key, but we can add more flexibility in the future if needed
    # deleting agent will delete all API keys under the agent
    api_keys: Mapped[list[APIKey]] = relationship(
        "APIKey", lazy="select", cascade="all, delete-orphan", init=False
    )


class APIKey(Base):
    """
    APIKey is the authentication token to access the platform.
    In this opinionated design, api key belongs to an agent.
    """

    __tablename__ = "api_keys"

    # id is not the actual API key, it's just a unique identifier to easily reference each API key entry without depending
    # on the API key string itself. Also for logging without exposing the actual API key string.
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    # "key" is the encrypted actual API key string that the user will use to authenticate
    key: Mapped[str] = mapped_column(Key(), nullable=False, unique=True)
    key_hmac: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id"), unique=True, nullable=False
    )
    status: Mapped[APIKeyStatus] = mapped_column(SqlEnum(APIKeyStatus), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )


# TODO: how to do versioning for app and funcitons to allow backward compatibility, or we don't actually need to
# because function schema is loaded dynamically from the database to user
# TODO: do we need auth_required on function level?
class Function(Base):
    """
    Function is a callable function that can be executed.
    Each function belongs to one App.
    """

    __tablename__ = "functions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    app_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("apps.id"), nullable=False
    )
    # Note: the function name is unique across the platform and should have app information, e.g., "GITHUB_CLONE_REPO"
    # ideally this should just be <app name>_<function name> (uppercase)
    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    # if private, the function is only visible to privileged Projects (e.g., useful for internal and A/B testing)
    visibility: Mapped[Visibility] = mapped_column(SqlEnum(Visibility), nullable=False)
    # can be used to control if the app's discoverability
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    protocol: Mapped[Protocol] = mapped_column(SqlEnum(Protocol), nullable=False)
    protocol_data: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    # empty dict for function that takes no args
    parameters: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    # TODO: should response schema be generic (data + execution success of not + optional error) or specific to the function
    response: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    # TODO: should we provide EMBEDDING_DIMENSION here? which makes it less flexible if we want to change the embedding dimention in the future
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # the App that this function belongs to
    app: Mapped[App] = relationship("App", lazy="select", back_populates="functions", init=False)

    @property
    def app_name(self) -> str:
        return str(self.app.name)


class App(Base):
    __tablename__ = "apps"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    # Need name to be unique to support globally unique function name.
    name: Mapped[str] = mapped_column(String(APP_NAME_MAX_LENGTH), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    # provider (or company) of the app, e.g., google, github, or ACI or user (if allow user to create custom apps)
    provider: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    version: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    # if private, the app is only visible to privileged Projects (e.g., useful for internal and A/B testing)
    visibility: Mapped[Visibility] = mapped_column(SqlEnum(Visibility), nullable=False)
    # operational status of the app, can be used to control if the app's discoverability
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # security schemes (including it's config) supported by the app, e.g., API key, OAuth2, etc
    security_schemes: Mapped[dict[SecurityScheme, dict]] = mapped_column(
        MutableDict.as_mutable(EncryptedSecurityScheme),
        nullable=False,
    )
    # default security credentials (provided by ACI, if any) for the app that can be used by any client
    default_security_credentials_by_scheme: Mapped[dict[SecurityScheme, dict]] = mapped_column(
        MutableDict.as_mutable(EncryptedSecurityCredentials),
        nullable=False,
    )
    # embedding vector for similarity search
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSION), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # deleting app will delete all functions under the app
    functions: Mapped[list[Function]] = relationship(
        "Function",
        lazy="select",
        cascade="all, delete-orphan",
        back_populates="app",
        init=False,
    )


# TODO: We make the decision to only allow one configuration per app per project to avoid unjustified
# complexity and mental overhead on client side. (simplify apis and sdks) But we can revisit this decision
# if later a valid use case is found.
# TODO: should we delete app's associated linked accounts when user delete the app configuration?
# TODO: revisit if we should disallow client changing the security scheme after the record is created, to
# enforce consistant linked accounts type.
# TODO: Reconsider if "enabled_functions" should be in a separate table to enforce data integrity, or use periodic task to clean up
class AppConfiguration(Base):
    """
    App configuration is a configuration for an app in a project.
    A record is created when the user enable and configure an app to a project.
    """

    __tablename__ = "app_configurations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    app_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("apps.id"), nullable=False
    )
    # selected (by client) as default security scheme for the linking accounts. Although making security_scheme constant is easier for
    # implementation, we keep the flexibility for future use to allow user to select different security scheme for different linked accounts.
    # So, ultimately the actual security scheme and credentials should be decided by individual linked accounts
    # stored in linked_accounts table.
    security_scheme: Mapped[SecurityScheme] = mapped_column(SqlEnum(SecurityScheme), nullable=False)
    # can store security scheme override for each app, e.g., store client id and secret for OAuth2 if client
    # want to use their own OAuth2 app for whitelabeling
    # TODO: create a pydantic model for security scheme overrides once we finalize overridable fields
    security_scheme_overrides: Mapped[dict[SecurityScheme, dict]] = mapped_column(
        MutableDict.as_mutable(EncryptedSecurityScheme),
        nullable=False,
    )
    # controlled by users to enable or disable the app
    # TODO: what are the implications of enabling/disabling the app?
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # indicate if all functions of the app are enabled for this app
    all_functions_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # if all_functions_enabled is false, this list contains the unqiue names of the functions that are enabled for this app
    enabled_functions: Mapped[list[str]] = mapped_column(
        ARRAY(String(MAX_STRING_LENGTH)), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    app: Mapped[App] = relationship("App", lazy="select", init=False)

    @property
    def app_name(self) -> str:
        return str(self.app.name)

    # unique constraint
    __table_args__ = (
        # If in the future we want to allow a project to integrate the same app multiple times, we can remove the unique constraint
        # but that would require changes in other places (business logic and other tables)
        UniqueConstraint("project_id", "app_id", name="uc_project_app"),
    )


# TODO: table can get large if there are significant number of clients
# (O(n) = #clients * #projects_per_client * #apps * #linked_accounts_per_app)
# need to keep an eye out on performance and revisit if we should:
# - use nosql (or sharding) to store linked accounts instead.
# - use separate database instance for clients with large number of linked accounts
# - use separate tables per project. Some benefits including easier to delete the record and associated
#   linked accounts when user delete the app configuration, without locking the table for too long. But number of
#   tables can be too big for postgres.
class LinkedAccount(Base):
    """
    Linked account is a specific account under an app in a project.
    """

    __tablename__ = "linked_accounts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    app_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("apps.id"), nullable=False
    )
    # linked_account_owner_id should be unique per app per project, it should identify the end user, which
    # is the owner of the linked account. One common design is to use the same linked_account_owner_id that
    # identifies an end user for all configured apps in a project.
    linked_account_owner_id: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    security_scheme: Mapped[SecurityScheme] = mapped_column(SqlEnum(SecurityScheme), nullable=False)
    # security credentials are different for each security scheme, e.g., API key, OAuth2 (access token, refresh token, scope, etc) etc
    # it can beempty dict because the linked account could be created to use default credentials provided by ACI
    security_credentials: Mapped[dict] = mapped_column(
        MutableDict.as_mutable(EncryptedSecurityCredentials),
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=True, init=False
    )

    app: Mapped[App] = relationship("App", lazy="select", init=False)

    @property
    def app_name(self) -> str:
        return str(self.app.name)

    __table_args__ = (
        # TODO: write test
        UniqueConstraint(
            "project_id",
            "app_id",
            "linked_account_owner_id",
            name="uc_project_app_linked_account_owner",
        ),
    )

    # deleting linked account will delete all associated secrets
    secrets: Mapped[list[Secret]] = relationship(
        "Secret", lazy="select", cascade="all, delete-orphan", init=False
    )


class Secret(Base):
    __tablename__ = "secrets"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    linked_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("linked_accounts.id"), nullable=False
    )

    key: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    value: Mapped[bytes] = mapped_column(BYTEA, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    __table_args__ = (UniqueConstraint("linked_account_id", "key", name="uc_linked_account_key"),)


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False, unique=True)
    stripe_product_id: Mapped[str] = mapped_column(
        String(MAX_STRING_LENGTH), nullable=False, unique=True
    )
    stripe_monthly_price_id: Mapped[str] = mapped_column(
        String(MAX_STRING_LENGTH), nullable=False, unique=True
    )
    stripe_yearly_price_id: Mapped[str] = mapped_column(
        String(MAX_STRING_LENGTH), nullable=False, unique=True
    )
    features: Mapped[dict] = mapped_column(MutableDict.as_mutable(JSONB), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    org_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, unique=True)
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("plans.id"), nullable=False
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(MAX_STRING_LENGTH), nullable=False, unique=True
    )
    stripe_subscription_id: Mapped[str] = mapped_column(
        String(MAX_STRING_LENGTH), nullable=False, unique=True
    )
    status: Mapped[StripeSubscriptionStatus] = mapped_column(
        SqlEnum(StripeSubscriptionStatus), nullable=False
    )
    interval: Mapped[StripeSubscriptionInterval] = mapped_column(
        SqlEnum(StripeSubscriptionInterval), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )


class ProcessedStripeEvent(Base):
    __tablename__ = "processed_stripe_events"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    event_id: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )


__all__ = [
    "APIKey",
    "Agent",
    "App",
    "AppConfiguration",
    "Base",
    "Function",
    "LinkedAccount",
    "Project",
    "Secret",
]
