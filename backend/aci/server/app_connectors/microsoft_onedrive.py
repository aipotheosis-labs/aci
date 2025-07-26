import csv
import io
import tempfile
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

    def create_docx_from_markdown(
        self, markdown_data: str, parent_folder_id: str, filename: str | None = None
    ) -> dict[str, str | int]:
        """
        Convert Markdown text to a formatted DOCX document and save it to OneDrive.
        Uses the md2docx-python library for robust conversion.

        Args:
            markdown_data: The Markdown text as a string to convert
            parent_folder_id: The identifier of the parent folder where the DOCX file will be created
            filename: Optional custom name for the DOCX file (without .docx extension)

        Returns:
            dict: Response containing the created DOCX file metadata
        """
        logger.info(f"Creating DOCX file from Markdown on OneDrive, folder: {parent_folder_id}")

        try:
            from md2docx_python.src.md2docx_python import markdown_to_word

            # Determine filename
            if not filename:
                filename = "converted_document"

            # Ensure .docx extension
            if not filename.endswith(".docx"):
                filename += ".docx"

            # Create temporary files for conversion
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as md_file:
                md_file.write(markdown_data)
                md_file_path = md_file.name

            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as docx_file:
                docx_file_path = docx_file.name

            try:
                # Convert markdown to DOCX using the well-maintained library
                markdown_to_word(md_file_path, docx_file_path)

                # Read the generated DOCX file
                with open(docx_file_path, "rb") as docx_file:
                    docx_bytes = docx_file.read()

                # Upload DOCX file to OneDrive
                upload_url = (
                    f"{self.base_url}/me/drive/items/{parent_folder_id}:/{filename}:/content"
                )

                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                }

                upload_response = requests.put(
                    upload_url, headers=headers, data=docx_bytes, timeout=60
                )
                upload_response.raise_for_status()

                result = upload_response.json()

                # Count some basic stats for the response
                lines = markdown_data.split("\n")
                word_count = len(markdown_data.split())

                logger.info(
                    f"Successfully created DOCX file: {filename}, ID: {result.get('id', '')}"
                )

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
                    "lines_converted": len(lines),
                    "word_count": word_count,
                    "note": "DOCX file created successfully from Markdown using md2docx-python library.",
                }

            finally:
                # Clean up temporary files
                import os

                try:
                    os.unlink(md_file_path)
                    os.unlink(docx_file_path)
                except OSError:
                    pass  # Files already cleaned up

        except Exception as e:
            logger.error(f"Failed to create DOCX file from Markdown data: {e}")
            raise Exception(f"Failed to create DOCX file: {e}") from e

    def read_markdown_from_docx(self, item_id: str) -> dict[str, str | int]:
        """
        Convert a DOCX file from OneDrive to Markdown text.
        Uses the md2docx-python library for robust conversion.

        Args:
            item_id: The identifier of the DOCX file in OneDrive to convert

        Returns:
            dict: Response containing the markdown content and metadata
        """
        logger.info(f"Converting DOCX file to Markdown from OneDrive: {item_id}")

        try:
            from md2docx_python.src.docx2md_python import word_to_markdown

            # Download the DOCX file from OneDrive
            download_url = f"{self.base_url}/me/drive/items/{item_id}/content"
            headers = {"Authorization": f"Bearer {self.access_token}"}

            download_response = requests.get(download_url, headers=headers, timeout=30)
            download_response.raise_for_status()

            # Get file metadata for response details
            metadata_url = f"{self.base_url}/me/drive/items/{item_id}"
            metadata_response = requests.get(metadata_url, headers=headers, timeout=30)
            metadata_response.raise_for_status()
            metadata = metadata_response.json()

            # Verify it's a DOCX file
            if not metadata.get("name", "").lower().endswith((".docx", ".doc")):
                raise Exception(f"File '{metadata.get('name', '')}' is not a Word document")

            # Create temporary files for conversion
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as docx_file:
                docx_file.write(download_response.content)
                docx_file_path = docx_file.name

            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as md_file:
                md_file_path = md_file.name

            try:
                # Convert DOCX to Markdown using the well-maintained library
                word_to_markdown(docx_file_path, md_file_path)

                # Read the generated Markdown file
                with open(md_file_path, encoding="utf-8") as md_file:
                    markdown_content = md_file.read()

                # Count some basic stats for the response
                lines = markdown_content.split("\n")
                word_count = len(markdown_content.split())

                logger.info(
                    f"Successfully converted DOCX to Markdown: {item_id}, {len(markdown_content)} characters"
                )

                return {
                    "content": markdown_content,
                    "id": metadata.get("id", ""),
                    "name": metadata.get("name", ""),
                    "path": metadata.get("parentReference", {}).get("path", "")
                    + "/"
                    + metadata.get("name", ""),
                    "size": metadata.get("size", 0),
                    "mime_type": metadata.get("file", {}).get("mimeType", ""),
                    "created_datetime": metadata.get("createdDateTime", ""),
                    "modified_datetime": metadata.get("lastModifiedDateTime", ""),
                    "lines_extracted": len(lines),
                    "word_count": word_count,
                    "note": "DOCX file successfully converted to Markdown using md2docx-python library.",
                }

            finally:
                # Clean up temporary files
                import os

                try:
                    os.unlink(docx_file_path)
                    os.unlink(md_file_path)
                except OSError:
                    pass  # Files already cleaned up

        except Exception as e:
            logger.error(f"Failed to convert DOCX file to Markdown: {item_id}, error: {e}")
            raise Exception(f"Failed to convert DOCX file: {e}") from e
