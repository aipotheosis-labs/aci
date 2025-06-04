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
        mock_auth.return_value.invite_user_to_org.return_value = None

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


def test_invite_member_unauthorized(
    test_client: TestClient,
    dummy_user_2: DummyUser,
) -> None:
    """Test that a non-admin user cannot invite members."""
    response = test_client.post(
        f"{config.ROUTER_PREFIX_ORGANIZATIONS}/invite",
        json={
            "email": "new_member@example.com",
            "role": OrganizationRole.MEMBER,
        },
        headers={
            "Authorization": f"Bearer {dummy_user_2.access_token}",
            "X-ACI-ORG-ID": str(dummy_user_2.org_id),
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_member(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that an admin can remove a member from the organization."""
    with patch("aci.server.acl.get_propelauth") as mock_auth:
        mock_auth.return_value.remove_user_from_org.return_value = None

        response = test_client.delete(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members/some_member_id",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_remove_self(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test that a member can remove themselves."""
    with patch("aci.server.acl.get_propelauth") as mock_auth:
        mock_auth.return_value.remove_user_from_org.return_value = None

        response = test_client.delete(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members/{dummy_user.propel_auth_user.user_id}",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


def test_remove_member_unauthorized(
    test_client: TestClient,
    dummy_user_2: DummyUser,
) -> None:
    """Test that a non-admin user cannot remove other members."""
    response = test_client.delete(
        f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members/some_other_member_id",
        headers={
            "Authorization": f"Bearer {dummy_user_2.access_token}",
            "X-ACI-ORG-ID": str(dummy_user_2.org_id),
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_members(
    test_client: TestClient,
    dummy_user: DummyUser,
) -> None:
    """Test listing organization members."""
    with patch("aci.server.acl.get_propelauth") as mock_auth:
        mock_auth.return_value.fetch_users_in_org.return_value.users = [
            type(
                "User",
                (),
                {
                    "user_id": "user1",
                    "email": "user1@example.com",
                    "org_id_to_org_info": {
                        str(dummy_user.org_id): {
                            "user_role": OrganizationRole.OWNER,
                        }
                    },
                    "first_name": "User",
                    "last_name": "One",
                },
            ),
            type(
                "User",
                (),
                {
                    "user_id": "user2",
                    "email": "user2@example.com",
                    "org_id_to_org_info": {
                        str(dummy_user.org_id): {
                            "user_role": OrganizationRole.MEMBER,
                        }
                    },
                    "first_name": "User",
                    "last_name": "Two",
                },
            ),
        ]

        response = test_client.get(
            f"{config.ROUTER_PREFIX_ORGANIZATIONS}/members",
            headers={
                "Authorization": f"Bearer {dummy_user.access_token}",
                "X-ACI-ORG-ID": str(dummy_user.org_id),
            },
        )
        assert response.status_code == status.HTTP_200_OK
        members = response.json()
        assert len(members) == 2
        assert members[0]["user_id"] == "user1"
        assert members[0]["role"] == OrganizationRole.OWNER
        assert members[1]["user_id"] == "user2"
        assert members[1]["role"] == OrganizationRole.MEMBER
