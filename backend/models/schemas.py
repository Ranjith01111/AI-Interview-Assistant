"""
Pydantic models (schemas) for the AI Interview Assistant.
These define the shape of request/response data.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class QuestionType(str, Enum):
    """Type of interview question"""
    TECHNICAL = "technical"
    HR = "hr"
    BEHAVIORAL = "behavioral"


class InterviewQuestion(BaseModel):
    """A single interview question"""
    id: int
    question: str
    type: QuestionType
    topic: str = ""  # e.g., "Python", "Leadership", etc.


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
