"""
Verbal Interview Routes — Real-time conversational interview powered by Ollama.

Simulates a real-world phone interview:
- AI speaks naturally, reacts to answers, probes deeper
- Asks HR + resume-based technical questions
- Evaluates each answer in real-time with improvement suggestions
- Provides detailed final review with per-question feedback

Flow:
  1. POST /verbal/start   → Start session, get greeting + first question
  2. POST /verbal/respond → Send candidate answer → get reaction + next question + per-answer feedback
  3. POST /verbal/end     → End session → get full evaluation with improvement suggestions
"""

import uuid
import re as re_module
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.session import get_db
from backend.models.interview import InterviewSession
from backend.core.security import get_current_active_user
from backend.models.user import User
from backend.core.logging import get_logger

logger = get_logger("backend.routes.verbal")

router = APIRouter(
    prefix="/verbal",
    tags=["Verbal Interview"],
    dependencies=[Depends(get_current_active_user)],
)

# ── Active session store ───────────────────────────────────────────────────
_verbal_sessions: Dict[str, dict] = {}


# ── Interviewer System Prompt (Natural Conversational Style) ───────────────
INTERVIEWER_SYSTEM_PROMPT = """You are a senior HR interviewer conducting a real phone interview. You speak naturally like a human — warm, professional, conversational.

CONVERSATION RULES:
1. ALWAYS react to the candidate's answer FIRST (1 sentence) before asking the next question
   - "That's a great point about [something they mentioned]..."
   - "Interesting, so you were handling [their detail]..."
   - "I appreciate you sharing that..."
2. Then ask your next question naturally, as a follow-up or transition
3. Keep your total response to 2-3 sentences MAX (this is spoken aloud)
4. NEVER list multiple questions — ask exactly ONE
5. If the answer was vague/short, probe deeper: "Could you tell me more about...?"
6. Use natural speech patterns — contractions, casual transitions

INTERVIEW TOPICS (cover these across 6-8 questions):
- Self introduction
- Recent role & responsibilities (use resume details)
- A specific project they worked on (ask about challenges, decisions, outcomes)
- Technical skills (ask them to explain a concept or tool they use)
- Problem-solving approach
- Working with teams / handling disagreements
- Career growth / what they want next

ENDING: After 7-8 exchanges, say EXACTLY: "That wraps up our interview for today. Thank you so much for your time — it was great speaking with you."

{resume_context}
"""

# ── Evaluation Prompt ──────────────────────────────────────────────────────
EVALUATE_ANSWER_PROMPT = """Evaluate this interview answer. Be specific and constructive.

Question: {question}
Answer: {answer}

Score each (1-10) and give ONE specific improvement suggestion:
- Relevance: Does it answer the question? (score)
- Clarity: Is it well-structured and easy to follow? (score)
- Depth: Does it include specifics, examples, numbers? (score)
- Communication: Professional language, confidence? (score)

Format your response EXACTLY like this:
RELEVANCE: [score]
CLARITY: [score]
DEPTH: [score]
COMMUNICATION: [score]
SUGGESTION: [one specific actionable improvement tip]
STRENGTH: [one thing they did well]"""

# ── Fallback questions for when Ollama is down ─────────────────────────────
FALLBACK_QUESTIONS = [
    "Hi there! Thanks for taking the time to chat today. Let's start easy — can you give me a quick overview of who you are and what you do?",
    "That's great. So tell me about your current or most recent role — what does a typical day look like for you?",
    "Interesting. Can you walk me through a project you're proud of? What was the challenge and how did you tackle it?",
    "Nice. When you hit a technical problem you haven't seen before, what's your go-to approach?",
    "Makes sense. How about working with others — can you tell me about a time you had a disagreement with a teammate and how it played out?",
    "I appreciate that. Looking ahead, where do you see yourself in the next couple of years? What kind of work excites you?",
    "Last one — if I asked your previous manager to describe your biggest strength, what would they say?",
    "That wraps up our interview for today. Thank you so much for your time — it was great speaking with you.",
]


# ── Request/Response Schemas ───────────────────────────────────────────────

class StartRequest(BaseModel):
    session_id: Optional[str] = None
    resume_text: Optional[str] = None


class RespondRequest(BaseModel):
    verbal_session_id: str
    candidate_message: str


class EndRequest(BaseModel):
    verbal_session_id: str


# ── Route Handlers ─────────────────────────────────────────────────────────

