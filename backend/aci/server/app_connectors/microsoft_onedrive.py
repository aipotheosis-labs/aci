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

    def upload_text_file(
        self, file_path: str, content: str, conflict_behavior: str = "replace"
    ) -> dict[str, str]:
        """
        Upload or create a text file to OneDrive.

        Args:
            file_path: The path where the file should be created, relative to root
            content: The text content to write to the file
            conflict_behavior: How to handle conflicts ("rename", "replace", "fail")

        Returns:
            dict: Response containing file metadata including id, name, and path
        """
        logger.info(f"Uploading text file to OneDrive: {file_path}")

        # Construct the API endpoint
        url = f"{self.base_url}/me/drive/root:/{file_path}:/content"

        # Set up headers
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "text/plain"}

        # Add conflict behavior as query parameter if specified
        params = {}
        if conflict_behavior and conflict_behavior != "replace":
            params["@microsoft.graph.conflictBehavior"] = conflict_behavior

        try:
            # Upload the file content
            response = requests.put(
                url, data=content.encode("utf-8"), headers=headers, params=params, timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully uploaded file: {file_path}, id: {result.get('id')}")

            return {
                "id": result.get("id", ""),
                "name": result.get("name", ""),
                "path": result.get("parentReference", {}).get("path", "")
                + "/"
                + result.get("name", ""),
                "size": result.get("size", 0),
                "created_datetime": result.get("createdDateTime", ""),
                "modified_datetime": result.get("lastModifiedDateTime", ""),
            }

        except Exception as e:
            logger.error(f"Failed to upload file to OneDrive: {file_path}, error: {e}")
            raise Exception(f"Failed to upload file: {e}") from e

    def read_text_file(self, file_path: str) -> dict[str, str]:
        """
        Read the content of a text file from OneDrive.

        Args:
            file_path: The path of the file to read, relative to root

        Returns:
            dict: Response containing file content and metadata
        """
        logger.info(f"Reading text file from OneDrive: {file_path}")

        # First get file metadata
        metadata_url = f"{self.base_url}/me/drive/root:/{file_path}"
        content_url = f"{self.base_url}/me/drive/root:/{file_path}:/content"

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
                raise Exception(f"'{file_path}' is not a file or does not exist")

            # Get file content
            content_response = requests.get(content_url, headers=headers, timeout=30)
            content_response.raise_for_status()

            # Decode content as text
            try:
                content = content_response.text
            except UnicodeDecodeError:
                logger.warning(
                    f"File {file_path} contains non-text content, attempting UTF-8 decode"
                )
                content = content_response.content.decode("utf-8", errors="replace")

            logger.info(f"Successfully read file: {file_path}, size: {len(content)} characters")

            return {
                "content": content,
                "id": metadata.get("id", ""),
                "name": metadata.get("name", ""),
                "path": metadata.get("parentReference", {}).get("path", "")
                + "/"
                + metadata.get("name", ""),
                "size": metadata.get("size", 0),
                "created_datetime": metadata.get("createdDateTime", ""),
                "modified_datetime": metadata.get("lastModifiedDateTime", ""),
            }

        except Exception as e:
            logger.error(f"Failed to read file from OneDrive: {file_path}, error: {e}")
            raise Exception(f"Failed to read file: {e}") from e
