#!/bin/bash
# This script is mounted into the localstack container to run during its container
# startup.
# This command creates a KMS key in the aws localstack container with an id of
# 00000000-0000-0000-0000-000000000001. This key is used as the key encryption
# key in local docker compose environment for the common/encryption.py module.
# Using fixed custom key material ensures the same key is generated each time

FIXED_KEY_MATERIAL="U2FsdGVkX1+K8yfnrMn+QRyh2nWPfI9wXA84BGm6YAA="
awslocal kms create-key --region us-east-2 --tags '[{"TagKey":"_custom_id_","TagValue":"00000000-0000-0000-0000-000000000001"},{"TagKey":"_custom_key_material_","TagValue":"'"$FIXED_KEY_MATERIAL"'"}]'
