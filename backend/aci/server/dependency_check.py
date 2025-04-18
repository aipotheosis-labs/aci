from aci.common.encryption import decrypt, encrypt
from aci.common.exceptions import DependencyCheckError


def check_aws_kms_dependency() -> None:
    check_data = b"start up dependency check"

    encrypted_data = encrypt(check_data)
    decrypted_data = decrypt(encrypted_data)

    if check_data != decrypted_data:
        raise DependencyCheckError(
            f"Encryption/decryption using AWS KMS failed: original data '{check_data!r}'"
            f"does not match decrypted result '{decrypted_data!r}'"
        )


def check_dependencies() -> None:
    check_aws_kms_dependency()
