"""
Pydantic models (schemas) for the AI Interview Assistant.
These define the shape of request/response data.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


class QuestionType(str, Enum):
    """Type of interview question"""
    TECHNICAL = "technical"
    HR = "hr"
    BEHAVIORAL = "behavioral"


class QuestionCategory(str, Enum):
    """Category of context-aware question — determines which prompt template is used."""
    PROJECT_BASED = "project_based"
    CHALLENGE = "challenge"
    ARCHITECTURE = "architecture"
    DEBUGGING = "debugging"
    GENERAL = "general"


class DifficultyLevel(str, Enum):
    """Difficulty grading for each question."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ProjectDetail(BaseModel):
    """A single project extracted from the candidate's resume."""
    name: str
    role: str = ""
    tech_stack: List[str] = []
    challenge: str = ""
    solution: str = ""
    outcome: str = ""


class ProjectContext(BaseModel):
    """Full structured context extracted from a resume — used as input for question generation."""
    projects: List[ProjectDetail] = []
    primary_skills: List[str] = []
    experience_level: str = "mid"
    domain_expertise: List[str] = []


class InterviewQuestion(BaseModel):
    """A single interview question"""
    id: int
    question: str
    type: QuestionType
    topic: str = ""  # e.g., "Python", "Leadership", etc.
    category: QuestionCategory = QuestionCategory.PROJECT_BASED
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    project_reference: str = ""

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_int(cls, v):
        """Accept string IDs like 'dsa_004' and convert to sequential int."""
        if isinstance(v, int):
            return v
        # Try parsing digits from the string; fallback to hash-based int
        import re
        match = re.search(r"(\d+)", str(v))
        return int(match.group(1)) if match else abs(hash(v)) % 10000


class ResumeUploadResponse(BaseModel):
    """Response after uploading and processing a resume"""
    success: bool
    message: str
    session_id: str  # Unique session ID for this interview
    candidate_name: str = "Candidate"
    skills_detected: List[str] = []
    experience_years: str = "Not specified"


class GenerateQuestionsResponse(BaseModel):
    """Response containing generated interview questions"""
    success: bool
    session_id: str
    questions: List[InterviewQuestion]
    total_questions: int


class ChatMessage(BaseModel):
    """A single message in the chat"""
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request to send a message in the interview chat"""
    session_id: str
    message: str  # User's answer to the current question


class FeedbackDetail(BaseModel):
    """Detailed feedback for a single answer"""
    model_config = {
        "protected_namespaces": (),
    }
    score: int = Field(ge=0, le=10, description="Score from 0 to 10")
    strengths: List[str] = []
    improvements: List[str] = []
    model_answer_hint: str = ""


class ChatResponse(BaseModel):
    """Response from the interview chat"""
    success: bool
    session_id: str
    message: str           # Next question or closing message
    feedback: Optional[FeedbackDetail] = None
    is_interview_complete: bool = False
    current_question_number: int = 0
    total_questions: int = 0
    # ── Interview Agent extensions ───────────────────────────────────
    is_follow_up: bool = False
    follow_up_depth: int = 0
    evaluation: Optional["AgentEvaluation"] = None


class SessionSummaryResponse(BaseModel):
    """Final interview summary for the session"""
    success: bool
    session_id: str
    candidate_name: str
    total_questions: int
    answered_questions: int
    average_score: float
    overall_feedback: str
    score_breakdown: List[dict] = []  # List of {question, score, feedback}
    recommendation: str = ""  # e.g., "Strong Hire", "Consider", "No Hire"


# =====================================================================
# Interview Agent Models
# =====================================================================

class AgentEvaluation(BaseModel):
    """Structured evaluation result from the Interview Agent."""
    model_config = {
        "protected_namespaces": (),
    }
    score: int = Field(ge=0, le=10, description="Score from 0 to 10")
    depth: str = Field(default="shallow", description="shallow | moderate | deep")
    strengths: List[str] = []
    gaps: List[str] = []
    follow_up_worthy: bool = False
    follow_up_angle: str = ""
    model_answer_hint: str = ""
    acknowledgment: str = "Thank you for your answer."


class FollowUpInfo(BaseModel):
    """Metadata about a follow-up decision."""
    triggered: bool = False
    reason: str = ""           # e.g., "brief_answer", "keyword_trigger", "low_score"
    depth: int = 0             # How many follow-ups deep (0 = base question)
    max_reached: bool = False  # True if at follow-up limit


class InterviewTurnResult(BaseModel):
    """Complete result of a single interview turn — used internally by the agent."""
    evaluation: AgentEvaluation
    follow_up: FollowUpInfo
    next_message: str          # The message to send to the candidate
    is_complete: bool = False  # True if interview is finished
    current_question_number: int = 0
    total_questions: int = 0


class ConversationTurn(BaseModel):
    """A single turn in the interview conversation — stored in agent memory."""
    role: str                  # "interviewer" or "candidate"
    content: str
    question_index: int = 0    # Which base question this relates to
    is_follow_up: bool = False
    follow_up_depth: int = 0
    score: Optional[int] = None

