"""
Evaluator Agent — Chain-of-thought answer evaluation using deepseek-r1.

The core intelligence of the agentic system. Uses structured reasoning
to evaluate interview answers with far greater nuance than keyword matching.

Agent Loop:
1. OBSERVE: Receive question + candidate answer + expected criteria
2. THINK: Reason about answer quality (chain-of-thought via deepseek-r1)
3. EVALUATE: Score 0-10 with justification
4. DECIDE: Is follow-up needed? What feedback to give?

100% local via Ollama. Falls back gracefully on timeout/error.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional

from .agent_config import get_agentic_config, AgenticConfig
from .ollama_client import get_ollama_client, OllamaClient

# ── Logger Setup ─────────────────────────────────────────────────────────────
try:
    from backend.core.logging import get_logger
    logger = get_logger("backend.agentic.evaluator_agent")
except ImportError:
    import logging
    logger = logging.getLogger("agentic.evaluator_agent")


# ══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════

EVALUATION_SYSTEM_PROMPT = """You are an expert technical interviewer evaluating a candidate's answer in a practice interview setting. Your role is to provide fair, encouraging, but honest evaluation.

Your evaluation should:
- Recognize partial understanding and give appropriate partial credit
- Be encouraging while being specific about gaps
- Suggest concrete improvements
- Consider the difficulty level when scoring

Scoring Guide:
- 9-10: Exceptional — demonstrates deep expertise, covers edge cases, provides examples
- 7-8: Strong — covers main concepts well, good depth, minor gaps
- 5-6: Adequate — covers basics, lacks depth or misses some key points
- 3-4: Weak — shows some awareness but significant gaps
- 1-2: Poor — mostly incorrect or irrelevant
- 0: No meaningful content or completely off-topic"""

EVALUATION_USER_PROMPT = """QUESTION: {question}

EXPECTED KEY CONCEPTS: {keywords}

DIFFICULTY LEVEL: {difficulty}

QUESTION CATEGORY: {category}

CANDIDATE'S ANSWER:
\"\"\"
{answer}
\"\"\"

Evaluate this answer step by step:
1. Identify what concepts the candidate demonstrated understanding of
2. Identify what key concepts are missing or incorrect
3. Assess the depth, clarity, and accuracy of the explanation
4. Consider if the answer matches the {difficulty} difficulty level expected

Provide your evaluation in this EXACT JSON format (no additional text outside the JSON):
{{
  "score": <float 0.0 to 10.0>,
  "strengths": ["specific strength 1", "specific strength 2"],
  "gaps": ["specific missing concept or area to improve 1", "area to improve 2"],
  "feedback": "Brief encouraging feedback with 1-2 specific improvement suggestions",
  "follow_up_question": "A targeted follow-up question to probe deeper understanding (or null if answer was thorough enough)",
  "reasoning": "Your step-by-step reasoning for the score"
}}"""


# ══════════════════════════════════════════════════════════════════════════════
# JSON EXTRACTION UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def extract_json_from_response(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract JSON from LLM response text.

    Handles common LLM output patterns:
    - Pure JSON
    - JSON wrapped in markdown code fences (```json ... ```)
    - JSON with leading/trailing text
    - deepseek-r1's <think>...</think> blocks before JSON

    Args:
        raw_text: Raw text from the LLM

    Returns:
        Parsed dict or None if extraction failed
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    # 1. Remove deepseek-r1 <think>...</think> blocks
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # 2. Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. Try extracting from markdown code fences
    code_fence_patterns = [
        r"```json\s*\n?(.*?)\n?\s*```",
        r"```\s*\n?(.*?)\n?\s*```",
    ]
    for pattern in code_fence_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue

    # 4. Try finding JSON object boundaries
    # Look for the outermost { ... }
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        candidate = text[brace_start:brace_end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 5. Try fixing common JSON issues (trailing commas, single quotes)
    if brace_start != -1 and brace_end > brace_start:
        candidate = text[brace_start:brace_end + 1]
        # Remove trailing commas before } or ]
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
        # Replace single quotes with double quotes (risky but last resort)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    logger.warning(
        "json_extraction_failed",
        text_preview=text[:200],
        text_length=len(text),
    )
    return None


def validate_evaluation_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize the evaluation result from the LLM.

    Ensures all required fields are present with correct types.
    """
    # Score: must be a number 0-10
    score = data.get("score", 5.0)
    if isinstance(score, str):
        try:
            score = float(score)
        except ValueError:
            score = 5.0
    score = max(0.0, min(10.0, float(score)))

    # Strengths: must be a list of strings
    strengths = data.get("strengths", [])
    if isinstance(strengths, str):
        strengths = [strengths]
    strengths = [str(s) for s in strengths if s][:5]  # Cap at 5 items

    # Gaps: must be a list of strings
    gaps = data.get("gaps", [])
    if isinstance(gaps, str):
        gaps = [gaps]
    gaps = [str(g) for g in gaps if g][:5]

    # Feedback: must be a string
    feedback = data.get("feedback", "")
    if not isinstance(feedback, str):
        feedback = str(feedback) if feedback else ""

    # Follow-up question: string or None
    follow_up = data.get("follow_up_question")
    if follow_up and not isinstance(follow_up, str):
        follow_up = str(follow_up)
    if follow_up and follow_up.lower() in ("null", "none", "n/a", ""):
        follow_up = None

    # Reasoning: string
    reasoning = data.get("reasoning", "")
    if not isinstance(reasoning, str):
        reasoning = str(reasoning) if reasoning else ""

    return {
        "score": round(score, 1),
        "strengths": strengths,
        "gaps": gaps,
        "feedback": feedback,
        "follow_up_question": follow_up,
        "reasoning": reasoning,
    }


