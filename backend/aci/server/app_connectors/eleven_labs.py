import base64
from typing import Any, override

from elevenlabs import ElevenLabs as ElevenLabsClient
from elevenlabs import VoiceSettings

from aci.common.db.sql_models import LinkedAccount
from aci.common.logging_setup import get_logger
from aci.common.schemas.security_scheme import (
    APIKeyScheme,
    APIKeySchemeCredentials,
)
from aci.server.app_connectors.base import AppConnectorBase

logger = get_logger(__name__)


class ElevenLabs(AppConnectorBase):
    """Connector for ElevenLabs text-to-speech API."""

    def __init__(
        self,
        linked_account: LinkedAccount,
        security_scheme: APIKeyScheme,
        security_credentials: APIKeySchemeCredentials,
    ):
        super().__init__(linked_account, security_scheme, security_credentials)
        self.client = ElevenLabsClient(api_key=security_credentials.secret_key)

    @override
    def _before_execute(self) -> None:
        pass

    def create_speech(
        self,
        voice_id: str,
        text: str,
        model_id: str | None = "eleven_multilingual_v2",
        voice_settings: VoiceSettings | None = None,
    ) -> dict[str, Any]:
        """
        Converts text into speech using ElevenLabs API and returns base64-encoded MP3 audio.

        Args:
            voice_id: ID of the voice to be used
            text: The text that will be converted into speech
            model_id: Identifier of the model to use (defaults to eleven_multilingual_v2)
            voice_settings: Voice settings overriding stored settings for the given voice

        Returns:
            Dictionary containing the base64-encoded MP3 audio and metadata
        """
        try:
            # Use the ElevenLabs SDK to convert text to speech
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=model_id,
                voice_settings=voice_settings,
                output_format="mp3_44100_128",  # Request MP3 format with 44.1kHz and 128kbps
            )

            # Convert the generator to bytes
            audio_bytes = b"".join(audio_generator)

            # Convert audio bytes to base64
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

            return {
                "success": True,
                "audio_base64": audio_base64,
                "format": "mp3",
                "voice_id": voice_id,
                "text_length": len(text),
                "model_id": model_id,
                "sample_rate": "44100",
                "bitrate": "128",
            }

        except Exception as e:
            logger.error(f"ElevenLabs SDK error: {e}")
            return {
                "success": False,
                "error": f"ElevenLabs SDK error: {e}",
                "voice_id": voice_id,
            }
