import csv
import io
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

    def read_text_file_content(self, item_id: str) -> dict[str, str | int]:
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

    def create_excel_from_csv(
        self, csv_data: str, parent_folder_id: str, filename: str | None = None
    ) -> dict[str, str | int]:
        """
        Convert CSV data to a properly formatted CSV file and save it to OneDrive.
        This creates a CSV file that can be opened in Excel.

        Args:
            csv_data: The CSV data as a string to save
            parent_folder_id: The identifier of the parent folder where the CSV file will be created
            filename: Optional custom name for the CSV file (without .csv extension)

        Returns:
            dict: Response containing the created CSV file metadata
        """
        logger.info(f"Creating CSV file on OneDrive, folder: {parent_folder_id}")

        try:
            # Parse and validate CSV data using built-in csv module
            csv_reader = csv.reader(io.StringIO(csv_data))
            rows = list(csv_reader)

            if not rows:
                raise Exception("CSV data is empty")

            # Determine filename
            if not filename:
                filename = "converted_data"

            # Ensure .csv extension
            if not filename.endswith(".csv"):
                filename += ".csv"

            # Upload CSV file to OneDrive using the existing text file creation method
            upload_url = f"{self.base_url}/me/drive/items/{parent_folder_id}:/{filename}:/content"

            headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "text/csv"}

            upload_response = requests.put(
                upload_url, headers=headers, data=csv_data.encode("utf-8"), timeout=60
            )
            upload_response.raise_for_status()

            result = upload_response.json()

            logger.info(f"Successfully created CSV file: {filename}, ID: {result.get('id', '')}")

            return {
                "id": result.get("id", ""),
                "name": result.get("name", ""),
                "path": result.get("parentReference", {}).get("path", "")
                + "/"
                + result.get("name", ""),
                "size": result.get("size", 0),
                "mime_type": result.get("file", {}).get("mimeType", ""),
                "created_datetime": result.get("createdDateTime", ""),
                "modified_datetime": result.get("lastModifiedDateTime", ""),
                "download_url": result.get("@microsoft.graph.downloadUrl", ""),
                "rows_converted": len(rows),
                "columns_converted": len(rows[0]) if rows else 0,
                "note": "CSV file created successfully. This file can be opened in Excel.",
            }

        except Exception as e:
            logger.error(f"Failed to create CSV file from CSV data: {e}")
            raise Exception(f"Failed to create CSV file: {e}") from e
