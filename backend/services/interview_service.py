"""
Interview Service - Manages the mock interview conversation.

Features:
- Conversational chain using LangChain ConversationBufferMemory
- Asks one question at a time
- Scores answers and provides feedback
- Tracks progress through the question list
"""

from typing import Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

from utils.config import settings
from utils.session_store import session_store
from backend.models.schemas import ChatResponse, FeedbackDetail


# ------------------------------------------------
# PROMPT: Interview Host / Moderator
# ------------------------------------------------
INTERVIEW_HOST_TEMPLATE = """
You are a professional and encouraging AI interview coach named "Alex".
You are conducting a structured mock interview.

Your responsibilities:
1. You are currently evaluating the candidate's answer to an interview question
2. Score their answer from 0-10 (10 = perfect, 0 = no relevant answer)
3. Give specific, actionable feedback
4. Be encouraging but honest

Interview History (for context):
{history}

Current Input from Candidate: {input}

Respond in this EXACT JSON format (no markdown, no code blocks, just pure JSON):
{{
  "score": <number 0-10>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>"],
  "model_answer_hint": "<brief hint about what a great answer looks like>",
  "acknowledgment": "<1-2 sentence encouraging response to the candidate>"
}}
"""

# ------------------------------------------------
# PROMPT: Final Score Summary
# ------------------------------------------------
SUMMARY_PROMPT = """
You are an AI interview coach. Based on this complete interview session, provide a final assessment.

Interview History:
{history}

Candidate Name: {candidate_name}
Total Questions Asked: {total_questions}
Average Score: {average_score}/10

Generate a final interview summary with:
1. Overall performance (2-3 sentences)
2. Top strengths (2-3 bullet points)
3. Key areas for improvement (2-3 bullet points)
4. Hiring recommendation: "Strong Hire" (8+), "Consider" (5-7), or "No Hire" (below 5)

Keep it professional and constructive.
"""


def get_or_create_conversation_chain(session_id: str) -> ConversationChain:
    """
    Get existing conversation chain or create a new one for this session.
    Uses ConversationBufferMemory to maintain chat history.
    
    Args:
        session_id: The unique session ID
        
    Returns:
        LangChain ConversationChain object
    """
    session = session_store.get_session(session_id)
    
    # Return existing chain if already created
    if session.get("conversation_chain"):
        return session["conversation_chain"]
    
    # Create memory object - stores ALL messages in the conversation
    memory = ConversationBufferMemory(
        memory_key="history",
        return_messages=False,
        human_prefix="Candidate",
        ai_prefix="Interviewer"
    )
    
    # Create the prompt template for the conversational chain
    prompt = PromptTemplate(
        input_variables=["history", "input"],
        template=INTERVIEW_HOST_TEMPLATE
    )
    
    # Initialize the LLM
    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        temperature=0.3,  # Lower temperature for consistent scoring
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": settings.OPENROUTER_SITE_URL,
            "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
        }
    )
    
    # Create conversational chain with memory
    chain = ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt,
        verbose=False,
    )
    
    # Store chain in session
    session_store.set_conversation_chain(session_id, chain)
    
    return chain


def parse_feedback_response(raw_response: str) -> Optional[FeedbackDetail]:
    """
    Parse the AI's JSON feedback response into a FeedbackDetail object.
    
    Args:
        raw_response: Raw JSON string from the AI
        
    Returns:
        FeedbackDetail object or None if parsing fails
    """
    import json
    import re
    
    try:
        # Clean up the response (remove any markdown if present)
        cleaned = raw_response.strip()
        # Remove markdown code blocks if present
        cleaned = re.sub(r"```json\s*", "", cleaned)
        cleaned = re.sub(r"```\s*", "", cleaned)
        
        data = json.loads(cleaned)
        
        return FeedbackDetail(
            score=max(0, min(10, int(data.get("score", 5)))),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", []),
            model_answer_hint=data.get("model_answer_hint", ""),
        ), data.get("acknowledgment", "Thank you for your answer.")
        
    except (json.JSONDecodeError, ValueError, KeyError):
        # Fallback if JSON parsing fails
        return FeedbackDetail(
            score=5,
            strengths=["You attempted to answer the question"],
            improvements=["Please provide more specific details"],
            model_answer_hint="A good answer includes specific examples from your experience.",
        ), "Thank you for your answer. Let's continue."


