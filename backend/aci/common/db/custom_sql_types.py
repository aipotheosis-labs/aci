import base64
import copy
import json

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.types import LargeBinary, TypeDecorator

from aci.common import encryption
from aci.common.enums import SecurityScheme


def _encrypt_value(value: str) -> str:
    """Encrypt a string value and return base64-encoded result."""
    encrypted_bytes = encryption.encrypt(value.encode("utf-8"))
    # The bytes returned by the encryption.encrypt method can be any bytes,
    # which is not always valid for utf-8 decoding, so we need to encode it
    # using base64 first to ensure it's a valid bytes for utf-8. Then, we
    # decode it back to a string using utf-8.
    return base64.b64encode(encrypted_bytes).decode("utf-8")


def _decrypt_value(value: str) -> str:
    """Decrypt a base64-encoded encrypted string."""
    encrypted_bytes = base64.b64decode(value)
    return encryption.decrypt(encrypted_bytes).decode("utf-8")


class Key(TypeDecorator[str]):
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: Dialect) -> bytes | None:
        if value is not None:
            if not isinstance(value, str):
                raise TypeError("Key type expects a string value")
            plain_bytes = value.encode("utf-8")
            encrypted_bytes = encryption.encrypt(plain_bytes)
            return encrypted_bytes
        return None

    def process_result_value(self, value: bytes | None, dialect: Dialect) -> str | None:
        if value is not None:
            if not isinstance(value, bytes):
                raise TypeError("Key type expects a bytes value")
            decrypted_bytes = encryption.decrypt(value)
            return decrypted_bytes.decode("utf-8")
        return None


class EncryptedSecurityScheme(TypeDecorator[dict]):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: dict | None, dialect: Dialect) -> dict | None:
        if value is not None:
            encrypted_value = copy.deepcopy(value)  # Use deepcopy to handle nested structures

            for scheme_type, scheme_data in encrypted_value.items():
                # We only need to encrypt the client_secret in OAuth2Scheme
                if scheme_type == SecurityScheme.OAUTH2 and "client_secret" in scheme_data:
                    client_secret = scheme_data["client_secret"]
                    if isinstance(client_secret, str):
                        scheme_data["client_secret"] = _encrypt_value(client_secret)

            return encrypted_value
        return None

    def process_result_value(self, value: dict | None, dialect: Dialect) -> dict | None:
        if value is not None:
            decrypted_value = copy.deepcopy(value)  # Use deepcopy to handle nested structures

            for scheme_type, scheme_data in decrypted_value.items():
                # We only need to decrypt the client_secret in OAuth2Scheme
                if scheme_type == SecurityScheme.OAUTH2 and "client_secret" in scheme_data:
                    client_secret_b64 = scheme_data["client_secret"]
                    if isinstance(client_secret_b64, str):
                        scheme_data["client_secret"] = _decrypt_value(client_secret_b64)

            return decrypted_value
        return None


class EncryptedSecurityCredentials(TypeDecorator[dict]):
    impl = JSONB
    cache_ok = True

    def process_bind_param(self, value: dict | None, dialect: Dialect) -> dict | None:
        if value is not None:
            encrypted_value = copy.deepcopy(value)  # Avoid modifying the original dict

            # TODO: if we add a new field or rename a field in the future,
            # we need to update the process_result_value method to handle the new field

            # APIKeySchemeCredentials
            if "secret_key" in encrypted_value:
                secret_key = encrypted_value["secret_key"]
                if isinstance(secret_key, str):
                    encrypted_value["secret_key"] = _encrypt_value(secret_key)

            # OAuth2SchemeCredentials
            elif "access_token" in encrypted_value:
                client_secret = encrypted_value.get("client_secret")
                if isinstance(client_secret, str):
                    encrypted_value["client_secret"] = _encrypt_value(client_secret)

                access_token = encrypted_value.get("access_token")
                if isinstance(access_token, str):
                    encrypted_value["access_token"] = _encrypt_value(access_token)

                refresh_token = encrypted_value.get("refresh_token")
                if isinstance(refresh_token, str):
                    encrypted_value["refresh_token"] = _encrypt_value(refresh_token)

                raw_token_response = encrypted_value.get("raw_token_response")
                if isinstance(raw_token_response, dict):
                    raw_token_response_str = json.dumps(raw_token_response)
                    encrypted_value["raw_token_response"] = _encrypt_value(raw_token_response_str)

            # NoAuthSchemeCredentials (empty dict) - do nothing

            return encrypted_value
        return None

    def process_result_value(self, value: dict | None, dialect: Dialect) -> dict | None:
        if value is not None:
            decrypted_value = copy.deepcopy(value)  # Avoid modifying the original dict

            # APIKeySchemeCredentials
            if "secret_key" in decrypted_value:
                secret_key_b64 = decrypted_value["secret_key"]
                if isinstance(secret_key_b64, str):
                    decrypted_value["secret_key"] = _decrypt_value(secret_key_b64)

            # OAuth2SchemeCredentials
            elif "access_token" in decrypted_value:
                client_secret_b64 = decrypted_value.get("client_secret")
                if isinstance(client_secret_b64, str):
                    decrypted_value["client_secret"] = _decrypt_value(client_secret_b64)

                access_token_b64 = decrypted_value.get("access_token")
                if isinstance(access_token_b64, str):
                    decrypted_value["access_token"] = _decrypt_value(access_token_b64)

                refresh_token_b64 = decrypted_value.get("refresh_token")
                if isinstance(refresh_token_b64, str):
                    decrypted_value["refresh_token"] = _decrypt_value(refresh_token_b64)

                raw_token_response_b64 = decrypted_value.get("raw_token_response")
                if isinstance(raw_token_response_b64, str):
                    decrypted_str = _decrypt_value(raw_token_response_b64)
                    decrypted_value["raw_token_response"] = json.loads(decrypted_str)

            # NoAuthSchemeCredentials (empty dict) - do nothing

            return decrypted_value
        return None
