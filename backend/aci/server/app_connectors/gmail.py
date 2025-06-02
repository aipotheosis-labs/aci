import base64
from email.mime.text import MIMEText
from typing import override

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from aci.common.db.sql_models import LinkedAccount
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    OAuth2Scheme,
    OAuth2SchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


# TODO: how should we handle args are passed as flattened? separated by double underscore?
# e.g. person__name, person__title. maybe need to preprocess the args before passing to the method?
class Gmail(AppConnectorBase):
    """
    Gmail Connector.
    """

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: OAuth2Scheme,
        security_credentials: OAuth2SchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        self.credentials = Credentials(  # type: ignore
            token=security_credentials.access_token,
            refresh_token=security_credentials.refresh_token,
        )

    @override
    def _before_execute(self) -> None:
        # TODO: technicall you can check credential validity here and optionally refresh the token
        # e.g., if creds.expired and creds.refresh_token:
        #     creds.refresh(Request())
        # but this doesn't sit well with our existing credential fetch and update mechanism
        # (which was built for generic oauth2/api_key REST APIs)
        pass

    # TODO: support HTML type for body
    def send_email(
        self,
        sender: str,
        recipient: str,
        body: str,
        subject: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Send an email using Gmail API.

        Args:
            sender: Sender email address
            recipient: Recipient email address(es), comma-separated for multiple recipients
            body: Email body content
            subject: Optional email subject
            cc: Optional list of carbon copy recipients
            bcc: Optional list of blind carbon copy recipients

        Returns:
            dict: Response from the Gmail API
        """
        logger.info("executing send_email")

        # Create and encode the email message
        message = MIMEText(body)
        message["to"] = recipient

        if subject:
            message["subject"] = subject
        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)

        # Create the final message body
        message_body = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

        service = build("gmail", "v1", credentials=self.credentials)

        sent_message = service.users().messages().send(userId=sender, body=message_body).execute()  # type: ignore

        logger.info(f"Email sent successfully. Message ID: {sent_message.get('id', 'unknown')}")

        # TODO: if later found necessary, return the whole message object instead of just the id
        return {"message_id": sent_message.get("id", "unknown")}

    # TODO: support HTML type for body
    def drafts_create(
        self,
        sender: str,
        recipient: str,
        body: str,
        subject: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Create a draft email using Gmail API.

        Args:
            sender: Sender email address
            recipient: Recipient email address(es), comma-separated for multiple recipients
            body: Email body content
            subject: Optional email subject
            cc: Optional list of carbon copy recipients
            bcc: Optional list of blind carbon copy recipients

        Returns:
            dict: Response from the Gmail API containing the draft ID
        """
        logger.info("executing drafts_create")

        # Create and encode the email message
        message = MIMEText(body)
        message["to"] = recipient

        if subject:
            message["subject"] = subject
        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)

        # Create the message body
        message_body = {"message": {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}}

        service = build("gmail", "v1", credentials=self.credentials)

        # Create the draft
        draft = service.users().drafts().create(userId=sender, body=message_body).execute()  # type: ignore

        logger.info(f"Draft created successfully. Draft ID: {draft.get('id', 'unknown')}")

        return {"draft_id": draft.get("id", "unknown")}

    # TODO: support HTML type for body
    def drafts_update(
        self,
        draft_id: str,
        sender: str,
        recipient: str,
        body: str,
        subject: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> dict[str, str]:
        """
        Update an existing draft email using Gmail API.

        Args:
            draft_id: ID of the draft to update
            sender: Sender email address
            recipient: Recipient email address(es), comma-separated for multiple recipients
            body: Email body content
            subject: Optional email subject
            cc: Optional list of carbon copy recipients
            bcc: Optional list of blind carbon copy recipients

        Returns:
            dict: Response from the Gmail API containing the updated draft ID
        """
        logger.info(f"executing drafts_update for draft ID: {draft_id}")

        # Create and encode the email message
        message = MIMEText(body)
        message["to"] = recipient

        if subject:
            message["subject"] = subject
        if cc:
            message["cc"] = ", ".join(cc)
        if bcc:
            message["bcc"] = ", ".join(bcc)

        # Create the message body
        message_body = {
            "id": draft_id,
            "message": {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()},
        }

        service = build("gmail", "v1", credentials=self.credentials)

        # Update the draft
        updated_draft = (
            service.users().drafts().update(userId=sender, id=draft_id, body=message_body).execute()  # type: ignore
        )

        logger.info(f"Draft updated successfully. Draft ID: {updated_draft.get('id', 'unknown')}")

        return {"draft_id": updated_draft.get("id", "unknown")}
