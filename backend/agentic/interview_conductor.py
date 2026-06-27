"""
Interview Conductor — Natural, adaptive interview conversation using llama3.

Replaces the static state machine with an intelligent conversational agent
that generates natural transitions, contextual follow-ups, and adaptive phrasing.

Capabilities:
- Adapts question phrasing based on candidate's experience level
- Generates contextual follow-up questions based on evaluation
- Provides encouraging, specific transitions between questions
- Adjusts tone dynamically based on performance trajectory
- Generates personalized introduction and closing

100% local via Ollama/llama3.
"""

import time
from typing import Any, Dict, List, Optional

from .agent_config import get_agentic_config, AgenticConfig
from .ollama_client import get_ollama_client, OllamaClient

# ── Logger Setup ─────────────────────────────────────────────────────────────
try:
    from backend.core.logging import get_logger
    logger = get_logger("backend.agentic.interview_conductor")
except ImportError:
    import logging
    logger = logging.getLogger("agentic.interview_conductor")


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

CONDUCTOR_SYSTEM_PROMPT = """You are a friendly, professional technical interviewer conducting a practice interview. Your personality:
- Warm and encouraging, but professional
- You acknowledge good answers specifically
- You transition smoothly between topics
- You never reveal scores directly in conversation
- You keep responses concise (2-4 sentences max)
- You address the candidate by name when appropriate

Important: You are conducting a PRACTICE interview to help the candidate improve. Be supportive."""

INTRODUCTION_PROMPT = """Generate a brief, warm introduction for a practice interview.

Candidate Name: {candidate_name}
Skills Detected: {skills}
Total Questions: {question_count}

Write a 2-3 sentence introduction that:
1. Greets them by name
2. Briefly mentions you'll cover topics related to their skills
3. Encourages them to answer naturally

Keep it natural and conversational. Do NOT use bullet points or headers."""

TRANSITION_PROMPT = """Generate a brief transition between interview questions.

Previous Question Score: {prev_score}/10
Previous Answer Quality: {quality_label}
Next Question: "{next_question}"
Next Question Number: {question_number} of {total_questions}
Question Type: {question_type}

Write a 1-2 sentence transition that:
1. Briefly acknowledges the previous answer (encouraging tone regardless of score)
2. Naturally introduces the next question topic

Do NOT repeat the next question itself — just the transition lead-in.
Keep it under 30 words. Be natural, not robotic."""

FOLLOW_UP_PROMPT = """Generate a follow-up question based on the candidate's answer.

Original Question: "{question}"
Candidate's Answer: "{answer}"
Evaluation Summary: Score {score}/10. Gaps: {gaps}

Generate ONE specific follow-up question that:
1. Probes deeper into an area where the answer was weak or vague
2. Is specific enough to guide the candidate toward the missing concept
3. Feels like a natural interviewer would ask it

Write ONLY the follow-up question (one sentence). No preamble."""

CLOSING_PROMPT = """Generate a brief, encouraging closing message for the interview.

Candidate Name: {candidate_name}
Total Questions Answered: {total_questions}
Average Score: {average_score}/10
Top Strengths: {top_strengths}
Main Areas to Improve: {main_gaps}

Write a 2-3 sentence closing that:
1. Thanks them for completing the interview
2. Highlights their strongest area
3. Encourages continued practice on their weaker areas

Be warm, specific, and encouraging. Do NOT mention numerical scores."""


# ══════════════════════════════════════════════════════════════════════════════
# FALLBACK TEMPLATES (when Ollama is unavailable)
# ══════════════════════════════════════════════════════════════════════════════

FALLBACK_INTRODUCTIONS = [
    "Welcome, {name}! Let's begin your practice interview. I'll ask you {count} questions covering your technical skills. Take your time and answer naturally.",
    "Hi {name}! Ready to practice? I have {count} questions prepared for you. Remember, this is a learning exercise — there are no wrong answers, only room to grow.",
    "Hello {name}! Let's get started with your practice interview. We have {count} questions ahead. Feel free to think through your answers before responding.",
]

