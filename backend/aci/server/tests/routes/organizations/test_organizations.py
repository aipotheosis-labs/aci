from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from aci.common.enums import OrganizationRole
from aci.server import config
from aci.server.tests.conftest import DummyUser


def test_invite_user(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that an admin can invite a user to the organization."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        # Mock the required methods
        mock_auth.require_org_member_with_minimum_role.return_value = None
        mock_auth.invite_user_to_org.return_value = None

        response = test_client.post(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/invite_user",
            json={
                "email": "new_user@example.com",
                "role": OrganizationRole.MEMBER,
            },
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_auth.invite_user_to_org.assert_called_once_with(
            org_id=str(dummy_user.org_id),
            email="new_user@example.com",
            role=OrganizationRole.MEMBER,
        )


def test_cannot_invite_user_as_owner(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that you cannot invite a user with the OWNER role."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        # Mock the required methods
        mock_auth.require_org_member_with_minimum_role.return_value = None
        mock_auth.invite_user_to_org.return_value = None

        response = test_client.post(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/invite_user",
            json={
                "email": "new_owner@example.com",
                "role": OrganizationRole.OWNER,
            },
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
            },
        )
        # This should fail - we don't allow inviting owners
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # The auth method should not be called since validation should fail first
        mock_auth.invite_user_to_org.assert_not_called()


def test_remove_user(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that an admin can remove a user from the organization."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        mock_auth.require_org_member_with_minimum_role.return_value = None
        mock_auth.remove_user_from_org.return_value = None

        response = test_client.delete(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/users/some_user_id",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_auth.remove_user_from_org.assert_called_once_with(
            org_id=str(dummy_user.org_id), user_id="some_user_id"
        )


def test_remove_self(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that a user can remove themselves."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        mock_auth.remove_user_from_org.return_value = None
        dummy_user.propel_auth_user.org_id_to_org_member_info[
            str(dummy_user.org_id)
        ].user_assigned_role = OrganizationRole.MEMBER

        response = test_client.delete(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/users/{dummy_user.propel_auth_user.user_id}",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_auth.remove_user_from_org.assert_called_once_with(
            org_id=str(dummy_user.org_id), user_id=dummy_user.propel_auth_user.user_id
        )


def test_owner_cannot_remove_self(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that an organization owner cannot remove themselves."""
    # Note: dummy_user is already configured as an OWNER in conftest.py
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_ORGANIZATIONS}/users/{dummy_user.propel_auth_user.user_id}",
        headers={
            "Authorization": f"Bearer {dummy_user.access_token}",
            config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_users(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test listing organization users."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        # Mock the required methods
        mock_auth.require_org_member.return_value = None

        # Create a simple mock response with one user
        mock_response = type(
            "UsersPaged",
            (),
            {
                "users": [
                    type(
                        "User",
                        (),
                        {
                            "user_id": "user1",
                            "email": "user1@example.com",
                            "org_id_to_org_info": {
                                str(dummy_user.org_id): {
                                    "user_role": OrganizationRole.MEMBER,
                                }
                            },
                            "first_name": "User",
                            "last_name": "One",
                        },
                    ),
                ]
            },
        )
        mock_auth.fetch_users_in_org.return_value = mock_response

        response = test_client.get(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/users",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                config.ACI_ORG_ID_HEADER: str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        assert len(users) == 1
        assert users[0]["user_id"] == "user1"
        assert users[0]["role"] == OrganizationRole.MEMBER
