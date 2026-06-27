"""
Voice Service — Edge-TTS Integration for AI Interview Assistant

Uses edge-tts (Microsoft Neural Voices) for high-quality server-side TTS.
Browser Web Speech API remains the STT engine (frontend handles transcription).

Dependencies: edge-tts (already in requirements.txt)
"""

import io
import asyncio
from typing import Optional

from backend.core.logging import get_logger

logger = get_logger("backend.services.voice_service")

# ─── Configuration ───────────────────────────────────────────────────────────

# Default voice: en-US-AriaNeural is a warm, professional female voice
# ideal for interview scenarios. Alternatives:
#   - "en-US-GuyNeural"       (male, conversational)
#   - "en-US-JennyNeural"     (female, friendly)
#   - "en-GB-SoniaNeural"     (British female)
#   - "en-US-DavisNeural"     (male, calm)
DEFAULT_VOICE = "en-US-AriaNeural"

# Speech rate adjustment (negative = slower, positive = faster)
# Slightly slower for interview clarity
DEFAULT_RATE = "-5%"

# Pitch adjustment
DEFAULT_PITCH = "+0Hz"

# Output format — MP3 is compact and widely supported for WebSocket streaming
OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"


# ─── TTS Engine ──────────────────────────────────────────────────────────────

async def text_to_speech(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
) -> bytes:
    """
    Convert text to speech audio bytes using Microsoft Edge TTS (neural voices).

    Args:
        text:  The text to synthesize into speech.
        voice: The Edge TTS voice identifier (e.g., "en-US-AriaNeural").
        rate:  Speech rate adjustment (e.g., "-5%", "+10%").
        pitch: Pitch adjustment (e.g., "+2Hz", "-1Hz").

    Returns:
        MP3 audio bytes ready for streaming over WebSocket, or empty bytes
        if synthesis fails (graceful degradation to browser TTS).
    """
    if not text or not text.strip():
        logger.warning("text_to_speech_called_with_empty_text")
        return b""

    # Trim excessively long text to prevent timeouts (cap at ~2000 chars)
    max_chars = 2000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
        logger.info("text_to_speech_text_truncated", original_length=len(text))

    try:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )

        # Collect all audio chunks into a buffer
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        audio_bytes = buffer.getvalue()

        if not audio_bytes:
            logger.warning("text_to_speech_produced_empty_audio", text_length=len(text))
            return b""

        logger.info(
            "text_to_speech_success",
            text_length=len(text),
            audio_size=len(audio_bytes),
            voice=voice,
        )
        return audio_bytes

    except ImportError:
        logger.error(
            "edge_tts_not_installed",
            hint="Install with: pip install edge-tts",
        )
        return b""

    except Exception as e:
        logger.error(
            "text_to_speech_failed",
            error=str(e),
            text_length=len(text),
            voice=voice,
        )
        return b""


async def text_to_speech_streaming(
    text: str,
    voice: str = DEFAULT_VOICE,
    rate: str = DEFAULT_RATE,
    pitch: str = DEFAULT_PITCH,
):
    """
    Async generator that yields audio chunks as they're produced by edge-tts.

    Use this for real-time streaming over WebSocket when you want to send
    audio progressively rather than waiting for the full synthesis to complete.

    Yields:
        bytes: Audio chunks (MP3 fragments) as they become available.
    """
    if not text or not text.strip():
        return

    try:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio" and chunk["data"]:
                yield chunk["data"]

    except ImportError:
        logger.error("edge_tts_not_installed_streaming")
        return

    except Exception as e:
        logger.error("text_to_speech_streaming_failed", error=str(e))
        return


# ─── STT (Browser-Based) ────────────────────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Transcription placeholder — STT is handled on the frontend via Web Speech API.

    The frontend captures audio via the browser's built-in speech recognition,
    converts it to text, and sends the text directly over WebSocket. This function
    exists as a fallback if raw audio bytes are ever sent to the backend.

    Args:
        audio_bytes: Raw audio data (not used in current architecture).
        filename:    Original filename hint.

    Returns:
        A placeholder string indicating browser STT should be used.
    """
    logger.info(
        "transcribe_audio_called_but_using_browser_stt",
        size=len(audio_bytes),
        filename=filename,
    )
    return "[Voice transcription is handled by your browser. Please ensure microphone access is granted.]"


# ─── Utility ─────────────────────────────────────────────────────────────────

async def list_available_voices(language_filter: str = "en-") -> list[dict]:
    """
    List available Edge TTS voices, optionally filtered by language prefix.

    Useful for allowing users to select their preferred interview voice.

    Returns:
        List of voice dictionaries with name, gender, and locale info.
    """
    try:
        import edge_tts

        voices = await edge_tts.list_voices()
        if language_filter:
            voices = [v for v in voices if v.get("Locale", "").startswith(language_filter)]
        return voices

    except ImportError:
        logger.error("edge_tts_not_installed_list_voices")
        return []

    except Exception as e:
        logger.error("list_voices_failed", error=str(e))
        return []
