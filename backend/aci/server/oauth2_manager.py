import random
import string
import time
from typing import Any, cast

from authlib.integrations.httpx_client import AsyncOAuth2Client

from aci.common.exceptions import LinkedAccountOAuth2Error
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import OAuth2SchemeCredentials

UNICODE_ASCII_CHARACTER_SET = string.ascii_letters + string.digits
logger = get_logger(__name__)


class OAuth2Manager:
    def __init__(
        self,
        app_name: str,
        client_id: str,
        client_secret: str,
        scope: str,
        authorize_url: str,
        access_token_url: str,
        refresh_token_url: str,
        token_endpoint_auth_method: str | None = None,
    ):
        """
        Initialize the OAuth2Manager

        Args:
            client_id: The client ID of the OAuth2 client
            client_secret: The client secret of the OAuth2 client
            scope: The scope of the OAuth2 client
            authorize_url: The URL of the OAuth2 authorization server
            access_token_url: The URL of the OAuth2 access token server
            refresh_token_url: The URL of the OAuth2 refresh token server
            token_endpoint_auth_method:
                client_secret_basic (default) or client_secret_post or none
                Additional options can be achieved by registering a custom auth method
        """
        self.app_name = app_name
        self.authorize_url = authorize_url
        self.access_token_url = access_token_url
        self.refresh_token_url = refresh_token_url

        self.oauth2_client = AsyncOAuth2Client(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint_auth_method=token_endpoint_auth_method,
            scope=scope,
            code_challenge_method="S256",  # only S256 is supported
            # TODO: use update_token callback to save tokens to the database
            update_token=None,
        )

    # TODO: some app may not support "code_verifier"?
    async def create_authorization_url(
        self,
        redirect_uri: str,
        state: str,
        code_verifier: str,
        access_type: str = "offline",
        prompt: str = "consent",
    ) -> str:
        """
        Create authorization URL for user to authorize your application

        Args:
            client: AsyncOAuth2Client instance
            authorization_endpoint: Authorization URL
            state: Optional state parameter for CSRF protection
            scope: OAuth2 scopes (space-separated)
            **kwargs: Additional parameters to include in authorization request

        Returns:
            Tuple of (authorization_url, state)
        """

        # TODO: some oauth2 apps may have unconventional params, temporarily handle them here
        app_specific_params = {}
        if self.app_name == "REDDIT":
            app_specific_params = {
                "duration": "permanent",
            }
            logger.info(
                "adding app specific params",
                extra={"app_name": self.app_name, "params": app_specific_params},
            )
        # TODO:
        # - "scope" can be specified here
        # - "response_type" can be specified here (default is "code")
        # - and additional options can be specified here (like access_type, prompt, etc.)
        authorization_url, _ = self.oauth2_client.create_authorization_url(
            url=self.authorize_url,
            redirect_uri=redirect_uri,
            state=state,
            code_verifier=code_verifier,
            access_type=access_type,
            prompt=prompt,
            **app_specific_params,
        )

        # TODO: remove PII log
        logger.error(
            "OAuth2Manager.create_authorization_url",
            extra={"authorization_url": authorization_url},
        )

        return str(authorization_url)

    # TODO: some app may not support "code_verifier"?
    async def fetch_token(
        self,
        redirect_uri: str,
        code: str,
        code_verifier: str,
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token

        Args:
            client: AsyncOAuth2Client instance
            token_endpoint: Token URL
            authorization_response: Full callback URL with code
            code: Authorization code (alternative to authorization_response)
            token_storage: Optional token storage mechanism
            user_id: User identifier for token storage
            **kwargs: Additional parameters for token request

        Returns:
            Token response dictionary
        """
        # Can use either full response URL or just the code
        token = cast(
            dict[str, Any],
            await self.oauth2_client.fetch_token(
                self.access_token_url,
                redirect_uri=redirect_uri,
                code=code,
                code_verifier=code_verifier,
            ),
        )

        # TODO: remove PII log
        logger.error(
            "OAuth2Manager.fetch_token",
            extra={"token": token},
        )

        # TODO: handle openid?

        return token

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> dict[str, Any]:
        """
        Refresh an access token

        Args:
            client: AsyncOAuth2Client instance with refresh token
            token_endpoint: Token URL
            token_storage: Optional token storage mechanism
            user_id: User identifier for token storage
            **kwargs: Additional parameters for refresh request

        Returns:
            Updated token dictionary
        """
        token = cast(
            dict[str, Any],
            await self.oauth2_client.refresh_token(
                self.refresh_token_url, refresh_token=refresh_token
            ),
        )

        # TODO: remove PII log
        logger.error(
            "OAuth2Manager.refresh_token",
            extra={"token": token},
        )

        return token

    @staticmethod
    def generate_code_verifier(length: int = 48) -> str:
        """
        Generate a random code verifier for OAuth2
        """
        rand = random.SystemRandom()
        return "".join(rand.choice(UNICODE_ASCII_CHARACTER_SET) for _ in range(length))

    @staticmethod
    def rewrite_oauth2_authorization_url(app_name: str, authorization_url: str) -> str:
        """
        Rewrite OAuth2 authorization URL for specific apps that need special handling.
        Currently handles Slack's special case where user scopes and scopes need to be replaced.
        TODO: this approach is hacky and need to refactor this in the future

        Args:
            app_name: Name of the OAuth2 app (e.g., 'slack')
            authorization_url: The original authorization URL

        Returns:
            The rewritten authorization URL if needed, otherwise the original URL
        """
        if app_name == "SLACK":
            # Slack requires user scopes to be prefixed with 'user_'
            # Replace 'scope=' with 'user_scope=' and add 'scope=' with the null value
            if "scope=" in authorization_url:
                # Extract the original scope value
                scope_start = authorization_url.find("scope=") + 6
                scope_end = authorization_url.find("&", scope_start)
                if scope_end == -1:
                    scope_end = len(authorization_url)
                original_scope = authorization_url[scope_start:scope_end]

                # Replace the original scope with user_scope and add scope
                new_url = authorization_url.replace(
                    f"scope={original_scope}", f"user_scope={original_scope}&scope="
                )
                return new_url

        return authorization_url

    @staticmethod
    def parse_oauth2_security_credentials(
        app_name: str, token_response: dict
    ) -> OAuth2SchemeCredentials:
        """
        Parse OAuth2SchemeCredentials from token response with app-specific handling.

        Args:
            app_name: Name of the app/provider (e.g., "SLACK", "GOOGLE")
            token_response: OAuth2 token response from provider

        Returns:
            OAuth2SchemeCredentials with appropriate fields set
        """
        if app_name == "SLACK":
            authed_user = token_response.get("authed_user", {})
            if not authed_user or "access_token" not in authed_user:
                logger.error(f"Invalid Slack OAuth response: {token_response}")
                raise LinkedAccountOAuth2Error("Invalid Slack OAuth response")

            return OAuth2SchemeCredentials(
                access_token=authed_user["access_token"],
                token_type=authed_user.get("token_type"),
                refresh_token=authed_user.get("refresh_token"),
                expires_at=int(time.time()) + authed_user.get("expires_in")
                if authed_user.get("expires_in")
                else None,
                raw_token_response=token_response,
            )

        if "access_token" not in token_response:
            logger.error(f"Missing access token in OAuth response: {token_response}")
            raise LinkedAccountOAuth2Error("Missing access token in OAuth response")

        return OAuth2SchemeCredentials(
            access_token=token_response["access_token"],
            token_type=token_response.get("token_type"),
            expires_at=int(time.time()) + token_response["expires_in"]
            if "expires_in" in token_response
            else None,
            refresh_token=token_response.get("refresh_token"),
            raw_token_response=token_response,
        )

    # def create_token_update_callback(token_storage, user_id: str) -> Callable:
    #     """
    #     Create a callback function to handle token updates

    #     Args:
    #         token_storage: Token storage mechanism
    #         user_id: User identifier

    #     Returns:
    #         Callback function for update_token
    #     """

    #     async def update_token(token, refresh_token=None, access_token=None):
    #         if token_storage:
    #             await token_storage.save_token(token, user_id=user_id)

    #     return update_token
