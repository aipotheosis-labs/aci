from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from aci.common.db import crud
from aci.common.enums import SecurityScheme
from aci.common.schemas.security_scheme import (
    APIKeySchemeCredentials,
    NoAuthSchemeCredentials,
    OAuth2SchemeCredentials,
)


@pytest.mark.parametrize(
    "security_scheme, credentials, should_raise",
    [
        (
            SecurityScheme.OAUTH2,
            OAuth2SchemeCredentials(
                client_id="test",
                client_secret="test",
                scope="test_scope_1 test_scope_2",
                access_token="test",
                refresh_token="test",
            ),
            False,
        ),
        (
            SecurityScheme.API_KEY,
            APIKeySchemeCredentials(secret_key="test"),
            False,
        ),
        (SecurityScheme.NO_AUTH, NoAuthSchemeCredentials(), False),
        (SecurityScheme.OAUTH2, APIKeySchemeCredentials(secret_key="test"), True),
        (SecurityScheme.API_KEY, NoAuthSchemeCredentials(), True),
        (SecurityScheme.NO_AUTH, APIKeySchemeCredentials(secret_key="test"), True),
    ],
)
def test_update_linked_account_credentials(
    security_scheme: SecurityScheme,
    credentials: OAuth2SchemeCredentials | APIKeySchemeCredentials | NoAuthSchemeCredentials,
    should_raise: bool,
) -> None:
    # Setup mocks
    mock_db_session = MagicMock()
    mock_linked_account = MagicMock()
    mock_linked_account.security_scheme = security_scheme
    mock_linked_account.id = uuid4()

    if should_raise:
        with pytest.raises(ValueError):
            crud.linked_accounts.update_linked_account_credentials(
                mock_db_session, mock_linked_account, credentials
            )
    else:
        result = crud.linked_accounts.update_linked_account_credentials(
            mock_db_session, mock_linked_account, credentials
        )

        assert result == mock_linked_account
        mock_linked_account.security_credentials = credentials.model_dump(mode="json")
        mock_db_session.flush.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_linked_account)
