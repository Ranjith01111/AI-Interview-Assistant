"""
Session Service — Redis-backed session state management.

Replaces the old in-memory `utils/session_store.py`.
Stores ephemeral data (FAISS vector stores, LangChain chains) in Redis
while persistent data (scores, answers) lives in PostgreSQL.
"""

from typing import Any, Dict, List, Optional

from backend.core.config import settings
from backend.db.redis import (
    redis_set_json,
    redis_get_json,
    redis_set_pickle,
    redis_get_pickle,
    redis_set_bytes,
    redis_get_bytes,
    redis_delete,
)

# Key prefixes for different data types
_PREFIX_SESSION = "session:"
_PREFIX_VECTORSTORE = "vectorstore:"
_PREFIX_CHAIN = "chain:"
_PREFIX_QUESTIONS = "questions:"
_PREFIX_FEEDBACK = "feedback:"
_PREFIX_STATE = "state:"
_PREFIX_PROJECTS = "projects:"
_PREFIX_DEDUP = "dedup:"
_PREFIX_AGENT = "agent:"
_PREFIX_PARSED_RESUME = "parsed_resume:"


# ── Session metadata (JSON) ─────────────────────────────────────────

async def save_session_meta(
    session_id: str,
    candidate_name: str,
    skills: List[str],
    experience: str,
    resume_text: str,
) -> None:
    """Store lightweight session metadata in Redis."""
    await redis_set_json(
        f"{_PREFIX_SESSION}{session_id}",
        {
            "session_id": session_id,
            "candidate_name": candidate_name,
            "skills": skills,
            "experience": experience,
            "resume_text": resume_text,
        },
    )


async def get_session_meta(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session metadata."""
    return await redis_get_json(f"{_PREFIX_SESSION}{session_id}")


# ── FAISS vector store (native bytes — pickle-free) ──────────────────
# FAISS C-extension objects contain _thread.RLock which cannot be pickled.
# Use FAISS's own faiss.serialize_index path via serialize_to_bytes().

async def save_vector_store(session_id: str, vector_store: Any = None) -> None:
    """No-op in standalone mode — FAISS not used."""
    pass


async def get_vector_store(session_id: str) -> Optional[Any]:
    """No-op in standalone mode — returns True to indicate session exists."""
    # Check if parsed resume exists instead
    return await get_parsed_resume(session_id)


# ── LangChain conversation chain (pickle) ───────────────────────────

async def save_conversation_chain(session_id: str, chain: Any) -> None:
    """Store the LangChain ConversationChain in Redis."""
    await redis_set_pickle(f"{_PREFIX_CHAIN}{session_id}", chain)


async def get_conversation_chain(session_id: str) -> Optional[Any]:
    """Retrieve the ConversationChain."""
    return await redis_get_pickle(f"{_PREFIX_CHAIN}{session_id}")


# ── Questions cache (JSON-safe representation) ──────────────────────

async def save_questions_cache(session_id: str, questions: List[Dict]) -> None:
    """Cache generated questions in Redis for fast retrieval."""
    await redis_set_json(f"{_PREFIX_QUESTIONS}{session_id}", questions)


async def get_questions_cache(session_id: str) -> Optional[List[Dict]]:
    """Retrieve cached questions."""
    return await redis_get_json(f"{_PREFIX_QUESTIONS}{session_id}")


# ── Interview state (current question index, etc.) ──────────────────

async def save_interview_state(session_id: str, state: Dict[str, Any]) -> None:
    """Store current interview progress."""
    await redis_set_json(f"{_PREFIX_STATE}{session_id}", state)


async def get_interview_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve interview progress state."""
    return await redis_get_json(f"{_PREFIX_STATE}{session_id}")


# ── Answer feedback accumulator ──────────────────────────────────────

async def add_answer_feedback(session_id: str, feedback_entry: Dict) -> None:
    """Append a single answer's feedback to the session's list."""
    key = f"{_PREFIX_FEEDBACK}{session_id}"
    existing = await redis_get_json(key)
    if existing is None:
        existing = []
    existing.append(feedback_entry)
    await redis_set_json(key, existing)


async def get_all_feedback(session_id: str) -> List[Dict]:
    """Return all answer feedback entries."""
    result = await redis_get_json(f"{_PREFIX_FEEDBACK}{session_id}")
    return result or []


async def clear_feedback(session_id: str) -> None:
    """Clear stored feedback (used when restarting an interview)."""
    await redis_delete(f"{_PREFIX_FEEDBACK}{session_id}")


# ── Project context (JSON) ──────────────────────────────────────────

async def save_project_context(session_id: str, project_context: dict) -> None:
    """Cache extracted structured project JSON in Redis."""
    await redis_set_json(f"{_PREFIX_PROJECTS}{session_id}", project_context)


async def get_project_context(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached project context."""
    return await redis_get_json(f"{_PREFIX_PROJECTS}{session_id}")


# ── Anti-Repetition dedup FAISS index (pickle/bytes) ────────────────

async def save_dedup_index(session_id: str, index_data: bytes) -> None:
    """Cache the serialized FAISS dedup index in Redis."""
    await redis_set_pickle(f"{_PREFIX_DEDUP}{session_id}", index_data)


async def get_dedup_index(session_id: str) -> Optional[bytes]:
    """Retrieve the cached FAISS dedup index."""
    return await redis_get_pickle(f"{_PREFIX_DEDUP}{session_id}")


# ── Interview Agent state (pickle — full agent object) ──────────────

async def save_agent_state(session_id: str, agent_state: Any) -> None:
    """Persist the InterviewAgent state (memory, progress, scores) to Redis."""
    await redis_set_pickle(f"{_PREFIX_AGENT}{session_id}", agent_state)


async def get_agent_state(session_id: str) -> Optional[Any]:
    """Retrieve the serialized InterviewAgent state."""
    return await redis_get_pickle(f"{_PREFIX_AGENT}{session_id}")


# ── Parsed resume data (JSON) — replaces FAISS in standalone mode ──

async def save_parsed_resume(session_id: str, parsed_data: dict) -> None:
    """Store structured resume parse result in Redis."""
    await redis_set_json(f"{_PREFIX_PARSED_RESUME}{session_id}", parsed_data)


async def get_parsed_resume(session_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve parsed resume data."""
    return await redis_get_json(f"{_PREFIX_PARSED_RESUME}{session_id}")


# ── Cleanup ──────────────────────────────────────────────────────────

async def delete_session_cache(session_id: str) -> None:
    """Remove ALL Redis keys for a given session."""
    for prefix in (
        _PREFIX_SESSION,
        _PREFIX_VECTORSTORE,
        _PREFIX_CHAIN,
        _PREFIX_QUESTIONS,
        _PREFIX_FEEDBACK,
        _PREFIX_STATE,
        _PREFIX_PROJECTS,
        _PREFIX_DEDUP,
        _PREFIX_AGENT,
        _PREFIX_PARSED_RESUME,
    ):
        await redis_delete(f"{prefix}{session_id}")

