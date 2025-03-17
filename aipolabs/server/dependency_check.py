from aipolabs.common.encryption import decrypt, encrypt
from aipolabs.common.exceptions import DependencyCheckError


def check_aws_kms_dependency() -> None:
    check_data = b"start up dependency check"

    encrypted_data = encrypt(check_data)
    decrypted_data = decrypt(encrypted_data)

    if check_data != decrypted_data:
        raise DependencyCheckError("Encryption/decryption using AWS KMS failed")


def check_dependencies() -> None:
    check_aws_kms_dependency()
