"""
tts_service.py - Text-to-speech service for LexGuard.

Primary: Google Cloud Text-to-Speech API (REST)
Fallback: Signals client to use Web Speech API
"""

import base64
import logging
from typing import Optional

import requests

from ..utils.constants import TTS_LANGUAGE_CODE, TTS_VOICE_NAME, TTS_AUDIO_ENCODING

logger = logging.getLogger(__name__)

_google_tts_api_key: str = ""


def init_tts(api_key: str) -> None:
    """Configure the Google TTS API key.

    Args:
        api_key: Google Cloud Text-to-Speech API key.
    """
    global _google_tts_api_key
    _google_tts_api_key = api_key
    logger.info("TTS service initialised.")


def _synthesize_via_google(text: str, language_code: str, voice_name: str) -> Optional[str]:
    """Call Google Cloud TTS REST endpoint and return base64 audio.

    Args:
        text: Text to synthesize (max 5000 chars).
        language_code: BCP-47 language code.
        voice_name: Google TTS voice name.

    Returns:
        Base64-encoded MP3 audio string, or None on failure.
    """
    if not _google_tts_api_key:
        return None

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={_google_tts_api_key}"
    payload = {
        "input": {"text": text[:4500]},
        "voice": {"languageCode": language_code, "name": voice_name},
        "audioConfig": {"audioEncoding": TTS_AUDIO_ENCODING},
    }
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json().get("audioContent")
    except Exception as exc:
        logger.warning("Google TTS failed: %s", exc)
        return None


def synthesize_speech(
    text: str,
    language_code: str = TTS_LANGUAGE_CODE,
    voice_name: str = TTS_VOICE_NAME,
) -> dict:
    """Convert text to speech audio.

    Args:
        text: Text to be spoken.
        language_code: Target language BCP-47 code.
        voice_name: Google TTS voice name to use.

    Returns:
        Dict with keys:
            - 'audio_base64': base64 MP3 audio (or None)
            - 'source': 'google' or 'web_speech_api'
            - 'success': bool
            - 'fallback_text': text for Web Speech API fallback
    """
    audio = _synthesize_via_google(text, language_code, voice_name)
    if audio:
        return {
            "audio_base64": audio,
            "source": "google",
            "success": True,
            "fallback_text": text,
        }

    logger.info("Google TTS unavailable; client will use Web Speech API.")
    return {
        "audio_base64": None,
        "source": "web_speech_api",
        "success": False,
        "fallback_text": text,
    }
