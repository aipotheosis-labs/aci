from typing import cast

import aws_encryption_sdk  # type: ignore
import boto3  # type: ignore
from aws_cryptographic_material_providers.mpl import (  # type: ignore
    AwsCryptographicMaterialProviders,
)
from aws_cryptographic_material_providers.mpl.config import MaterialProvidersConfig  # type: ignore
from aws_cryptographic_material_providers.mpl.models import CreateAwsKmsKeyringInput  # type: ignore
from aws_cryptographic_material_providers.mpl.references import IKeyring  # type: ignore
from aws_encryption_sdk import CommitmentPolicy

from aipolabs.server import config

client = aws_encryption_sdk.EncryptionSDKClient(
    commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_REQUIRE_DECRYPT
)

kms_client = boto3.client(
    "kms",
    region_name=config.AWS_REGION,
    endpoint_url=config.AWS_ENDPOINT_URL,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
)


mat_prov: AwsCryptographicMaterialProviders = AwsCryptographicMaterialProviders(
    config=MaterialProvidersConfig()
)

keyring_input: CreateAwsKmsKeyringInput = CreateAwsKmsKeyringInput(
    kms_key_id=config.SECRETS_MANAGER_KEK_ARN,
    kms_client=kms_client,
)


def encrypt(plain_data: bytes) -> bytes:
    kms_keyring: IKeyring = mat_prov.create_aws_kms_keyring(input=keyring_input)
    # TODO: ignore encryptor_header for now
    my_ciphertext, _ = client.encrypt(source=plain_data, keyring=kms_keyring)
    return cast(bytes, my_ciphertext)


def decrypt(cipher_data: bytes) -> bytes:
    kms_keyring: IKeyring = mat_prov.create_aws_kms_keyring(input=keyring_input)
    # TODO: ignore decryptor_header for now
    my_plaintext, _ = client.decrypt(source=cipher_data, keyring=kms_keyring)
    return cast(bytes, my_plaintext)
