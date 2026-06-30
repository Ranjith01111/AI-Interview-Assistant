"""
NLP Interview Engine — Standalone, no external APIs.

Provides:
  • resume_parser      — Extract skills, experience, projects from PDF text
  • question_bank      — 245+ question templates by skill/difficulty
  • question_generator — Select personalized questions for a candidate
  • answer_evaluator   — Score answers with keyword matching + length analysis
  • feedback_generator — Human-readable feedback from evaluation scores
  • interview_presets  — Pre-configured interview mode presets
"""

from backend.nlp_engine.resume_parser import parse_resume_structured
from backend.nlp_engine.question_generator import generate_questions_for_candidate
from backend.nlp_engine.answer_evaluator import evaluate_answer
from backend.nlp_engine.feedback_generator import generate_feedback, generate_final_summary
from backend.nlp_engine.interview_presets import get_all_presets, get_preset

__all__ = [
    "parse_resume_structured",
    "generate_questions_for_candidate",
    "evaluate_answer",
    "generate_feedback",
    "generate_final_summary",
    "get_all_presets",
    "get_preset",
]
