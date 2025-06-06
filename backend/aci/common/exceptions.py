from fastapi import status


class ACIException(Exception):  # noqa: N818
    """
    Base class for all ACI exceptions with consistent structure.

    Attributes:
        title (str): error title.
        message (str): an optional detailed error message.
        error_code (int): HTTP status code to identify the error type.
    """

    def __init__(
        self,
        title: str,
        message: str | None = None,
        error_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        super().__init__(title, message, error_code)
        self.title = title
        self.message = message
        self.error_code = error_code

    def __str__(self) -> str:
        """
        String representation that combines title and message (if available)
        """
        if self.message:
            return f"{self.title}: {self.message}"
        return self.title


class UnexpectedError(ACIException):
    """
    Exception raised when an unexpected error occurs
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Unexpected error",
            message=message,
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class AuthenticationError(ACIException):
    """
    Exception raised when an authentication error occurs
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Authentication error",
            message=message,
            error_code=status.HTTP_401_UNAUTHORIZED,
        )


class NoImplementationFound(ACIException):
    """
    Exception raised when a feature or function is not implemented
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="No implementation found",
            message=message,
            error_code=status.HTTP_501_NOT_IMPLEMENTED,
        )


class ProjectNotFound(ACIException):
    """
    Exception raised when a project is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Project not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class ProjectAccessDenied(ACIException):
    """
    Exception raised when a project is not accessible to a user
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Project access denied",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class OrgAccessDenied(ACIException):
    """
    Exception raised when an organization is not accessible to a user
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Org access denied",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class AppNotFound(ACIException):
    """
    Exception raised when an app is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class AppConfigurationNotFound(ACIException):
    """
    Exception raised when an app configuration is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App configuration not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class AppConfigurationDisabled(ACIException):
    """
    Exception raised when an app configuration is disabled
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App configuration disabled",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class AppConfigurationAlreadyExists(ACIException):
    """
    Exception raised when an app configuration already exists
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App configuration already exists",
            message=message,
            error_code=status.HTTP_409_CONFLICT,
        )


class AppSecuritySchemeNotSupported(ACIException):
    """
    Exception raised when a security scheme is not supported by an app
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Specified security scheme not supported by the app",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidBearerToken(ACIException):
    """
    Exception raised when a http bearer token is invalid
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid bearer token",
            message=message,
            error_code=status.HTTP_401_UNAUTHORIZED,
        )


class InvalidAPIKey(ACIException):
    """
    Exception raised when an API key is invalid
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid API key",
            message=message,
            error_code=status.HTTP_401_UNAUTHORIZED,
        )


class DailyQuotaExceeded(ACIException):
    """
    Exception raised when a daily quota is exceeded
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Daily quota exceeded",
            message=message,
            error_code=status.HTTP_401_UNAUTHORIZED,
        )


class MaxProjectsReached(ACIException):
    """
    Exception raised when a user/organization has reached the maximum number of projects
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Max projects reached",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class MaxAgentsReached(ACIException):
    """
    Exception raised when a project has reached the maximum number of agents
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Max agents reached",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class UserNotFound(ACIException):
    """
    Exception raised when a user is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="User not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class FunctionNotFound(ACIException):
    """
    Exception raised when a function is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Function not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class InvalidFunctionInput(ACIException):
    """
    Exception raised when a function input is invalid
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid function input",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidFunctionDefinitionFormat(ACIException):
    """
    Exception raised when an invalid function definition format is provided
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid function definition format",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )


class LinkedAccountAlreadyExists(ACIException):
    """
    Exception raised when a linked account already exists
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Linked account already exists",
            message=message,
            error_code=status.HTTP_409_CONFLICT,
        )


class LinkedAccountNotFound(ACIException):
    """
    Exception raised when a linked account is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Linked account not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class LinkedAccountDisabled(ACIException):
    """
    Exception raised when a linked account is disabled
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Linked account disabled",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class AgentNotFound(ACIException):
    """
    Exception raised when an agent is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Agent not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class AppNotAllowedForThisAgent(ACIException):
    """
    Exception raised when an app is not allowed to be used by an agent
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App not allowed for this agent",
            message=message,
            error_code=status.HTTP_401_UNAUTHORIZED,
        )


class CustomInstructionViolation(ACIException):
    """
    Exception raised when a function execution is reject due to a custom instruction
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Custom instruction violation",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class AgentSecretsManagerError(ACIException):
    """
    Exception raised when an error occurs in the Agent Secrets Manager
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Agent Secrets Manager error",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )


class DependencyCheckError(ACIException):
    """
    Exception raised when a dependency check fails
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Dependency check error",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )


class SubscriptionPlanNotFound(ACIException):
    """
    Exception raised when a plan is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Subscription plan not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class BillingError(ACIException):
    """
    Exception raised when a billing error occurs
    """

    def __init__(
        self,
        message: str | None = None,
        error_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(
            title="Billing error",
            message=message,
            error_code=error_code,
        )


class OAuth2Error(ACIException):
    """
    Exception raised when an OAuth2 error occurs
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="OAuth2 error",
            message=message,
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class MaxUniqueLinkedAccountOwnerIdsReached(ACIException):
    """Raised when an organization has reached its maximum allowed linked accounts for an app."""

    def __init__(self, plan: str | None = None, message: str | None = None):
        title = "Max unique linked account owner ids reached"
        if plan:
            title = f"{title} for the {plan} plan"
        super().__init__(
            title=title,
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )


class ProjectCreationError(ACIException):
    """
    Exception raised when there is an error creating a project
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Failed to create project",
            message=message,
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ProjectIsLastInOrgError(ACIException):
    """
    Exception raised when a project cannot be deleted
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Project is the last in the organization",
            message=message,
            error_code=status.HTTP_409_CONFLICT,
        )


class MaxAgentSecretsReached(ACIException):
    """
    Exception raised when a project has reached the maximum number of agent secrets allowed by their subscription plan
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Max agent secrets reached",
            message=message,
            error_code=status.HTTP_403_FORBIDDEN,
        )
