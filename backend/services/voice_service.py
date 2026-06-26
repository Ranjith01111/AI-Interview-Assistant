"""
Voice Service — STANDALONE VERSION (No External APIs)

Uses browser-native Web Speech API for STT/TTS (handled on frontend).
Backend only processes text answers — no audio transcription needed server-side.
"""

from backend.core.logging import get_logger

logger = get_logger("backend.services.voice_service")


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """
    Fallback transcription — in standalone mode, STT is done on the frontend
    using the Web Speech API. This function is only called if raw audio is sent.
    
    Returns a placeholder message instructing to use browser STT.
    """
    logger.info("transcribe_audio_called_but_using_browser_stt", size=len(audio_bytes))
    return "[Voice transcription is handled by your browser. Please ensure microphone access is granted.]"


async def text_to_speech(text: str, voice: str = "alloy") -> bytes:
    """
    In standalone mode, TTS is done on the frontend using the Web Speech API.
    Returns empty bytes — the frontend handles speech synthesis.
    """
    return b""
