from enum import Enum


class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    # can only be disabled by aipolabs
    DISABLED = "disabled"
    # TODO: this is soft delete (requested by user), in the future might consider hard delete and keep audit logs somewhere else
    DELETED = "deleted"


class SecurityScheme(str, Enum):
    """
    security scheme type for an app (or function if support override)
    """

    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    HTTP_BASIC = "http_basic"
    HTTP_BEARER = "http_bearer"
    OAUTH2 = "oauth2"


class Protocol(str, Enum):
    """
    function protocol type
    ideally all functions under the same app should use the same protocol, but we don't enforce that for maximum flexibility
    """

    REST = "rest"
    # GRAPHQL = "graphql"
    # WEBSOCKET = "websocket"
    # GRPC = "grpc"


class HttpLocation(str, Enum):
    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"


# TODO: use lowercase for consistency?
class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class EntityType(str, Enum):
    ENTITY = "entity"
    USER = "user"
    ORGANIZATION = "organization"


class Visibility(str, Enum):
    """visibility of an app or function"""

    PUBLIC = "public"
    PRIVATE = "private"


class SubscriptionPlan(str, Enum):
    """
    subscription plan for a user or organization.
    """

    CUSTOM = "custom"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """
    subscription status for a user or organization.
    """

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class OrganizationRole(str, Enum):
    """
    role for a user in an organization.
    """

    ADMIN = "admin"
    MEMBER = "member"