@router.post("/start")
async def start_verbal_interview(
    request: StartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Start a new verbal interview. Returns greeting + first question."""
    resume_text = request.resume_text or ""

    # Fetch resume from existing session if available
    if request.session_id:
        try:
            sid = uuid.UUID(request.session_id)
            result = await db.execute(
                select(InterviewSession).where(InterviewSession.id == sid)
            )
            session = result.scalar_one_or_none()
            if session and session.resume_text:
                resume_text = session.resume_text
        except Exception as e:
            logger.warning("verbal_resume_fetch_failed", error=str(e))

    # Build system prompt with resume context
    resume_context = ""
    if resume_text:
        truncated = resume_text[:2500]
        resume_context = f"\nCANDIDATE'S RESUME:\n{truncated}\n\nUse this to ask SPECIFIC questions about their projects, skills, and experience mentioned above."

    system_prompt = INTERVIEWER_SYSTEM_PROMPT.format(resume_context=resume_context)

    # Get first message from Ollama
    first_message = await _get_ollama_response(
        system_prompt=system_prompt,
        messages=[{
            "role": "user",
            "content": "Begin the interview. Greet the candidate warmly and naturally, then ask your first question about their background."
        }],
    )

    if not first_message:
        first_message = FALLBACK_QUESTIONS[0]

    # Create session state
    verbal_id = str(uuid.uuid4())
    _verbal_sessions[verbal_id] = {
        "system_prompt": system_prompt,
        "messages": [
            {"role": "assistant", "content": first_message},
        ],
        "exchanges": [],  # Store Q&A pairs with evaluations
        "question_count": 1,
        "resume_text": resume_text,
        "user_id": str(current_user.id),
        "session_id": request.session_id,
        "using_ollama": first_message != FALLBACK_QUESTIONS[0],
        "fallback_index": 1,
        "current_question": first_message,
    }

    logger.info("verbal_started", verbal_id=verbal_id, has_resume=bool(resume_text))

    return {
        "success": True,
        "verbal_session_id": verbal_id,
        "message": first_message,
        "question_number": 1,
        "is_complete": False,
    }


@router.post("/respond")
async def respond_to_verbal(request: RespondRequest):
    """
    Process candidate's spoken answer. Returns:
    - Interviewer's natural reaction + next question
    - Real-time feedback on the answer (scores + suggestion)
    """
    session = _verbal_sessions.get(request.verbal_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found. Start a new one.")

    candidate_msg = request.candidate_message.strip()
    if not candidate_msg:
        return {
            "success": True,
            "message": "Sorry, I didn't catch that. Could you say that again?",
            "question_number": session["question_count"],
            "is_complete": False,
            "feedback": None,
        }

    # ── Evaluate this answer (async, in parallel with getting next question)
    current_question = session["current_question"]
    feedback = await _evaluate_single_answer(current_question, candidate_msg)

    # Store the exchange
    session["exchanges"].append({
        "question_number": session["question_count"],
        "question": current_question,
        "answer": candidate_msg,
        "feedback": feedback,
    })

    # ── Add to conversation history
    session["messages"].append({"role": "user", "content": candidate_msg})

    # ── Get next interviewer message
    is_ending = session["question_count"] >= 7

    if session["using_ollama"]:
        extra = ""
        if is_ending:
            extra = "\n\nThis is the FINAL question. After reacting to their answer, say exactly: 'That wraps up our interview for today. Thank you so much for your time — it was great speaking with you.'"

        next_message = await _get_ollama_response(
            system_prompt=session["system_prompt"] + extra,
            messages=session["messages"],
        )

        if not next_message:
            session["using_ollama"] = False
            idx = min(session["fallback_index"], len(FALLBACK_QUESTIONS) - 1)
            next_message = FALLBACK_QUESTIONS[idx]
            session["fallback_index"] += 1
    else:
        idx = min(session["fallback_index"], len(FALLBACK_QUESTIONS) - 1)
        next_message = FALLBACK_QUESTIONS[idx]
        session["fallback_index"] += 1

    session["messages"].append({"role": "assistant", "content": next_message})
    session["question_count"] += 1
    session["current_question"] = next_message

    # Check completion
    is_complete = (
        "wraps up our interview" in next_message.lower() or
        "concludes our interview" in next_message.lower() or
        "that's all for today" in next_message.lower() or
        session["question_count"] > 9
    )

    return {
        "success": True,
        "message": next_message,
        "question_number": session["question_count"],
        "is_complete": is_complete,
        "feedback": feedback,  # Real-time per-answer feedback
    }


@router.post("/end")
async def end_verbal_interview(request: EndRequest):
    """
    End interview and generate comprehensive review with:
    - Per-question scores + improvement suggestions
    - Overall scores across all dimensions
    - Top strengths & areas to improve
    - Specific actionable tips
    """
    try:
        session = _verbal_sessions.get(request.verbal_session_id)
        if not session:
            # Return a minimal review instead of 404 so frontend doesn't crash
            return {
                "success": True,
                "evaluation": {
                    "overall_score": 0,
                    "rating": "Session expired — please try again",
                    "scores": {"relevance": 0, "clarity": 0, "depth": 0, "communication": 0, "fluency": 0},
                    "stats": {"total_questions": 0, "total_answers": 0, "total_words": 0, "avg_words_per_answer": 0, "filler_words_count": 0},
                    "question_reviews": [],
                    "overall_suggestion": "Your session expired. Please start a new interview.",
                    "top_strengths": [],
                    "areas_to_improve": ["Start a new session and complete the full interview for detailed feedback."],
                },
            }

        exchanges = session["exchanges"]
        candidate_answers = [ex["answer"] for ex in exchanges]

        # ── Calculate overall scores from per-question feedback
        all_feedback = [ex["feedback"] for ex in exchanges if ex["feedback"]]

        if all_feedback:
            avg_fn = lambda key: round(sum(f.get(key, 5) for f in all_feedback) / len(all_feedback), 1)
            overall_relevance = avg_fn("relevance")
            overall_clarity = avg_fn("clarity")
            overall_depth = avg_fn("depth")
            overall_communication = avg_fn("communication")
            overall_score = round((overall_relevance + overall_clarity + overall_depth + overall_communication) / 4, 1)
        else:
            overall_relevance = overall_clarity = overall_depth = overall_communication = 5.0
            overall_score = 5.0

        # ── Fluency analysis
        total_words = sum(len(a.split()) for a in candidate_answers)
        avg_words = round(total_words / max(len(candidate_answers), 1), 1)
        
        fillers = ["um", "uh", "like", "you know", "basically", "actually", "sort of", "kind of"]
        total_fillers = sum(
            sum(a.lower().count(f) for f in fillers)
            for a in candidate_answers
        )
        fluency_score = round(max(2, min(10, 10 - (total_fillers * 0.8) - (1 if avg_words < 20 else 0))), 1)

        # ── Get AI-generated overall suggestion
        overall_suggestion = await _get_overall_suggestion(exchanges, session["system_prompt"])

        # ── Build per-question review
        question_reviews = []
        for ex in exchanges:
            fb = ex.get("feedback") or {}
            question_reviews.append({
                "question_number": ex["question_number"],
                "question": ex["question"][:200],
                "answer_preview": ex["answer"][:300],
                "word_count": len(ex["answer"].split()),
                "scores": {
                    "relevance": fb.get("relevance", 5),
                    "clarity": fb.get("clarity", 5),
                    "depth": fb.get("depth", 5),
                    "communication": fb.get("communication", 5),
                    "average": round(
                        (fb.get("relevance", 5) + fb.get("clarity", 5) + fb.get("depth", 5) + fb.get("communication", 5)) / 4, 1
                    ),
                },
                "suggestion": fb.get("suggestion", "Try to include specific examples with numbers or outcomes."),
                "strength": fb.get("strength", "You answered the question."),
            })

        # ── Rating
        rating = (
            "Excellent — Ready for real interviews" if overall_score >= 8 else
            "Good — Minor improvements needed" if overall_score >= 6.5 else
            "Average — Practice more with specific examples" if overall_score >= 5 else
            "Needs Improvement — Focus on structure and depth"
        )

        # Cleanup
        if request.verbal_session_id in _verbal_sessions:
            del _verbal_sessions[request.verbal_session_id]

        return {
            "success": True,
            "evaluation": {
                "overall_score": overall_score,
                "rating": rating,
                "scores": {
                    "relevance": overall_relevance,
                    "clarity": overall_clarity,
                    "depth": overall_depth,
                    "communication": overall_communication,
                    "fluency": fluency_score,
                },
                "stats": {
                    "total_questions": len(exchanges),
                    "total_answers": len(candidate_answers),
                    "total_words": total_words,
                    "avg_words_per_answer": avg_words,
                    "filler_words_count": total_fillers,
                },
                "question_reviews": question_reviews,
                "overall_suggestion": overall_suggestion,
                "top_strengths": _extract_top_strengths(question_reviews),
                "areas_to_improve": _extract_improvements(question_reviews),
            },
        }

    except Exception as e:
        logger.error("verbal_end_failed", error=str(e))
        import traceback
        logger.error("verbal_end_traceback", tb=traceback.format_exc())
        # Return a valid response even on error so frontend doesn't crash
        return {
            "success": True,
            "evaluation": {
                "overall_score": 5.0,
                "rating": "Review partially generated",
                "scores": {"relevance": 5, "clarity": 5, "depth": 5, "communication": 5, "fluency": 5},
                "stats": {"total_questions": 0, "total_answers": 0, "total_words": 0, "avg_words_per_answer": 0, "filler_words_count": 0},
                "question_reviews": [],
                "overall_suggestion": f"An error occurred during review generation: {str(e)}. Your interview responses were recorded but detailed analysis could not be completed.",
                "top_strengths": ["You completed the interview."],
                "areas_to_improve": ["Try again for a complete evaluation."],
            },
        }


# ══════════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ══════════════════════════════════════════════════════════════════════════════

async def _get_ollama_response(system_prompt: str, messages: List[Dict[str, str]]) -> Optional[str]:
    """Get natural conversation response from Ollama."""
    try:
        from backend.agentic.ollama_client import get_ollama_client
        from backend.agentic.agent_config import get_agentic_config
        client = get_ollama_client()

        if not await client.is_available():
            return None

        config = get_agentic_config()
        response = await client.chat(
            model=config.conversation_model,
            messages=messages,
            system=system_prompt,
            temperature=0.7,
            max_tokens=150,  # Short for natural speech
            timeout=25.0,
        )

        if response and len(response) > 10:
            return response.strip()
        return None
    except Exception as e:
        logger.error("verbal_ollama_error", error=str(e))
        return None


async def _evaluate_single_answer(question: str, answer: str) -> dict:
    """Evaluate a single Q&A pair. Returns scores + suggestion."""
    # Try Ollama evaluation
    try:
        from backend.agentic.ollama_client import get_ollama_client
        from backend.agentic.agent_config import get_agentic_config
        client = get_ollama_client()

        if await client.is_available():
            config = get_agentic_config()
            prompt = EVALUATE_ANSWER_PROMPT.format(question=question[:200], answer=answer[:500])

            response = await client.generate(
                model=config.evaluation_model,
                prompt=prompt,
                temperature=0.2,
                max_tokens=200,
                timeout=15.0,
            )

            if response:
                return _parse_evaluation(response)
    except Exception as e:
        logger.warning("verbal_eval_failed", error=str(e))

    # Fallback: rule-based evaluation
    return _rule_based_evaluate(question, answer)


def _parse_evaluation(response: str) -> dict:
    """Parse LLM evaluation response into structured scores."""
    result = {
        "relevance": 5, "clarity": 5, "depth": 5, "communication": 5,
        "suggestion": "Add more specific examples.", "strength": "Good attempt.",
    }

    for line in response.split("\n"):
        line = line.strip()
        if line.startswith("RELEVANCE:"):
            result["relevance"] = _extract_score(line)
        elif line.startswith("CLARITY:"):
            result["clarity"] = _extract_score(line)
        elif line.startswith("DEPTH:"):
            result["depth"] = _extract_score(line)
        elif line.startswith("COMMUNICATION:"):
            result["communication"] = _extract_score(line)
        elif line.startswith("SUGGESTION:"):
            result["suggestion"] = line.replace("SUGGESTION:", "").strip()
        elif line.startswith("STRENGTH:"):
            result["strength"] = line.replace("STRENGTH:", "").strip()

    return result


def _extract_score(line: str) -> int:
    """Extract numeric score from a line like 'RELEVANCE: 7'."""
    match = re_module.search(r'(\d+)', line)
    if match:
        return max(1, min(10, int(match.group(1))))
    return 5


def _rule_based_evaluate(question: str, answer: str) -> dict:
    """Fallback rule-based evaluation when Ollama is unavailable."""
    words = answer.split()
    wc = len(words)
    
    # Relevance: check if answer contains words from the question
    q_words = set(question.lower().split())
    a_words = set(answer.lower().split())
    overlap = len(q_words & a_words)
    relevance = min(10, 4 + overlap)

    # Depth: based on word count and specifics
    depth = min(10, 3 + (wc // 10))
    numbers = len(re_module.findall(r'\d+', answer))
    if numbers > 0:
        depth = min(10, depth + 2)

    # Clarity: sentence structure
    sentences = [s for s in answer.split('.') if len(s.strip()) > 5]
    clarity = min(10, 4 + len(sentences))

    # Communication: professional words
    pro_words = ["implemented", "managed", "developed", "collaborated", "optimized", "delivered", "led", "designed"]
    pro_count = sum(1 for w in pro_words if w in answer.lower())
    communication = min(10, 4 + pro_count * 2 + (1 if wc > 30 else 0))

    # Suggestion
    suggestions = []
    if wc < 20:
        suggestions.append("Elaborate more — aim for 40-60 words with specific examples.")
    if numbers == 0:
        suggestions.append("Include metrics or numbers (e.g., 'reduced load time by 40%').")
    if pro_count == 0:
        suggestions.append("Use professional action verbs: implemented, optimized, collaborated.")
    if len(sentences) < 2:
        suggestions.append("Structure with multiple sentences: context → action → result.")
    
    suggestion = suggestions[0] if suggestions else "Good answer! Try adding one more specific detail."
    
    # Strength
    strengths = []
    if wc > 30:
        strengths.append("Detailed response with good length.")
    if pro_count > 0:
        strengths.append("Strong professional vocabulary.")
    if numbers > 0:
        strengths.append("Included quantifiable results.")
    strength = strengths[0] if strengths else "You addressed the question directly."

    return {
        "relevance": relevance,
        "clarity": clarity,
        "depth": depth,
        "communication": communication,
        "suggestion": suggestion,
        "strength": strength,
    }


async def _get_overall_suggestion(exchanges: list, system_prompt: str) -> str:
    """Generate an overall improvement suggestion using Ollama."""
    try:
        from backend.agentic.ollama_client import get_ollama_client
        from backend.agentic.agent_config import get_agentic_config
        client = get_ollama_client()

        if not await client.is_available():
            return _fallback_overall_suggestion(exchanges)

        config = get_agentic_config()
        
        # Build summary of the interview
        summary = "\n".join([
            f"Q{ex['question_number']}: {ex['question'][:80]}\nA: {ex['answer'][:150]}"
            for ex in exchanges[:6]
        ])

        prompt = f"""Based on this interview, give 3 specific improvement tips for the candidate. Be constructive and actionable. Keep each tip to 1 sentence.

Interview Summary:
{summary}

Format:
1. [tip]
2. [tip]
3. [tip]"""

        response = await client.generate(
            model=config.conversation_model,
            prompt=prompt,
            temperature=0.3,
            max_tokens=200,
            timeout=15.0,
        )

        if response and len(response) > 20:
            return response.strip()
    except Exception as e:
        logger.warning("verbal_overall_suggestion_failed", error=str(e))

    return _fallback_overall_suggestion(exchanges)


def _fallback_overall_suggestion(exchanges: list) -> str:
    """Rule-based overall suggestion."""
    total_words = sum(len(ex["answer"].split()) for ex in exchanges)
    avg = total_words / max(len(exchanges), 1)
    
    tips = []
    if avg < 25:
        tips.append("1. Expand your answers — aim for 40-60 words using the STAR method (Situation, Task, Action, Result).")
    else:
        tips.append("1. Great answer length! Now focus on adding one quantifiable result per answer (numbers, percentages, timelines).")
    
    tips.append("2. Practice smooth transitions: start with a brief context, then your main point, then the outcome.")
    tips.append("3. Record yourself answering questions and listen back — this helps identify filler words and pacing issues.")
    
    return "\n".join(tips)


def _extract_top_strengths(reviews: list) -> List[str]:
    """Extract unique strengths from per-question reviews."""
    strengths = list(set(r["strength"] for r in reviews if r.get("strength")))
    return strengths[:3] if strengths else ["You completed the full interview."]


def _extract_improvements(reviews: list) -> List[str]:
    """Extract top improvement areas from per-question reviews."""
    suggestions = list(set(r["suggestion"] for r in reviews if r.get("suggestion")))
    return suggestions[:3] if suggestions else ["Practice with more mock interviews."]
