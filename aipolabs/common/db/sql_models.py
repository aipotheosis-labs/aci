"""
Note: try to keep dependencies on other internal packages to a minimum.
Note: at the time of writing, it's still too early to do optimizations on the database schema,
but we should keep an eye on it and be prepared for potential future optimizations.
for example,
1. should enum where possible, such as Plan, Visibility, etc
2. create index on embedding and other fields that are frequently used for filtering
3. materialized views for frequently queried data
4. limit string length for fields that have string type
"""

# TODO: ideally shouldn't need it in python 3.12 for forward reference?
from __future__ import annotations

import datetime
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint, func

# Note: need to use postgresqlr ARRAY in order to use overlap operator
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)

from aipolabs.common.enums import (
    APIKeyStatus,
    Plan,
    Protocol,
    SecurityScheme,
    Visibility,
)

EMBEDDING_DIMENTION = 1024
APP_DEFAULT_VERSION = "1.0.0"
# need app to be shorter because it's used as prefix for function name
APP_NAME_MAX_LENGTH = 100
MAX_STRING_LENGTH = 255


class Base(MappedAsDataclass, DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)


# TODO: Note we might need to set up index for embedding manually for customizing the similarity search algorithm
# (https://github.com/pgvector/pgvector)
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    # google, github, email, etc
    auth_provider: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    # google id, github id, email, etc
    auth_user_id: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    email: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    profile_picture: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[Plan] = mapped_column(SqlEnum(Plan), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # deleting user will delete all projects owned by the user
    owned_projects: Mapped[list[Project]] = relationship(
        "Project",
        lazy="select",
        cascade="all, delete-orphan",
        foreign_keys="Project.owner_user_id",
        init=False,
    )

    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_user_id", name="uc_auth_provider_user"),
    )


# logical container for isolating and managing API keys, selected apps, and other data
# each project can have multiple API keys
# TODO: might need to limit number of projects a user can create
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    # Note: creator is not necessarily the owner
    # should be a user and should be the same as owner_user_id if owner is of type user
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    # owner of the project can be a user or an organization, here we have both fields as ForeignKey instead of (owner_type + owner_id)
    # to enforce db integrity
    owner_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    owner_organization_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    # if public, the project can only access public apps and functions
    # if private, the project can access all apps and functions, useful for A/B testing and internal testing before releasing
    # newly added apps and functions to public
    visibility_access: Mapped[Visibility] = mapped_column(SqlEnum(Visibility), nullable=False)

    """ quota related fields: TODO: TBD how to implement quota system """
    daily_quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, init=False)
    daily_quota_reset_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    total_quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False, init=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # deleting project will delete all agents under the project
    agents: Mapped[list[Agent]] = relationship(
        "Agent", lazy="select", cascade="all, delete-orphan", init=False
    )

    # check constraint to ensure project owner is either a user or an organization
    __table_args__ = (
        CheckConstraint(
            "(owner_user_id IS NOT NULL AND owner_organization_id IS NULL) OR "
            "(owner_user_id IS NULL AND owner_organization_id IS NOT NULL)",
            name="cc_project_owner",
        ),
    )


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # agent level control of what apps and functions are not accessible by the agent, apart from the project level control
    # TODO: reconsider if this should be in a separate table to enforce data integrity, or use periodic task to clean up
    excluded_apps: Mapped[list[UUID]] = mapped_column(ARRAY(PGUUID(as_uuid=True)), nullable=False)
    excluded_functions: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
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
    __tablename__ = "api_keys"

    # id is not the actual API key, it's just a unique identifier to easily reference each API key entry without depending
    # on the API key string itself.
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    # "key" is the actual API key string that the user will use to authenticate
    key: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False, unique=True)
    agent_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id"), unique=True, nullable=False
    )
    status: Mapped[APIKeyStatus] = mapped_column(SqlEnum(APIKeyStatus), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
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
    # if false, the function is not visible and will not be searchable and executable
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    protocol: Mapped[Protocol] = mapped_column(SqlEnum(Protocol), nullable=False)
    protocol_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # empty dict for function that takes no args
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    # TODO: should response schema be generic (data + execution success of not + optional error) or specific to the function
    response: Mapped[dict] = mapped_column(JSON, nullable=False)
    # TODO: should we provide EMBEDDING_DIMENTION here? which makes it less flexible if we want to change the embedding dimention in the future
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENTION), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # each function belongs to one app
    app: Mapped[App] = relationship("App", lazy="select", back_populates="functions", init=False)


