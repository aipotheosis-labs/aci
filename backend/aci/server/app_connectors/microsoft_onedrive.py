from typing import override

import requests

from aci.common.db.sql_models import LinkedAccount
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


class MicrosoftOnedrive(AppConnectorBase):
    """
    Microsoft OneDrive Connector for text file operations.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: OAuth2Scheme,
        security_credentials: OAuth2SchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        self.access_token = security_credentials.access_token
        self.base_url = "https://graph.microsoft.com/v1.0"

    @override
    def _before_execute(self) -> None:
        # TODO: Check token validity and refresh if needed
        pass

    def read_text_file(self, item_id: str) -> dict[str, str]:
        """
        Read the content of a text file from OneDrive by its item ID.

        Args:
            item_id: The identifier of the driveItem file to read

        Returns:
            dict: Response containing file content and metadata
        """
        logger.info(f"Reading text file from OneDrive: {item_id}")

        # Construct API URLs
        metadata_url = f"{self.base_url}/me/drive/items/{item_id}"
        content_url = f"{self.base_url}/me/drive/items/{item_id}/content"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
        }

        try:
            # Get file metadata first
            metadata_response = requests.get(metadata_url, headers=headers, timeout=30)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()

            # Check if it's a file (not a folder)
            if "file" not in metadata:
                raise Exception(f"Item '{item_id}' is not a file or does not exist")

            # Get file content - this will follow the 302 redirect automatically
            content_response = requests.get(content_url, headers=headers, timeout=30)
            content_response.raise_for_status()

            # Decode content as text
            try:
                content = content_response.text
            except UnicodeDecodeError:
                logger.warning(f"File {item_id} contains non-text content, attempting UTF-8 decode")
                content = content_response.content.decode("utf-8", errors="replace")

            logger.info(f"Successfully read file: {item_id}, size: {len(content)} characters")

            return {
                "content": content,
                "id": metadata.get("id", ""),
                "name": metadata.get("name", ""),
                "path": metadata.get("parentReference", {}).get("path", "")
                + "/"
                + metadata.get("name", ""),
                "size": metadata.get("size", 0),
                "mime_type": metadata.get("file", {}).get("mimeType", ""),
                "created_datetime": metadata.get("createdDateTime", ""),
                "modified_datetime": metadata.get("lastModifiedDateTime", ""),
            }

        except Exception as e:
            logger.error(f"Failed to read file from OneDrive: {item_id}, error: {e}")
            raise Exception(f"Failed to read file: {e}") from e
