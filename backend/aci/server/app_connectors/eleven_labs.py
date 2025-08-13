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
        output_format: str = "mp3_44100_128",
    ) -> dict[str, Any]:
        """
        Converts text into speech using ElevenLabs API and returns base64-encoded audio.

        Args:
            voice_id: ID of the voice to be used
            text: The text that will be converted into speech
            model_id: Identifier of the model to use (defaults to eleven_multilingual_v2)
            voice_settings: Voice settings overriding stored settings for the given voice
            output_format: Output format of the generated audio. Formatted as codec_sample_rate_bitrate. Defaults to mp3_44100_128.

        Returns:
            Dictionary containing the base64-encoded MP3 audio and metadata
        """
        logger.info("Executing create_speech")

        # Use the ElevenLabs SDK to convert text to speech
        audio_generator = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            voice_settings=voice_settings,
            output_format=output_format,
        )

        # Convert the generator to bytes
        audio_bytes = b"".join(audio_generator)

        # Convert audio bytes to base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        logger.info(
            f"Generated speech, bytes={len(audio_bytes)}, voice_id={voice_id}, model_id={model_id}, output_format={output_format}"
        )

        return {
            "audio_base64": audio_base64,
            "voice_id": voice_id,
            "text_length": len(text),
            "model_id": model_id,
            "output_format": output_format,
        }
