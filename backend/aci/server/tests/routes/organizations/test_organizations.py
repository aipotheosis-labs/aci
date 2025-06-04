from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from aci.common.enums import OrganizationRole
from aci.server import config
from aci.server.tests.conftest import DummyUser


def test_invite_member(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that an admin can invite a member to the organization."""
    with patch("aci.server.acl.get_propelauth") as mock_auth:
        # Mock the required methods
        mock_auth.require_org_member_with_minimum_role.return_value = None
        mock_auth.invite_user_to_org.return_value = None

        response = test_client.post(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/invite",
            json={
                "email": "new_member@example.com",
                "role": OrganizationRole.MEMBER,
            },
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_remove_member(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that an admin can remove a member from the organization."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        mock_auth.require_org_member_with_minimum_role.return_value = None
        mock_auth.remove_user_from_org.return_value = None

        response = test_client.delete(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members/some_member_id",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_auth.remove_user_from_org.assert_called_once_with(
            org_id=str(dummy_user.org_id), user_id="some_member_id"
        )


def test_remove_self(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that a member can remove themselves."""
    with patch("aci.server.routes.organizations.auth") as mock_auth:
        mock_auth.remove_user_from_org.return_value = None

        response = test_client.delete(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members/{dummy_user.propel_auth_user.user_id}",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_auth.remove_user_from_org.assert_called_once_with(
            org_id=str(dummy_user.org_id), user_id=dummy_user.propel_auth_user.user_id
        )


def test_list_members(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test listing organization members."""
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
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_200_OK
        members = response.json()
        assert len(members) == 1
        assert members[0]["user_id"] == "user1"
        assert members[0]["role"] == OrganizationRole.MEMBER