# ══════════════════════════════════════════════════════════════════════════════
# EVALUATOR AGENT CLASS
# ══════════════════════════════════════════════════════════════════════════════

class EvaluatorAgent:
    """
    Uses deepseek-r1 to evaluate interview answers with chain-of-thought reasoning.

    The agent processes each answer through a structured reasoning pipeline:
    1. OBSERVE: Parse the question, answer, and expected criteria
    2. THINK: Invoke deepseek-r1 with chain-of-thought prompt
    3. EVALUATE: Extract structured JSON evaluation from response
    4. DECIDE: Determine if follow-up is needed based on score + gaps

    Falls back to a basic score estimation if the LLM is unavailable or
    produces unparseable output.
    """

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        config: Optional[AgenticConfig] = None,
    ):
        self._client = client or get_ollama_client()
        self._config = config or get_agentic_config()
        self._model = self._config.evaluation_model

    async def evaluate_answer(
        self,
        question_text: str,
        answer_text: str,
        expected_keywords: List[str],
        difficulty: str = "medium",
        category: str = "technical",
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's answer using chain-of-thought reasoning.

        Args:
            question_text: The interview question that was asked
            answer_text: The candidate's response
            expected_keywords: Keywords/concepts a good answer should cover
            difficulty: easy/medium/hard
            category: technical/behavioral/hr

        Returns:
            Dict with:
                - score: float (0-10)
                - strengths: List[str]
                - gaps: List[str]
                - feedback: str (natural language feedback)
                - follow_up_question: Optional[str]
                - reasoning: str (chain-of-thought reasoning)
                - model_answer_hint: str (derived from gaps)
                - acknowledgment: str (brief score-based acknowledgment)
                - evaluation_mode: str ("agentic" or "fallback")
        """
        start_time = time.time()

        # ── Step 1: OBSERVE — Validate inputs ────────────────────────────
        if not answer_text or not answer_text.strip():
            return self._empty_answer_result()

        if not question_text or not question_text.strip():
            return self._no_question_result(answer_text)

        # ── Step 2: THINK — Build the evaluation prompt ──────────────────
        keywords_str = ", ".join(expected_keywords) if expected_keywords else "general understanding"

        user_prompt = EVALUATION_USER_PROMPT.format(
            question=question_text,
            keywords=keywords_str,
            difficulty=difficulty,
            category=category,
            answer=answer_text,
        )

        # ── Step 3: EVALUATE — Invoke deepseek-r1 ───────────────────────
        raw_response = await self._client.generate(
            model=self._model,
            prompt=user_prompt,
            system=EVALUATION_SYSTEM_PROMPT,
            temperature=self._config.eval_temperature,
            max_tokens=self._config.max_tokens_eval,
            timeout=self._config.timeout_seconds,
        )

        elapsed = time.time() - start_time

        # ── Step 4: PARSE — Extract structured evaluation ────────────────
        if raw_response is None:
            logger.warning(
                "evaluator_agent_no_response",
                elapsed_s=round(elapsed, 2),
                model=self._model,
            )
            return self._fallback_result(question_text, answer_text, expected_keywords, difficulty)

        parsed = extract_json_from_response(raw_response)

        if parsed is None:
            logger.warning(
                "evaluator_agent_parse_failed",
                elapsed_s=round(elapsed, 2),
                response_preview=raw_response[:300],
            )
            return self._fallback_result(question_text, answer_text, expected_keywords, difficulty)

        # ── Step 5: VALIDATE — Ensure correct structure ──────────────────
        result = validate_evaluation_result(parsed)

        # ── Step 6: DECIDE — Add metadata and format response ────────────
        result["model_answer_hint"] = self._generate_model_hint(result["gaps"], expected_keywords)
        result["acknowledgment"] = self._generate_acknowledgment(result["score"])
        result["evaluation_mode"] = "agentic"
        result["elapsed_seconds"] = round(elapsed, 2)

        if self._config.log_reasoning and result.get("reasoning"):
            logger.info(
                "evaluator_reasoning",
                score=result["score"],
                reasoning_preview=result["reasoning"][:200],
            )

        logger.info(
            "evaluator_agent_success",
            score=result["score"],
            strengths_count=len(result["strengths"]),
            gaps_count=len(result["gaps"]),
            has_follow_up=result["follow_up_question"] is not None,
            elapsed_s=round(elapsed, 2),
        )

        return result

    # ── Fallback Methods ─────────────────────────────────────────────────────

    def _fallback_result(
        self,
        question_text: str,
        answer_text: str,
        expected_keywords: List[str],
        difficulty: str,
    ) -> Dict[str, Any]:
        """
        Generate a basic evaluation when LLM is unavailable.

        Uses simple heuristics:
        - Word count vs expected for difficulty
        - Keyword presence check
        - Basic structure detection
        """
        words = answer_text.split()
        word_count = len(words)
        answer_lower = answer_text.lower()

        # Keyword matching
        keywords_found = []
        keywords_missed = []
        for kw in expected_keywords:
            if kw.lower() in answer_lower:
                keywords_found.append(kw)
            else:
                keywords_missed.append(kw)

        keyword_ratio = len(keywords_found) / max(len(expected_keywords), 1)

        # Length scoring
        min_words = {"easy": 20, "medium": 40, "hard": 60}.get(difficulty, 40)
        ideal_words = {"easy": 80, "medium": 150, "hard": 250}.get(difficulty, 150)
        length_ratio = min(1.0, word_count / ideal_words)
        length_penalty = 0.0 if word_count >= min_words else 0.3

        # Basic score estimation
        score = (keyword_ratio * 6.0 + length_ratio * 3.0 + (1.0 - length_penalty)) 
        score = max(0.0, min(10.0, score))

        strengths = []
        gaps = []

        if keywords_found:
            strengths.append(f"Mentioned key concepts: {', '.join(keywords_found[:3])}")
        if word_count >= ideal_words:
            strengths.append("Provided a detailed response")
        elif word_count >= min_words:
            strengths.append("Answered with reasonable detail")

        if keywords_missed:
            gaps.append(f"Consider covering: {', '.join(keywords_missed[:3])}")
        if word_count < min_words:
            gaps.append(f"Answer is too brief ({word_count} words). Aim for at least {min_words} words.")

        return {
            "score": round(score, 1),
            "strengths": strengths or ["Provided an answer"],
            "gaps": gaps or ["Try to elaborate further"],
            "feedback": f"Your answer covered {len(keywords_found)}/{len(expected_keywords)} expected concepts.",
            "follow_up_question": None,
            "reasoning": "Fallback evaluation (LLM unavailable) — scored by keyword matching and length.",
            "model_answer_hint": self._generate_model_hint(gaps, expected_keywords),
            "acknowledgment": self._generate_acknowledgment(score),
            "evaluation_mode": "fallback",
            "elapsed_seconds": 0.0,
        }

    def _empty_answer_result(self) -> Dict[str, Any]:
        """Result for empty/blank answers."""
        return {
            "score": 0.0,
            "strengths": [],
            "gaps": ["No answer provided"],
            "feedback": "Please provide an answer to the question. Even a partial answer is better than none.",
            "follow_up_question": None,
            "reasoning": "Empty answer received.",
            "model_answer_hint": "",
            "acknowledgment": "⚠️ **No answer detected.** Please provide a response.",
            "evaluation_mode": "agentic",
            "elapsed_seconds": 0.0,
        }

    def _no_question_result(self, answer_text: str) -> Dict[str, Any]:
        """Result when question text is missing (shouldn't happen in practice)."""
        return {
            "score": 5.0,
            "strengths": ["Provided a response"],
            "gaps": ["Unable to evaluate without question context"],
            "feedback": "Response received but evaluation context is incomplete.",
            "follow_up_question": None,
            "reasoning": "No question text provided — cannot evaluate relevance.",
            "model_answer_hint": "",
            "acknowledgment": "📝 Response noted.",
            "evaluation_mode": "agentic",
            "elapsed_seconds": 0.0,
        }

    # ── Helper Methods ───────────────────────────────────────────────────────

    def _generate_model_hint(self, gaps: List[str], expected_keywords: List[str]) -> str:
        """Generate a model answer hint from gaps and expected keywords."""
        if not gaps and not expected_keywords:
            return ""

        hints = []
        if expected_keywords:
            hints.append(f"Key concepts to cover: {', '.join(expected_keywords[:5])}")
        if gaps:
            hints.append(f"Areas to strengthen: {'; '.join(gaps[:3])}")

        return " | ".join(hints)

    def _generate_acknowledgment(self, score: float) -> str:
        """Generate a score-based acknowledgment message."""
        if score >= 9.0:
            return "✅ **Outstanding answer!** You demonstrated deep expertise and clear communication."
        elif score >= 7.0:
            return "✅ **Excellent answer!** You demonstrated strong understanding."
        elif score >= 6.0:
            return "👍 **Good answer.** You covered the key points well."
        elif score >= 4.0:
            return "💡 **Decent attempt.** There's room to deepen your explanation."
        elif score >= 2.0:
            return "⚠️ **Needs improvement.** Try to be more specific with examples and key concepts."
        else:
            return "⚠️ **Very brief or off-topic.** Review the topic and try a more detailed response."


# ══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ══════════════════════════════════════════════════════════════════════════════

_evaluator_instance: Optional[EvaluatorAgent] = None


def get_evaluator_agent() -> EvaluatorAgent:
    """Get or create the global EvaluatorAgent singleton."""
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = EvaluatorAgent()
    return _evaluator_instance
