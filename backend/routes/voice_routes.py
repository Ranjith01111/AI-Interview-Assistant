"""
Voice WebSocket Router — Handles real-time voice interview streaming.
"""

import json
import re
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: F401 - used in type hints

from backend.db.session import AsyncSessionLocal
from backend.core.logging import get_logger
from backend.services.voice_service import transcribe_audio, text_to_speech
from backend.services.interview_service import start_interview, process_interview_message
from backend.services.interview_agent import InterviewAgent

logger = get_logger("backend.routes.voice_routes")

router = APIRouter(prefix="/interview", tags=["Voice Interview"])


@router.websocket("/voice-stream/{session_id}")
async def websocket_voice_stream(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time voice streaming interview.
    Accepts candidate audio chunks, transcribes them with Whisper,
    interacts with the Interview Agent, and streams TTS audio back.
    """
    await websocket.accept()
    logger.info("voice_websocket_connected", session_id=session_id)

    try:
        # 1. Sync / Initialize the interview state
        agent = await InterviewAgent.restore(session_id)
        
        greeting_text = ""
        if agent is None:
            # Interview hasn't started yet, so trigger start
            logger.info("starting_interview_via_voice", session_id=session_id)
            async with AsyncSessionLocal() as db:
                chat_response = await start_interview(session_id, db)
                greeting_text = chat_response.message
                await db.commit()
        else:
            # Interview already started, retrieve the active question
            logger.info("resuming_interview_via_voice", session_id=session_id)
            # Find the last interviewer message
            greeting_text = next(
                (msg["content"] for msg in reversed(agent.state.conversation_history) if msg["role"] == "interviewer"),
                "Let's continue the interview."
            )

        # Send initial question text and voice
        await websocket.send_json({
            "type": "text",
            "text": greeting_text,
            "is_complete": False
        })
        
        # TTS for the greeting
        clean_text = clean_markdown(greeting_text)
        await websocket.send_json({"type": "state", "status": "speaking"})
        audio_bytes = await text_to_speech(clean_text)
        if audio_bytes:
            await websocket.send_bytes(audio_bytes)
        
        await websocket.send_json({"type": "state", "status": "listening"})

        # 2. Main message loop
        audio_buffer = bytearray()
        is_recording = False

        while True:
            # Receive message from WebSocket
            message = await websocket.receive()
            
            if "text" in message:
                try:
                    payload = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue
                
                msg_type = payload.get("type")
                if msg_type == "start_recording":
                    audio_buffer.clear()
                    is_recording = True
                    logger.info("candidate_started_recording", session_id=session_id)
                elif msg_type == "stop_recording":
                    is_recording = False
                    text_answer = payload.get("text")
                    if text_answer:
                        logger.info("candidate_submitted_local_text", session_id=session_id, length=len(text_answer))
                        await process_candidate_text_answer(websocket, text_answer, session_id)
                    else:
                        logger.info("candidate_stopped_recording", session_id=session_id, size=len(audio_buffer))
                        await process_candidate_voice(websocket, audio_buffer, session_id)
                    # Clear buffer after processing
                    audio_buffer.clear()
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
            
            elif "bytes" in message:
                if is_recording:
                    audio_buffer.extend(message["bytes"])

    except WebSocketDisconnect:
        logger.info("voice_websocket_disconnected_by_client", session_id=session_id)
    except Exception as e:
        logger.error("voice_websocket_error", error=str(e), session_id=session_id)
        try:
            await websocket.send_json({"type": "error", "message": f"Server error: {str(e)}"})
        except Exception:
            pass


def clean_markdown(text: str) -> str:
    """Helper to clean markdown syntax for text-to-speech rendering."""
    # Keep bold text content, just remove the ** markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    # Remove symbols and line breaks
    text = text.replace("❓", "").replace("💡", "").replace("👋", "").replace("🎉", "")
    text = text.replace("---", "").strip()
    return text


async def process_candidate_voice(
    websocket: WebSocket,
    audio_bytes: bytes,
    session_id: str,
):
    """Transcribe audio, pass to agent, and play back next question."""
    if not audio_bytes or len(audio_bytes) < 100:
        await websocket.send_json({
            "type": "error",
            "message": "Audio was too short or silent. Please try again."
        })
        await websocket.send_json({"type": "state", "status": "listening"})
        return

    # Update state to processing
    await websocket.send_json({"type": "state", "status": "processing"})

    # Transcribe candidate answer
    transcript = await transcribe_audio(audio_bytes, filename="answer.webm")
    if not transcript or transcript.strip() == "[Inaudible response or transcription error]":
        await websocket.send_json({
            "type": "error",
            "message": "Could not understand your answer. Please repeat clearly."
        })
        await websocket.send_json({"type": "state", "status": "listening"})
        return

    # Send transcript back for frontend display
    await websocket.send_json({"type": "transcript", "text": transcript})

    try:
        # Feed transcript into interview system (per-operation DB session)
        async with AsyncSessionLocal() as db:
            chat_response = await process_interview_message(session_id, transcript, db)
            await db.commit()
    except Exception as e:
        logger.error("agent_processing_failed", error=str(e))
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to process answer: {str(e)}"
        })
        await websocket.send_json({"type": "state", "status": "listening"})
        return

    # Package feedback details
    feedback_dict = None
    if chat_response.feedback:
        feedback_dict = chat_response.feedback.model_dump()

    # Send text response back
    await websocket.send_json({
        "type": "text",
        "text": chat_response.message,
        "is_complete": chat_response.is_interview_complete,
        "feedback": feedback_dict
    })

    if chat_response.is_interview_complete:
        await websocket.send_json({"type": "state", "status": "completed"})
        return

    # Convert AI's next question to speech
    clean_text = clean_markdown(chat_response.message)
    await websocket.send_json({"type": "state", "status": "speaking"})
    
    tts_audio = await text_to_speech(clean_text)
    if tts_audio:
        await websocket.send_bytes(tts_audio)

    await websocket.send_json({"type": "state", "status": "listening"})


async def process_candidate_text_answer(
    websocket: WebSocket,
    transcript: str,
    session_id: str,
):
    """Process transcribed text directly without running server-side STT."""
    # Send transcript back for frontend display
    await websocket.send_json({"type": "transcript", "text": transcript})

    try:
        # Feed transcript into interview system (per-operation DB session)
        async with AsyncSessionLocal() as db:
            chat_response = await process_interview_message(session_id, transcript, db)
            await db.commit()
    except Exception as e:
        logger.error("agent_processing_failed", error=str(e))
        await websocket.send_json({
            "type": "error",
            "message": f"Failed to process answer: {str(e)}"
        })
        await websocket.send_json({"type": "state", "status": "listening"})
        return

    # Package feedback details
    feedback_dict = None
    if chat_response.feedback:
        feedback_dict = chat_response.feedback.model_dump()

    # Send text response back
    await websocket.send_json({
        "type": "text",
        "text": chat_response.message,
        "is_complete": chat_response.is_interview_complete,
        "feedback": feedback_dict
    })

    if chat_response.is_interview_complete:
        await websocket.send_json({"type": "state", "status": "completed"})
        return

    # Convert AI's next question to speech
    clean_text = clean_markdown(chat_response.message)
    await websocket.send_json({"type": "state", "status": "speaking"})
    
    tts_audio = await text_to_speech(clean_text)
    if tts_audio:
        await websocket.send_bytes(tts_audio)

    await websocket.send_json({"type": "state", "status": "listening"})

