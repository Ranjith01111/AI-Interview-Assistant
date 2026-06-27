"""
Recruiter Notes API Routes

CRUD endpoints for recruiter notes attached to interview sessions.
Supports private (author-only) and shared visibility modes.

Routes:
    POST   /api/v1/recruiter/sessions/{session_id}/notes  — Create a note
    GET    /api/v1/recruiter/sessions/{session_id}/notes  — List notes for session
    DELETE /api/v1/recruiter/notes/{note_id}              — Delete own note
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.db.session import get_db
from backend.models.recruiter_note import RecruiterNote
from backend.models.interview import InterviewSession
from backend.models.user import User, UserRole
from backend.core.security import get_current_active_user, require_role

router = APIRouter(
    prefix="/recruiter",
    tags=["Recruiter Notes"],
)


# —— Request / Response Schemas ————————————————————————————————————

class NoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="Note text content")
    is_private: bool = Field(default=True, description="If true, only visible to the author")


class NoteResponse(BaseModel):
    id: str
    content: str
    recruiter_id: str
    recruiter_name: str
    is_private: bool
    created_at: str

    class Config:
        from_attributes = True


class NotesListResponse(BaseModel):
    notes: list[NoteResponse]
    total: int


class NoteDeleteResponse(BaseModel):
    success: bool
    message: str


# —— Helper ————————————————————————————————————————————————————————

async def _validate_session_exists(session_id: str, db: AsyncSession) -> InterviewSession:
    """Validate session_id format and existence."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id format. Must be a valid UUID.",
        )

    result = await db.execute(
        select(InterviewSession).where(InterviewSession.id == session_uuid)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found.",
        )
    return session


# —— Endpoints ————————————————————————————————————————————————————

@router.post(
    "/sessions/{session_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    session_id: str,
    payload: NoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
):
    """
    Create a recruiter note for an interview session.

    Access: Admin, Recruiter only.
    """
    await _validate_session_exists(session_id, db)

    note = RecruiterNote(
        session_id=uuid.UUID(session_id),
        recruiter_id=current_user.id,
        content=payload.content.strip(),
        is_private=payload.is_private,
    )
    db.add(note)
    await db.flush()
    await db.refresh(note)

    return NoteResponse(
        id=str(note.id),
        content=note.content,
        recruiter_id=str(note.recruiter_id),
        recruiter_name=current_user.name,
        is_private=note.is_private,
        created_at=note.created_at.isoformat(),
    )


@router.get(
    "/sessions/{session_id}/notes",
    response_model=NotesListResponse,
)
async def list_notes(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
):
    """
    List all notes for an interview session.

    Visibility rules:
      - Shared notes (is_private=False) visible to all recruiters/admins
      - Private notes (is_private=True) visible ONLY to the author

    Access: Admin, Recruiter only.
    """
    await _validate_session_exists(session_id, db)
    session_uuid = uuid.UUID(session_id)

    # Fetch notes: shared notes OR private notes authored by current user
    result = await db.execute(
        select(RecruiterNote)
        .where(
            and_(
                RecruiterNote.session_id == session_uuid,
                # Show shared notes OR private notes belonging to current user
                (RecruiterNote.is_private == False) | (RecruiterNote.recruiter_id == current_user.id),  # noqa: E712
            )
        )
        .order_by(RecruiterNote.created_at.desc())
    )
    notes = result.scalars().all()

    # Resolve recruiter names via eager/lazy load
    note_responses = []
    for note in notes:
        # Access the relationship to get recruiter name
        recruiter = await db.get(User, note.recruiter_id)
        recruiter_name = recruiter.name if recruiter else "Unknown"

        note_responses.append(NoteResponse(
            id=str(note.id),
            content=note.content,
            recruiter_id=str(note.recruiter_id),
            recruiter_name=recruiter_name,
            is_private=note.is_private,
            created_at=note.created_at.isoformat(),
        ))

    return NotesListResponse(notes=note_responses, total=len(note_responses))


@router.delete(
    "/notes/{note_id}",
    response_model=NoteDeleteResponse,
)
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
):
    """
    Delete a recruiter note.

    Only the note author can delete their own note.
    Admins can delete any note.

    Access: Admin, Recruiter (own notes only).
    """
    try:
        note_uuid = uuid.UUID(note_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid note_id format. Must be a valid UUID.",
        )

    result = await db.execute(
        select(RecruiterNote).where(RecruiterNote.id == note_uuid)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found.",
        )

    # Authorization: only the author or an admin can delete
    if current_user.role != UserRole.ADMIN.value and note.recruiter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notes.",
        )

    await db.delete(note)
    await db.flush()

    return NoteDeleteResponse(success=True, message="Note deleted successfully.")
