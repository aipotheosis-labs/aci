# type: ignore
# ruff: noqa

from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from propelauth_py import (
    Auth,
    SamlIdpMetadata,
    StepUpMfaGrantType,
    StepUpMfaVerifyTotpResponse,
    TokenVerificationMetadata,
)
from propelauth_py.api import (
    OrgQueryOrderBy,
    UserQueryOrderBy,
)
from propelauth_py.errors import ForbiddenException, UnauthorizedException
from propelauth_py.user import OrgMemberInfo, User

_security = HTTPBearer(auto_error=False)


def _require_org_member_wrapper(auth, debug_mode: bool):
    def require_org_member(user: User, required_org_id: str):
        try:
            return auth.validate_org_access_and_get_org(user, required_org_id)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, debug_mode)

    return require_org_member


def _require_org_member_with_minimum_role_wrapper(auth, debug_mode: bool):
    def require_org_member_with_minimum_role(
        user: User, required_org_id: str, minimum_required_role: str
    ):
        try:
            return auth.validate_minimum_org_role_and_get_org(
                user, required_org_id, minimum_required_role
            )
        except ForbiddenException as e:
            _handle_forbidden_exception(e, debug_mode)

    return require_org_member_with_minimum_role


def _require_org_member_with_exact_role_wrapper(auth, debug_mode: bool):
    def require_org_member_with_exact_role(user: User, required_org_id: str, role: str):
        try:
            return auth.validate_exact_org_role_and_get_org(user, required_org_id, role)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, debug_mode)

    return require_org_member_with_exact_role


def _require_org_member_with_permission_wrapper(auth, debug_mode: bool):
    def require_org_member_with_permission(user: User, required_org_id: str, permission: str):
        try:
            return auth.validate_permission_and_get_org(user, required_org_id, permission)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, debug_mode)

    return require_org_member_with_permission


def _require_org_member_with_all_permissions_wrapper(auth, debug_mode: bool):
    def require_org_member_with_all_permissions(
        user: User, required_org_id: str, permissions: list[str]
    ):
        try:
            return auth.validate_all_permissions_and_get_org(user, required_org_id, permissions)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, debug_mode)

    return require_org_member_with_all_permissions


def _handle_forbidden_exception(e: ForbiddenException, debug_mode: bool):
    if debug_mode:
        raise HTTPException(status_code=403, detail=e.message)
    else:
        raise HTTPException(status_code=403)


