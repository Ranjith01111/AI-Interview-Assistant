"""
TTS Route — Serves audio for voice interview HR questions.
Uses edge-tts (free Microsoft neural voices, no API key).
Falls back to gTTS if edge-tts is unavailable.
"""

import io
import asyncio
from fastapi import APIRouter, Query, Request, Depends
from fastapi.responses import StreamingResponse

from backend.core.security import get_current_active_user
from backend.core.rate_limiter import limiter
from backend.models.user import User

router = APIRouter(prefix="/tts", tags=["TTS"])

# Try edge-tts first, then gTTS
_engine = None

async def _get_engine():
    global _engine
    if _engine: return _engine
    try:
        import edge_tts
        _engine = "edge"
        return _engine
    except ImportError:
        pass
    try:
        from gtts import gTTS
        _engine = "gtts"
        return _engine
    except ImportError:
        pass
    # Last resort: pyttsx3 (saves to file)
    try:
        import pyttsx3
        _engine = "pyttsx3"
        return _engine
    except ImportError:
        _engine = "none"
        return _engine


@router.get("/speak")
@limiter.limit("20/minute")
async def speak_text(request: Request, text: str = Query(..., max_length=500)):
    """
    Convert text to speech audio (MP3).
    Returns audio/mpeg stream.
    """
    engine = await _get_engine()

    if engine == "edge":
        import edge_tts
        # en-US-AriaNeural = warm female, natural conversational tone
        # Rate slightly slower for clarity
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural", rate="-8%", pitch="+2Hz")
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="audio/mpeg",
                                 headers={"Cache-Control": "public, max-age=3600"})

    elif engine == "gtts":
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', slow=False)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="audio/mpeg",
                                 headers={"Cache-Control": "public, max-age=3600"})

    elif engine == "pyttsx3":
        import pyttsx3
        import tempfile, os
        eng = pyttsx3.init()
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        eng.save_to_file(text, tmp.name)
        eng.runAndWait()
        buffer = io.BytesIO(open(tmp.name, 'rb').read())
        os.unlink(tmp.name)
        return StreamingResponse(buffer, media_type="audio/mpeg")

    else:
        # No TTS engine available — return silence or error
        return StreamingResponse(
            io.BytesIO(b""),
            media_type="audio/mpeg",
            status_code=503,
            headers={"X-Error": "No TTS engine installed. Run: pip install edge-tts"}
        )