FALLBACK_TRANSITIONS_HIGH = [
    "Great response! Let's move on.",
    "Well explained! Here's the next one.",
    "Solid answer! Moving forward.",
    "Nice work on that. Let's continue.",
]

FALLBACK_TRANSITIONS_MID = [
    "Thanks for that. Let's keep going.",
    "Got it. Here's the next question.",
    "Noted. Let's move to the next topic.",
    "Alright, let's continue.",
]

FALLBACK_TRANSITIONS_LOW = [
    "Thanks for attempting that. Let's try the next one.",
    "No worries, let's move on to something different.",
    "That's okay — let's continue with the next question.",
]

FALLBACK_CLOSINGS = [
    "Thanks for completing the interview, {name}! You showed solid understanding in several areas. Keep practicing the topics where you felt less confident — you'll get there!",
    "Great job finishing the interview, {name}! Focus on building depth in the areas mentioned in the feedback, and you'll be well-prepared for the real thing.",
]


# ══════════════════════════════════════════════════════════════════════════════
# INTERVIEW CONDUCTOR CLASS
# ══════════════════════════════════════════════════════════════════════════════

class InterviewConductor:
    """
    Uses llama3 to conduct natural, adaptive interviews.

    Generates human-quality transitions, introductions, follow-ups,
    and closing messages that make the interview feel conversational
    rather than mechanical.
    """

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        config: Optional[AgenticConfig] = None,
    ):
        self._client = client or get_ollama_client()
        self._config = config or get_agentic_config()
        self._model = self._config.conversation_model
        self._call_count = 0  # Track for fallback selection variety

    async def generate_introduction(
        self,
        candidate_name: str,
        skills: List[str],
        question_count: int,
    ) -> str:
        """
        Generate a warm, personalized interview introduction.

        Args:
            candidate_name: The candidate's name
            skills: List of detected skills from resume
            question_count: Total number of questions in the interview

        Returns:
            Natural introduction text
        """
        skills_str = ", ".join(skills[:5]) if skills else "various technical topics"

        prompt = INTRODUCTION_PROMPT.format(
            candidate_name=candidate_name,
            skills=skills_str,
            question_count=question_count,
        )

        response = await self._generate(prompt)

        if response:
            logger.info("conductor_introduction_generated", mode="agentic")
            return response

        # Fallback
        idx = hash(candidate_name) % len(FALLBACK_INTRODUCTIONS)
        fallback = FALLBACK_INTRODUCTIONS[idx].format(
            name=candidate_name, count=question_count
        )
        logger.info("conductor_introduction_generated", mode="fallback")
        return fallback

    async def generate_transition(
        self,
        prev_score: float,
        next_question: str,
        question_number: int,
        total_questions: int,
        question_type: str = "technical",
    ) -> str:
        """
        Generate a natural transition between questions.

        Args:
            prev_score: Score from the previous answer (0-10)
            next_question: Text of the next question
            question_number: Number of the next question (1-indexed)
            total_questions: Total question count
            question_type: Type of next question

        Returns:
            Transition text (does NOT include the question itself)
        """
        # Determine quality label
        if prev_score >= 7:
            quality_label = "strong"
        elif prev_score >= 5:
            quality_label = "adequate"
        else:
            quality_label = "needs improvement"

        prompt = TRANSITION_PROMPT.format(
            prev_score=prev_score,
            quality_label=quality_label,
            next_question=next_question[:100],  # Truncate for prompt efficiency
            question_number=question_number,
            total_questions=total_questions,
            question_type=question_type,
        )

        response = await self._generate(prompt, max_tokens=100)

        if response:
            # Ensure the response is concise
            response = response.strip()
            # Trim to first 2 sentences max
            sentences = response.split(". ")
            if len(sentences) > 2:
                response = ". ".join(sentences[:2]) + "."
            return response

        # Fallback
        return self._fallback_transition(prev_score)

    async def generate_follow_up(
        self,
        question: str,
        answer: str,
        evaluation: Dict[str, Any],
    ) -> Optional[str]:
        """
        Generate an intelligent follow-up question based on the evaluation.

        Args:
            question: The original question
            answer: The candidate's answer
            evaluation: The evaluation result dict

        Returns:
            Follow-up question text, or None if the LLM evaluation
            already provided one (passes it through)
        """
        # If the evaluator already generated a follow-up, use it
        existing_follow_up = evaluation.get("follow_up_question")
        if existing_follow_up:
            return existing_follow_up

        # Generate one with the conductor
        score = evaluation.get("score", 5.0)
        gaps = evaluation.get("gaps", [])

        # Don't generate follow-up for strong answers
        if score >= self._config.follow_up_threshold:
            return None

        gaps_str = "; ".join(gaps[:3]) if gaps else "lacks depth"

        prompt = FOLLOW_UP_PROMPT.format(
            question=question[:200],
            answer=answer[:300],
            score=score,
            gaps=gaps_str,
        )

        response = await self._generate(prompt, max_tokens=100)

        if response:
            # Clean up — ensure it's a single question
            response = response.strip()
            if not response.endswith("?"):
                response += "?"
            # Take only first sentence/question
            if "\n" in response:
                response = response.split("\n")[0].strip()
            return response

        return None

    async def generate_closing(
        self,
        candidate_name: str,
        total_questions: int,
        scores: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a personalized closing message summarizing the interview.

        Args:
            candidate_name: The candidate's name
            total_questions: Number of questions answered
            scores: List of score dicts from the interview

        Returns:
            Closing message text
        """
        # Calculate summary stats
        if scores:
            avg_score = sum(s.get("score", 0) for s in scores) / len(scores)
            # Find top strengths across all answers
            all_strengths = []
            all_gaps = []
            for s in scores:
                all_strengths.extend(s.get("strengths", []))
                all_gaps.extend(s.get("gaps", []))
        else:
            avg_score = 0
            all_strengths = []
            all_gaps = []

        top_strengths = ", ".join(all_strengths[:3]) if all_strengths else "answering interview questions"
        main_gaps = ", ".join(all_gaps[:3]) if all_gaps else "providing more depth"

        prompt = CLOSING_PROMPT.format(
            candidate_name=candidate_name,
            total_questions=total_questions,
            average_score=round(avg_score, 1),
            top_strengths=top_strengths,
            main_gaps=main_gaps,
        )

        response = await self._generate(prompt, max_tokens=200)

        if response:
            logger.info("conductor_closing_generated", mode="agentic")
            return response

        # Fallback
        idx = hash(candidate_name) % len(FALLBACK_CLOSINGS)
        fallback = FALLBACK_CLOSINGS[idx].format(name=candidate_name)
        logger.info("conductor_closing_generated", mode="fallback")
        return fallback

    # ── Private Methods ──────────────────────────────────────────────────────

    async def _generate(self, prompt: str, max_tokens: int = 256) -> Optional[str]:
        """
        Internal helper: generate text via llama3 with error handling.

        Returns None if generation fails (caller should use fallback).
        """
        try:
            response = await self._client.generate(
                model=self._model,
                prompt=prompt,
                system=CONDUCTOR_SYSTEM_PROMPT,
                temperature=self._config.chat_temperature,
                max_tokens=max_tokens,
                timeout=self._config.timeout_seconds,
            )
            if response and response.strip():
                self._call_count += 1
                return response.strip()
            return None
        except Exception as e:
            logger.warning("conductor_generate_failed", error=str(e))
            return None

    def _fallback_transition(self, prev_score: float) -> str:
        """Select an appropriate fallback transition based on score."""
        self._call_count += 1
        if prev_score >= 7:
            options = FALLBACK_TRANSITIONS_HIGH
        elif prev_score >= 4:
            options = FALLBACK_TRANSITIONS_MID
        else:
            options = FALLBACK_TRANSITIONS_LOW
        return options[self._call_count % len(options)]


# ══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ══════════════════════════════════════════════════════════════════════════════

_conductor_instance: Optional[InterviewConductor] = None


def get_interview_conductor() -> InterviewConductor:
    """Get or create the global InterviewConductor singleton."""
    global _conductor_instance
    if _conductor_instance is None:
        _conductor_instance = InterviewConductor()
    return _conductor_instance
