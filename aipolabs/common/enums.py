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

    API_KEY = "api_key"
    HTTP_BASIC = "http_basic"
    HTTP_BEARER = "http_bearer"
    OAUTH2_PASSWORD = "oauth2_password"
    OAUTH2_AUTH_CODE = "oauth2_auth_code"
    OAUTH2_AUTH_IMPLICIT = "oauth2_auth_implicit"
    OPEN_ID_CONNECT = "open_id_connect"


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


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ProjectOwnerType(str, Enum):
    USER = "user"
    ORGANIZATION = "organization"


class Visibility(str, Enum):
    """visibility of an app or function"""

    PUBLIC = "public"
    PRIVATE = "private"


class Plan(str, Enum):
    CUSTOM = "custom"
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