class FastAPIAuth:
    def __init__(
        self,
        auth_url: str,
        integration_api_key: str,
        token_verification_metadata: TokenVerificationMetadata | None,
        debug_mode: bool,
    ):
        self.auth_url = auth_url
        self.integration_api_key = integration_api_key
        self.token_verification_metadata = token_verification_metadata
        self.debug_mode = debug_mode
        self.auth = Auth(auth_url, integration_api_key, None)

    def require_user(self, credentials: HTTPAuthorizationCredentials = Depends(_security)):
        try:
            try:
                decoded_payload = jwt.decode(
                    credentials.credentials,
                    options={"verify_signature": False, "verify_aud": False},
                )
            except jwt.DecodeError as e:
                print(f"Error decoding JWT: {e}")

            # Use the decoded payload to populate the User object
            user_id = decoded_payload.get("user_id")
            email = decoded_payload.get("email")
            org_info_dict = decoded_payload.get("org_id_to_org_member_info", {})
            login_method = decoded_payload.get("login_method", {})

            org_id_to_org_member_info = {}
            for org_id, org_data in org_info_dict.items():
                org_id_to_org_member_info[org_id] = OrgMemberInfo(
                    org_id=org_data.get("org_id"),
                    org_name=org_data.get("org_name"),
                    url_safe_org_name=org_data.get("url_safe_org_name"),
                    org_metadata=org_data.get("org_metadata", {}),
                    user_assigned_role=org_data.get("user_role"),  # Note: key is 'user_role' in JWT
                    user_inherited_roles_plus_current_role=org_data.get(
                        "inherited_user_roles_plus_current_role", []
                    ),
                    org_role_structure=org_data.get("org_role_structure"),
                    assigned_additional_roles=org_data.get(
                        "additional_roles", []
                    ),  # Note: key is 'additional_roles' in JWT
                    user_permissions=org_data.get("user_permissions", []),
                )

            return User(
                user_id=user_id,
                email=email,
                org_id_to_org_member_info=org_id_to_org_member_info,
                login_method=login_method,
            )
        except UnauthorizedException as e:
            if self.debug_mode:
                raise HTTPException(status_code=401, detail=e.message)
            else:
                raise HTTPException(status_code=401)

    def optional_user(self, credentials: HTTPAuthorizationCredentials = Depends(_security)):
        if credentials is None:
            return None

        try:
            authorization_header = credentials.scheme + " " + credentials.credentials
            user = self.auth.validate_access_token_and_get_user(authorization_header)
            return user
        except UnauthorizedException:
            return None

    def require_org_member(self, user: User, required_org_id: str):
        try:
            return self.auth.validate_org_access_and_get_org(user, required_org_id)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, self.debug_mode)

    def require_org_member_with_minimum_role(
        self, user: User, required_org_id: str, minimum_required_role: str
    ):
        try:
            return self.auth.validate_minimum_org_role_and_get_org(
                user, required_org_id, minimum_required_role
            )
        except ForbiddenException as e:
            _handle_forbidden_exception(e, self.debug_mode)

    def require_org_member_with_exact_role(self, user: User, required_org_id: str, role: str):
        try:
            return self.auth.validate_exact_org_role_and_get_org(user, required_org_id, role)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, self.debug_mode)

    def require_org_member_with_permission(self, user: User, required_org_id: str, permission: str):
        try:
            return self.auth.validate_permission_and_get_org(user, required_org_id, permission)
        except ForbiddenException as e:
            _handle_forbidden_exception(e, self.debug_mode)

    def require_org_member_with_all_permissions(
        self, user: User, required_org_id: str, permissions: list[str]
    ):
        try:
            return self.auth.validate_all_permissions_and_get_org(
                user, required_org_id, permissions
            )
        except ForbiddenException as e:
            _handle_forbidden_exception(e, self.debug_mode)

    def validate_access_token_and_get_user(self, authorization_header: str) -> User:
        return self.auth.validate_access_token_and_get_user(
            authorization_header=authorization_header
        )

    def fetch_user_metadata_by_user_id(self, user_id: str, include_orgs: bool = False):
        return self.auth.fetch_user_metadata_by_user_id(user_id, include_orgs)

    def fetch_user_metadata_by_email(self, email: str, include_orgs: bool = False):
        return self.auth.fetch_user_metadata_by_email(email, include_orgs)

    def fetch_user_metadata_by_username(self, username: str, include_orgs: bool = False):
        return self.auth.fetch_user_metadata_by_username(username, include_orgs)

    def fetch_user_signup_query_params_by_user_id(self, user_id: str):
        return self.auth.fetch_user_signup_query_params_by_user_id(user_id)

    def fetch_batch_user_metadata_by_user_ids(
        self, user_ids: list[str], include_orgs: bool = False
    ):
        return self.auth.fetch_batch_user_metadata_by_user_ids(user_ids, include_orgs)

    def fetch_batch_user_metadata_by_emails(self, emails: list[str], include_orgs: bool = False):
        return self.auth.fetch_batch_user_metadata_by_emails(emails, include_orgs)

    def fetch_batch_user_metadata_by_usernames(
        self, usernames: list[str], include_orgs: bool = False
    ):
        return self.auth.fetch_batch_user_metadata_by_usernames(usernames, include_orgs)

    def fetch_org(self, org_id: str):
        return self.auth.fetch_org(org_id)

    def fetch_org_by_query(
        self,
        page_size: int = 10,
        page_number: int = 0,
        order_by: OrgQueryOrderBy = OrgQueryOrderBy.CREATED_AT_ASC,
        name: str | None = None,
        legacy_org_id: str | None = None,
        domain: str | None = None,
    ):
        return self.auth.fetch_org_by_query(
            page_size, page_number, order_by, name, legacy_org_id, domain
        )

    def fetch_custom_role_mappings(self):
        return self.auth.fetch_custom_role_mappings()

    def fetch_pending_invites(
        self, page_number: int = 0, page_size: int = 10, org_id: str | None = None
    ):
        return self.auth.fetch_pending_invites(page_number, page_size, org_id)

    def fetch_users_by_query(
        self,
        page_size: int = 10,
        page_number: int = 0,
        order_by: UserQueryOrderBy = UserQueryOrderBy.CREATED_AT_ASC,
        email_or_username: str | None = None,
        include_orgs: bool = False,
        legacy_user_id: str | None = None,
    ):
        return self.auth.fetch_users_by_query(
            page_size, page_number, order_by, email_or_username, include_orgs, legacy_user_id
        )

    def fetch_users_in_org(
        self,
        org_id: str,
        page_size: int = 10,
        page_number: int = 0,
        include_orgs: bool = False,
        role: str | None = None,
    ):
        return self.auth.fetch_users_in_org(org_id, page_size, page_number, include_orgs, role)

    def create_user(
        self,
        email: str,
        email_confirmed: bool = False,
        send_email_to_confirm_email_address: bool = True,
        ask_user_to_update_password_on_login: bool = False,
        password: str | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        properties: dict[str, Any] | None = None,
        ignore_domain_restrictions: bool = False,
    ):
        return self.auth.create_user(
            email,
            email_confirmed,
            send_email_to_confirm_email_address,
            ask_user_to_update_password_on_login,
            password,
            username,
            first_name,
            last_name,
            properties,
            ignore_domain_restrictions,
        )

    def invite_user_to_org(
        self, email: str, org_id: str, role: str, additional_roles: list[str] = []
    ):
        return self.auth.invite_user_to_org(email, org_id, role, additional_roles)

    def resend_email_confirmation(self, user_id: str):
        return self.auth.resend_email_confirmation(user_id)

    def logout_all_user_sessions(self, user_id: str):
        return self.auth.logout_all_user_sessions(user_id)

    def update_user_email(self, user_id: str, new_email: str, require_email_confirmation: bool):
        return self.auth.update_user_email(user_id, new_email, require_email_confirmation)

    def update_user_metadata(
        self,
        user_id: str,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        properties: dict[str, Any] | None = None,
        picture_url: str | None = None,
        update_password_required: bool | None = None,
        legacy_user_id: str | None = None,
    ):
        return self.auth.update_user_metadata(
            user_id,
            username,
            first_name,
            last_name,
            metadata,
            properties,
            picture_url,
            update_password_required,
            legacy_user_id,
        )

    def clear_user_password(self, user_id: str):
        return self.auth.clear_user_password(user_id)

    def update_user_password(
        self, user_id: str, password: str, ask_user_to_update_password_on_login: bool = False
    ):
        return self.auth.update_user_password(
            user_id, password, ask_user_to_update_password_on_login
        )

    def create_magic_link(
        self,
        email: str,
        redirect_to_url: str | None = None,
        expires_in_hours: str | None = None,
        create_new_user_if_one_doesnt_exist: bool | None = None,
        user_signup_query_parameters: dict[str, Any] | None = None,
    ):
        return self.auth.create_magic_link(
            email,
            redirect_to_url,
            expires_in_hours,
            create_new_user_if_one_doesnt_exist,
            user_signup_query_parameters,
        )

    def create_access_token(
        self, user_id: str, duration_in_minutes: int, active_org_id: str | None = None
    ):
        return self.auth.create_access_token(user_id, duration_in_minutes, active_org_id)

    def migrate_user_from_external_source(
        self,
        email: str,
        email_confirmed: bool,
        existing_user_id: str | None = None,
        existing_password_hash: str | None = None,
        existing_mfa_base32_encoded_secret: str | None = None,
        ask_user_to_update_password_on_login: bool = False,
        enabled: bool | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
        picture_url: str | None = None,
        properties: dict[str, Any] | None = None,
    ):
        return self.auth.migrate_user_from_external_source(
            email,
            email_confirmed,
            existing_user_id,
            existing_password_hash,
            existing_mfa_base32_encoded_secret,
            ask_user_to_update_password_on_login,
            enabled,
            first_name,
            last_name,
            username,
            picture_url,
            properties,
        )

    def migrate_user_password(
        self,
        user_id: str,
        password_hash: str,
    ):
        return self.auth.migrate_user_password(user_id, password_hash)

    def create_org(
        self,
        name: str,
        enable_auto_joining_by_domain: bool = False,
        members_must_have_matching_domain: bool = False,
        domain: str | None = None,
        max_users: str | None = None,
        custom_role_mapping_name: str | None = None,
        legacy_org_id: str | None = None,
    ):
        return self.auth.create_org(
            name,
            enable_auto_joining_by_domain,
            members_must_have_matching_domain,
            domain,
            max_users,
            custom_role_mapping_name,
            legacy_org_id,
        )

    def update_org_metadata(
        self,
        org_id: str,
        name: str | None = None,
        can_setup_saml: bool | None = None,
        metadata: dict[str, Any] | None = None,
        max_users: str | None = None,
        can_join_on_email_domain_match: bool | None = None,
        members_must_have_email_domain_match: bool | None = None,
        domain: str | None = None,
        require_2fa_by: str | None = None,
        extra_domains: list[str] | None = None,
    ):
        return self.auth.update_org_metadata(
            org_id,
            name,
            can_setup_saml,
            metadata,
            max_users,
            can_join_on_email_domain_match,
            members_must_have_email_domain_match,
            domain,
            require_2fa_by,
            extra_domains,
        )

    def subscribe_org_to_role_mapping(self, org_id: str, custom_role_mapping_name: str):
        return self.auth.subscribe_org_to_role_mapping(org_id, custom_role_mapping_name)

    def delete_org(self, org_id: str):
        return self.auth.delete_org(org_id)

    def revoke_pending_org_invite(self, org_id: str, invitee_email: str):
        return self.auth.revoke_pending_org_invite(org_id, invitee_email)

    def add_user_to_org(
        self, user_id: str, org_id: str, role: str, additional_roles: list[str] = []
    ):
        return self.auth.add_user_to_org(user_id, org_id, role, additional_roles)

    def remove_user_from_org(self, user_id: str, org_id: str):
        return self.auth.remove_user_from_org(user_id, org_id)

    def change_user_role_in_org(
        self, user_id: str, org_id: str, role: str, additional_roles: list[str] = []
    ):
        return self.auth.change_user_role_in_org(user_id, org_id, role, additional_roles)

    def delete_user(self, user_id: str):
        return self.auth.delete_user(user_id)

    def disable_user(self, user_id: str):
        return self.auth.disable_user(user_id)

    def enable_user(self, user_id: str):
        return self.auth.enable_user(user_id)

    def disable_user_2fa(self, user_id: str):
        return self.auth.disable_user_2fa(user_id)

    def enable_user_can_create_orgs(self, user_id: str):
        return self.auth.enable_user_can_create_orgs(user_id)

    def disable_user_can_create_orgs(self, user_id: str):
        return self.auth.disable_user_can_create_orgs(user_id)

    def allow_org_to_setup_saml_connection(self, org_id: str):
        return self.auth.allow_org_to_setup_saml_connection(org_id)

    def disallow_org_to_setup_saml_connection(self, org_id: str):
        return self.auth.disallow_org_to_setup_saml_connection(org_id)

    def fetch_api_key(self, api_key_id: str):
        return self.auth.fetch_api_key(api_key_id)

    def fetch_current_api_keys(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        user_email: str | None = None,
        page_size: int | None = None,
        page_number: int | None = None,
        api_key_type: str | None = None,
    ):
        return self.auth.fetch_current_api_keys(
            org_id, user_id, user_email, page_size, page_number, api_key_type
        )

    def fetch_archived_api_keys(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        user_email: str | None = None,
        page_size: int | None = None,
        page_number: int | None = None,
        api_key_type: str | None = None,
    ):
        return self.auth.fetch_archived_api_keys(
            org_id, user_id, user_email, page_size, page_number, api_key_type
        )

    def create_api_key(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        expires_at_seconds: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        return self.auth.create_api_key(org_id, user_id, expires_at_seconds, metadata)

    def update_api_key(
        self,
        api_key_id: str,
        expires_at_seconds: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        return self.auth.update_api_key(api_key_id, expires_at_seconds, metadata)

    def delete_api_key(self, api_key_id: str):
        return self.auth.delete_api_key(api_key_id)

    def validate_personal_api_key(self, api_key_token: str):
        return self.auth.validate_personal_api_key(api_key_token)

    def validate_org_api_key(self, api_key_token: str):
        return self.auth.validate_org_api_key(api_key_token)

    def validate_api_key(self, api_key_token: str):
        return self.auth.validate_api_key(api_key_token)

    def fetch_saml_sp_metadata(self, org_id: str):
        return self.auth.fetch_saml_sp_metadata(org_id)

    def set_saml_idp_metadata(self, org_id: str, saml_idp_metadata: SamlIdpMetadata):
        return self.auth.set_saml_idp_metadata(org_id=org_id, saml_idp_metadata=saml_idp_metadata)

    def saml_go_live(self, org_id: str):
        return self.auth.saml_go_live(org_id)

    def delete_saml_connection(self, org_id: str):
        return self.auth.delete_saml_connection(org_id)

    def verify_step_up_totp_challenge(
        self,
        action_type: str,
        user_id: str,
        code: str,
        grant_type: StepUpMfaGrantType,
        valid_for_seconds: int,
    ) -> StepUpMfaVerifyTotpResponse:
        return self.auth.verify_step_up_totp_challenge(
            action_type, user_id, code, grant_type, valid_for_seconds
        )

    def verify_step_up_grant(self, action_type: str, user_id: str, grant: str) -> bool:
        return self.auth.verify_step_up_grant(action_type, user_id, grant)


def init_auth(
    auth_url: str,
    api_key: str,
    token_verification_metadata: TokenVerificationMetadata | None = None,
    debug_mode=False,
) -> FastAPIAuth:
    """Fetches metadata required to validate access tokens and returns auth decorators and utilities"""
    return FastAPIAuth(
        auth_url=auth_url,
        integration_api_key=api_key,
        token_verification_metadata=token_verification_metadata,
        debug_mode=debug_mode,
    )