def process_interview_message(session_id: str, user_message: str) -> ChatResponse:
    """
    Process a candidate's answer and return the next question + feedback.
    
    Flow:
    1. Get current question number from session
    2. Score the candidate's answer using LangChain conversation chain
    3. Store feedback
    4. Move to next question or end interview
    
    Args:
        session_id: The unique session ID
        user_message: The candidate's answer text
        
    Returns:
        ChatResponse with feedback and next question (or completion message)
    """
    session = session_store.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found.")
    
    questions = session.get("questions", [])
    if not questions:
        raise ValueError("No questions found. Please generate questions first.")
    
    current_q_index = session.get("current_question_index", 0)
    total_questions = len(questions)
    
    # Get or create the conversation chain (with memory)
    chain = get_or_create_conversation_chain(session_id)
    
    # Get the current question being answered
    current_question = questions[current_q_index] if current_q_index < total_questions else None
    
    # Build context message for the AI evaluator
    if current_question:
        context_message = (
            f"The candidate was asked: '{current_question.question}'\n"
            f"Their answer: '{user_message}'"
        )
    else:
        context_message = user_message
    
    # Run through the conversation chain to get feedback
    raw_response = chain.predict(input=context_message)
    
    # Parse the feedback
    feedback_result = parse_feedback_response(raw_response)
    if isinstance(feedback_result, tuple):
        feedback, acknowledgment = feedback_result
    else:
        feedback = feedback_result
        acknowledgment = "Thank you for your answer."
    
    # Save this answer's feedback
    session_store.add_answer_feedback(session_id, {
        "question": current_question.question if current_question else "",
        "question_type": current_question.type if current_question else "unknown",
        "user_answer": user_message,
        "score": feedback.score,
        "feedback": feedback,
    })
    
    # Move to next question
    next_q_index = current_q_index + 1
    session_store.set_current_question_index(session_id, next_q_index)
    
    # Check if interview is complete
    if next_q_index >= total_questions:
        # Interview is done!
        completion_message = (
            f"{acknowledgment}\n\n"
            "🎉 **Interview Complete!** You've answered all the questions. "
            "Click **'View Final Summary'** to see your complete performance report."
        )
        return ChatResponse(
            success=True,
            session_id=session_id,
            message=completion_message,
            feedback=feedback,
            is_interview_complete=True,
            current_question_number=total_questions,
            total_questions=total_questions,
        )
    
    # Get the next question to ask
    next_question = questions[next_q_index]
    question_label = f"**Question {next_q_index + 1} of {total_questions}** [{next_question.type.value.upper()}]"
    
    next_message = (
        f"{acknowledgment}\n\n"
        f"---\n"
        f"{question_label}\n\n"
        f"❓ {next_question.question}"
    )
    
    return ChatResponse(
        success=True,
        session_id=session_id,
        message=next_message,
        feedback=feedback,
        is_interview_complete=False,
        current_question_number=next_q_index + 1,
        total_questions=total_questions,
    )


def start_interview(session_id: str) -> ChatResponse:
    """
    Start the interview by asking the first question.
    
    Args:
        session_id: The unique session ID
        
    Returns:
        ChatResponse with the first question
    """
    session = session_store.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found.")
    
    questions = session.get("questions", [])
    if not questions:
        raise ValueError("No questions generated. Please generate questions first.")
    
    # Reset interview state
    session_store.set_current_question_index(session_id, 0)
    session_store.clear_answer_feedback(session_id)
    
    first_question = questions[0]
    candidate_name = session.get("candidate_name", "Candidate")
    
    intro_message = (
        f"👋 Hello **{candidate_name}**! Welcome to your mock interview.\n\n"
        f"I'll ask you **{len(questions)} questions** — {sum(1 for q in questions if q.type.value == 'technical')} technical "
        f"and {sum(1 for q in questions if q.type.value == 'hr')} HR questions.\n\n"
        f"Take your time and answer as clearly and specifically as possible. Ready? Let's begin!\n\n"
        f"---\n"
        f"**Question 1 of {len(questions)}** [TECHNICAL]\n\n"
        f"❓ {first_question.question}"
    )
    
    return ChatResponse(
        success=True,
        session_id=session_id,
        message=intro_message,
        feedback=None,
        is_interview_complete=False,
        current_question_number=1,
        total_questions=len(questions),
    )


def generate_final_summary(session_id: str) -> dict:
    """
    Generate a comprehensive final interview summary.
    
    Args:
        session_id: The unique session ID
        
    Returns:
        Dict with complete summary data
    """
    session = session_store.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found.")
    
    candidate_name = session.get("candidate_name", "Candidate")
    answers_feedback = session.get("answers_feedback", [])
    questions = session.get("questions", [])
    
    if not answers_feedback:
        return {
            "success": False,
            "message": "No answers recorded yet."
        }
    
    # Calculate average score
    scores = [af["score"] for af in answers_feedback]
    average_score = sum(scores) / len(scores) if scores else 0
    
    # Build score breakdown
    score_breakdown = []
    for i, af in enumerate(answers_feedback):
        score_breakdown.append({
            "question_number": i + 1,
            "question": af["question"],
            "question_type": af.get("question_type", "unknown"),
            "score": af["score"],
            "score_display": f"{af['score']}/10",
            "strengths": af["feedback"].strengths if af.get("feedback") else [],
            "improvements": af["feedback"].improvements if af.get("feedback") else [],
        })
    
    # Determine recommendation
    if average_score >= 7.0:
        recommendation = "✅ Pass - Hr will be soon to contact you 👍"
        rec_color = "green"
    else:
        recommendation = "❌ Fail - Better luck next time"
        rec_color = "red"
    
    # Generate AI summary using conversation history
    chain = session.get("conversation_chain")
    overall_feedback = ""
    
    if chain and chain.memory:
        history_text = chain.memory.buffer if hasattr(chain.memory, 'buffer') else ""
        
        llm = ChatOpenAI(
            model=settings.OPENROUTER_MODEL,
            temperature=0.4,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
            }
        )
        
        summary_prompt = SUMMARY_PROMPT.format(
            history=history_text[:3000],  # Limit context length
            candidate_name=candidate_name,
            total_questions=len(questions),
            average_score=round(average_score, 1),
        )
        
        try:
            overall_feedback = llm.predict(summary_prompt)
        except Exception:
            overall_feedback = (
                f"Overall, {candidate_name} demonstrated "
                f"{'strong' if average_score >= 7 else 'moderate' if average_score >= 5 else 'developing'} "
                f"performance with an average score of {round(average_score, 1)}/10."
            )
    
    return {
        "success": True,
        "session_id": session_id,
        "candidate_name": candidate_name,
        "total_questions": len(questions),
        "answered_questions": len(answers_feedback),
        "average_score": round(average_score, 1),
        "overall_feedback": overall_feedback,
        "score_breakdown": score_breakdown,
        "recommendation": recommendation,
        "recommendation_color": rec_color,
    }
