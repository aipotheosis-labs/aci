from enum import StrEnum


class APIKeyStatus(StrEnum):
    ACTIVE = "active"
    # can only be disabled by ACI
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


class Visibility(StrEnum):
    """visibility of an app or function"""

    PUBLIC = "public"
    PRIVATE = "private"


class OrganizationRole(StrEnum):
    """
    role for a user in an organization.
    """

    OWNER = "Owner"
    ADMIN = "Admin"
    MEMBER = "Member"


class FunctionDefinitionFormat(StrEnum):
    """
    format for a function definition.
    """

    BASIC = "basic"  # only return name and description
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENAI_RESPONSES = "openai_responses"


class ClientIdentityProvider(StrEnum):
    GOOGLE = "google"
    # GITHUB = "github"


class StripeSubscriptionStatus(StrEnum):
    """
    Stripe subscription status: https://docs.stripe.com/api/subscriptions/object#subscription_object-status
    """

    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class StripeSubscriptionInterval(StrEnum):
    """
    Stripe recurring interval: https://docs.stripe.com/api/subscriptions/object#subscription_object-items-data-price-recurring-interval
    We only have month and year. Stripe also has day and week.
    """

    MONTH = "month"
    YEAR = "year"
