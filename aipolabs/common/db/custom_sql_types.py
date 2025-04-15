from sqlalchemy.engine import Dialect
from sqlalchemy.types import LargeBinary, TypeDecorator

from aipolabs.common import encryption


class Key(TypeDecorator[str]):
    """
    Stores a string key as UTF-8 encoded bytes in the database.
    This is useful for primary keys or indexed columns where direct string comparison
    might be inefficient depending on the database collation.
    """

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
