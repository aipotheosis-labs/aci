from fastapi import status


class AipolabsException(Exception):
    """
    Base class for all Aipolabs exceptions with consistent structure.

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


class UnknownException(AipolabsException):
    """
    Exception raised when an unknown error occurs
    """

    def __init__(
        self,
        title: str = "An unknown error occurred",
        message: str | None = None,
        error_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        super().__init__(title=title, message=message, error_code=error_code)


class UnexpectedException(AipolabsException):
    """
    Exception raised when an unexpected error occurs
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Unexpected error",
            message=message,
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class AuthenticationError(AipolabsException):
    """
    Exception raised when an authentication error occurs
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Authentication error",
            message=message,
            error_code=status.HTTP_401_UNAUTHORIZED,
        )


class NoImplementationFound(AipolabsException):
    """
    Exception raised when a feature or function is not implemented
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="No implementation found",
            message=message,
            error_code=status.HTTP_501_NOT_IMPLEMENTED,
        )


class ProjectNotFound(AipolabsException):
    """
    Exception raised when a project is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Project not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class ProjectAccessDenied(AipolabsException):
    """
    Exception raised when a project is not accessible to a user
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Project access denied", message=message, error_code=status.HTTP_403_FORBIDDEN
        )


class AppNotFound(AipolabsException):
    """
    Exception raised when an app is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class AppConfigurationNotFound(AipolabsException):
    """
    Exception raised when an app configuration is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App configuration not found",
            message=message,
            error_code=status.HTTP_404_NOT_FOUND,
        )


class AppConfigurationAlreadyExists(AipolabsException):
    """
    Exception raised when an app configuration already exists
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="App configuration already exists",
            message=message,
            error_code=status.HTTP_409_CONFLICT,
        )


class AppSecuritySchemeNotSupported(AipolabsException):
    """
    Exception raised when a security scheme is not supported by an app
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Specified security scheme not supported by the app",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidBearerToken(AipolabsException):
    """
    Exception raised when a http bearer token is invalid
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid bearer token", message=message, error_code=status.HTTP_401_UNAUTHORIZED
        )


class InvalidAPIKey(AipolabsException):
    """
    Exception raised when an API key is invalid
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid API key", message=message, error_code=status.HTTP_401_UNAUTHORIZED
        )


class DailyQuotaExceeded(AipolabsException):
    """
    Exception raised when a daily quota is exceeded
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Daily quota exceeded", message=message, error_code=status.HTTP_401_UNAUTHORIZED
        )


class UserNotFound(AipolabsException):
    """
    Exception raised when a user is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="User not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class FunctionNotFound(AipolabsException):
    """
    Exception raised when a function is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Function not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class InvalidFunctionInput(AipolabsException):
    """
    Exception raised when a function input is invalid
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Invalid function input", message=message, error_code=status.HTTP_400_BAD_REQUEST
        )


class LinkedAccountNotFound(AipolabsException):
    """
    Exception raised when a linked account is not found
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Linked account not found", message=message, error_code=status.HTTP_404_NOT_FOUND
        )


class LinkedAccountOAuth2Error(AipolabsException):
    """
    Exception raised when an OAuth2 error occurs
    """

    def __init__(self, message: str | None = None):
        super().__init__(
            title="Linked account OAuth2 error",
            message=message,
            error_code=status.HTTP_400_BAD_REQUEST,
        )