class App(Base):
    __tablename__ = "apps"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    # Need name to be unique to support both sdk (where user can specify apps by name) and globally unique function name.
    name: Mapped[str] = mapped_column(String(APP_NAME_MAX_LENGTH), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    # provider (or company) of the app, e.g., google, github, or aipolabs or user (if allow user to create custom apps)
    provider: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    version: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    # if private, the app is only visible to privileged Projects (e.g., useful for internal and A/B testing)
    visibility: Mapped[Visibility] = mapped_column(SqlEnum(Visibility), nullable=False)
    # operational status of the app
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # security schemes and it's config supported by the app, e.g., API key, OAuth2, etc
    security_schemes: Mapped[dict] = mapped_column(JSON, nullable=False)
    # embedding vector for similarity search
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENTION), nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # deleting app will delete all functions under the app
    functions: Mapped[list[Function]] = relationship(
        "Function", lazy="select", cascade="all, delete-orphan", back_populates="app", init=False
    )


# A user can have multiple projects, a project can integrate multiple apps, an app can have multiple linked accounts.
# Same app in different projects need to authenticate user accounts separately.
# When a user first create a project, there is no record for that project in this table,
# the record is created when the user select (enable) an app to the project.
# When user disable an app from the project, the record is not deleted, just the status is changed to disabled
# TODO: table can get large if there are too many users and each has many projects, need to keep an eye out on performance
# TODO: will it be necessary to store user selected security scheme type for the app here?
# TODO: will there be performance issue if we offer a button in dev portal to enable all apps at once?
# TODO: if App is disabled, should project_app_integration of that App also be disabled?
class ProjectAppIntegration(Base):
    __tablename__ = "project_app_integrations"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    app_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("apps.id"), nullable=False
    )
    # selected (by client) as default security scheme for the app integration. Although making security_scheme constant is easier for
    # implementation, we keep the flexibility for future use to allow user to select different security scheme for different linked accounts.
    # So, ultimately the actual security scheme and credentials should be decided by individual linked accounts
    # stored in linked_accounts table.
    security_scheme: Mapped[SecurityScheme | None] = mapped_column(
        SqlEnum(SecurityScheme), nullable=True
    )
    # controlled by users to enable or disable the app integration
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # exclude certain functions from the app.
    # TODO: Reconsider if this should be in a separate table to enforce data integrity, or use periodic task to clean up
    excluded_functions: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )

    # unique constraint
    # If in the future we want to allow the same project to integrate the same app multiple times, we can remove the unique constraint
    __table_args__ = (UniqueConstraint("project_id", "app_id", name="uc_project_app"),)


# a linked account is specific to an app in a project.
class LinkedAccount(Base):
    __tablename__ = "linked_accounts"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default_factory=uuid4, init=False
    )
    project_app_integration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("project_app_integrations.id"), nullable=False
    )
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    app_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("apps.id"), nullable=False
    )
    # account_name should be unique per app per project (or just per ProjectAppIntegration), ideally it identifies the end user.
    # Ideally this should be some user id in client's system that uniquely identify owner of the account.
    account_name: Mapped[str] = mapped_column(String(MAX_STRING_LENGTH), nullable=False)
    # here we assume it's possible to have linked account but no security credentials are required, in which case
    # security_scheme and security_credentials will be null
    security_scheme: Mapped[SecurityScheme | None] = mapped_column(
        SqlEnum(SecurityScheme), nullable=True
    )
    # security credentials are different for each security scheme, e.g., API key, OAuth2 (access token, refresh token, scope, etc) etc
    security_credentials: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False), server_default=func.now(), nullable=False, init=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        init=False,
    )
    __table_args__ = (
        UniqueConstraint(
            "project_app_integration_id", "account_name", name="uc_project_app_account_name"
        ),
        # For each app in a project, the account_name should be unique.
        # Technically this is redundant because of the unique contrainst above plus UniqueConstraint("project_id", "app_id", name="uc_project_app") in project_app_integrations table,
        # but add it here in case we want to remove UniqueConstraint("project_id", "app_id", name="uc_project_app") in the future
        UniqueConstraint(
            "project_id", "app_id", "account_name", name="uc_project_app_account_name"
        ),
        # Add a foreign key constraint to ensure consistency with project_app_integration
        CheckConstraint(
            """
            EXISTS (
                SELECT 1 FROM project_app_integrations
                WHERE id = project_app_integration_id
                AND project_id = project_id
                AND app_id = app_id
            )
            """,
            name="cc_linked_account_project_app_consistency",
        ),
    )
