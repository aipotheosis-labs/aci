from enum import StrEnum


class APIKeyStatus(StrEnum):
    ACTIVE = "active"
    # can only be disabled by aipolabs
    DISABLED = "disabled"
    # TODO: this is soft delete (requested by user), in the future might consider hard delete and keep audit logs somewhere else
    DELETED = "deleted"


class SecurityScheme(StrEnum):
    """
    security scheme type for an app (or function if support override)
    """

    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    HTTP_BASIC = "http_basic"
    HTTP_BEARER = "http_bearer"
    OAUTH2 = "oauth2"


class Protocol(StrEnum):
    """
    function protocol type
    ideally all functions under the same app should use the same protocol, but we don't enforce that for maximum flexibility
    """

    REST = "rest"
    CONNECTOR = "connector"
    # GRAPHQL = "graphql"
    # WEBSOCKET = "websocket"
    # GRPC = "grpc"


class HttpLocation(StrEnum):
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


# TODO: use lowercase for consistency?
class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class EntityType(StrEnum):
    ENTITY = "entity"
    USER = "user"
    ORGANIZATION = "organization"


class Visibility(StrEnum):
    """visibility of an app or function"""

    PUBLIC = "public"
    PRIVATE = "private"


class SubscriptionPlan(StrEnum):
    """
    subscription plan for a user or organization.
    """

    CUSTOM = "custom"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    """
    subscription status for a user or organization.
    """

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrganizationRole(StrEnum):
    """
    role for a user in an organization.
    """

    ADMIN = "admin"
    MEMBER = "member"


class FunctionDefinitionFormat(StrEnum):
    """
    format for a function definition.
    """

    BASIC = "basic"  # only return name and description
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class ClientIdentityProvider(StrEnum):
    GOOGLE = "google"
    # GITHUB = "github"
