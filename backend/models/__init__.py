"""
Models package — aggregates all ORM models for Alembic auto-detection
and provides convenient imports.
"""

# ORM models (SQLAlchemy)
from backend.models.interview import InterviewSession, SessionStatus
from backend.models.question import Question
from backend.models.answer import Answer
from backend.models.user import User, UserRole
from backend.models.audit_log import AuditLog
from backend.models.resume import Resume
from backend.models.proctor_log import ProctorLog
from backend.models.analytics import Analytics
from backend.models.question_embedding import QuestionEmbedding
from backend.models.coding_challenge import CodingChallenge
from backend.models.coding_submission import CodingSubmission

# New recruiter models — safe import (may fail if base class mismatch)
try:
    from backend.models.pipeline_history import PipelineHistory
    from backend.models.recruiter_note import RecruiterNote
except Exception:
    pass

# Pydantic schemas
from backend.models.schemas import (
    QuestionType,
    QuestionCategory,
    DifficultyLevel,
    ProjectDetail,
    ProjectContext,
    InterviewQuestion,
    ResumeUploadResponse,
    GenerateQuestionsResponse,
    ChatMessage,
    ChatRequest,
    FeedbackDetail,
    ChatResponse,
    SessionSummaryResponse,
    AgentEvaluation,
    FollowUpInfo,
    InterviewTurnResult,
    ConversationTurn,
)
from backend.models.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    UserListResponse,
    MessageResponse,
)

__all__ = [
    # ORM
    "InterviewSession",
    "SessionStatus",
    "Question",
    "Answer",
    "User",
    "UserRole",
    "AuditLog",
    "Resume",
    "ProctorLog",
    "Analytics",
    "QuestionEmbedding",
    "CodingChallenge",
    "CodingSubmission",
    # Pydantic
    "QuestionType",
    "QuestionCategory",
    "DifficultyLevel",
    "ProjectDetail",
    "ProjectContext",
    "InterviewQuestion",
    "ResumeUploadResponse",
    "GenerateQuestionsResponse",
    "ChatMessage",
    "ChatRequest",
    "FeedbackDetail",
    "ChatResponse",
    "SessionSummaryResponse",
    "AgentEvaluation",
    "FollowUpInfo",
    "InterviewTurnResult",
    "ConversationTurn",
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "TokenResponse",
    "UserResponse",
    "UserListResponse",
    "MessageResponse",
]
