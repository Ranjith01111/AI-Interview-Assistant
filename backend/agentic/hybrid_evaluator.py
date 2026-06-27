"""
Hybrid Evaluator — Smart fallback system combining LLM + Semantic + Rule-based evaluation.

Strategy:
1. If Ollama is available → Use agentic evaluation (deepseek-r1 + semantic matching)
2. If Ollama is unavailable → Fall back to rule-based (answer_evaluator.py)
3. When both are available → Blend scores: 70% LLM + 30% semantic similarity

This module is the single entry point for all answer evaluation in the system.
It maintains backward compatibility with the original evaluate_answer() interface.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from .agent_config import get_agentic_config, AgenticConfig
from .ollama_client import get_ollama_client, OllamaClient
from .evaluator_agent import get_evaluator_agent, EvaluatorAgent
from .semantic_matcher import get_semantic_matcher, SemanticMatcher

# ── Logger Setup ─────────────────────────────────────────────────────────────
try:
    from backend.core.logging import get_logger
    logger = get_logger("backend.agentic.hybrid_evaluator")
except ImportError:
    import logging
    logger = logging.getLogger("agentic.hybrid_evaluator")


# ══════════════════════════════════════════════════════════════════════════════
# RULE-BASED FALLBACK (imports existing evaluator)
# ══════════════════════════════════════════════════════════════════════════════

def _rule_based_evaluate(
    question_text: str,
    answer_text: str,
    expected_keywords: List[str],
    difficulty: str = "medium",
) -> Dict[str, Any]:
    """
    Call the original rule-based answer evaluator.

    Wraps the synchronous evaluate_answer() from nlp_engine.
    Returns result in the standard agentic format.
    """
    try:
        from backend.nlp_engine.answer_evaluator import evaluate_answer as _rule_evaluate
        result = _rule_evaluate(
            question_text=question_text,
            answer_text=answer_text,
            expected_keywords=expected_keywords,
            difficulty=difficulty,
        )
        # Augment with agentic-format fields
        result.setdefault("feedback", "")
        result.setdefault("follow_up_question", None)
        result.setdefault("reasoning", "Rule-based evaluation (keyword + TF-IDF + structure)")
        result.setdefault("evaluation_mode", "rule_based")
        result.setdefault("elapsed_seconds", 0.0)
        return result
    except ImportError as e:
        logger.error("rule_based_import_failed", error=str(e))
        # Absolute fallback — should never happen in normal operation
        return {
            "score": 5.0,
            "strengths": ["Answer provided"],
            "gaps": ["Unable to evaluate fully"],
            "feedback": "Evaluation system temporarily unavailable.",
            "follow_up_question": None,
            "reasoning": "Import error — returned default score",
            "model_answer_hint": "",
            "acknowledgment": "📝 Response recorded.",
            "evaluation_mode": "error_fallback",
            "elapsed_seconds": 0.0,
        }


# ══════════════════════════════════════════════════════════════════════════════
# HYBRID EVALUATOR CLASS
# ══════════════════════════════════════════════════════════════════════════════

class HybridEvaluator:
    """
    Intelligent evaluation system that combines multiple scoring strategies.

    Priority:
    1. Agentic (LLM chain-of-thought) — deepest understanding
    2. Semantic (embedding similarity) — concept coverage without LLM reasoning
    3. Rule-based (keyword + TF-IDF) — fast, deterministic fallback

    When Ollama is available, uses both #1 and #2 and blends scores.
    When Ollama is unavailable, falls back to #3 gracefully.
    """

    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        evaluator: Optional[EvaluatorAgent] = None,
        matcher: Optional[SemanticMatcher] = None,
        config: Optional[AgenticConfig] = None,
    ):
        self._client = client or get_ollama_client()
        self._evaluator = evaluator or get_evaluator_agent()
        self._matcher = matcher or get_semantic_matcher()
        self._config = config or get_agentic_config()

        # Stats tracking
        self._total_evaluations = 0
        self._agentic_evaluations = 0
        self._fallback_evaluations = 0

    @property
    def stats(self) -> Dict[str, int]:
        """Return evaluation statistics."""
        return {
            "total": self._total_evaluations,
            "agentic": self._agentic_evaluations,
            "fallback": self._fallback_evaluations,
        }

    async def evaluate(
        self,
        question_text: str,
        answer_text: str,
        expected_keywords: List[str],
        difficulty: str = "medium",
        category: str = "technical",
        model_answer_hint: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluate a candidate's answer using the best available method.

        This is the main entry point — replaces the old evaluate_answer() function.

        Args:
            question_text: The interview question
            answer_text: The candidate's answer
            expected_keywords: Expected keywords/concepts
            difficulty: easy/medium/hard
            category: technical/behavioral/hr
            model_answer_hint: Optional ideal answer for comparison

        Returns:
            Dict with standard evaluation format:
                - score: int (0-10)
                - strengths: List[str]
                - gaps: List[str]
                - feedback: str
                - follow_up_question: Optional[str]
                - model_answer_hint: str
                - acknowledgment: str
                - evaluation_mode: str ("agentic", "hybrid", "rule_based", "fallback")
                - reasoning: str
                - keywords_found: List[str] (backward compat)
                - keywords_missed: List[str] (backward compat)
        """
        self._total_evaluations += 1
        start_time = time.time()

        # ── Check Ollama availability ────────────────────────────────────
        ollama_available = await self._client.is_available()

        if not ollama_available:
            # Fall back to rule-based evaluation
            logger.info(
                "hybrid_evaluator_fallback",
                reason="ollama_unavailable",
                eval_number=self._total_evaluations,
            )
            self._fallback_evaluations += 1
            result = _rule_based_evaluate(
                question_text=question_text,
                answer_text=answer_text,
                expected_keywords=expected_keywords,
                difficulty=difficulty,
            )
            result["elapsed_seconds"] = round(time.time() - start_time, 2)
            return result

        # ── Ollama is available — use agentic evaluation ─────────────────
        self._agentic_evaluations += 1

        try:
            # Run LLM evaluation and semantic matching concurrently
            llm_task = self._evaluator.evaluate_answer(
                question_text=question_text,
                answer_text=answer_text,
                expected_keywords=expected_keywords,
                difficulty=difficulty,
                category=category,
            )

            semantic_task = self._matcher.compute_overall_semantic_score(
                question=question_text,
                answer=answer_text,
                expected_concepts=expected_keywords,
                model_answer_hint=model_answer_hint,
            )

            llm_result, semantic_result = await asyncio.gather(
                llm_task,
                semantic_task,
                return_exceptions=True,
            )

            # Handle exceptions from concurrent tasks
            if isinstance(llm_result, Exception):
                logger.error("hybrid_llm_task_failed", error=str(llm_result))
                llm_result = None

            if isinstance(semantic_result, Exception):
                logger.error("hybrid_semantic_task_failed", error=str(semantic_result))
                semantic_result = None

            # ── Blend results ────────────────────────────────────────────
            final_result = self._blend_results(
                llm_result=llm_result,
                semantic_result=semantic_result,
                question_text=question_text,
                answer_text=answer_text,
                expected_keywords=expected_keywords,
                difficulty=difficulty,
            )

            final_result["elapsed_seconds"] = round(time.time() - start_time, 2)

            logger.info(
                "hybrid_evaluator_success",
                mode=final_result.get("evaluation_mode", "unknown"),
                score=final_result["score"],
                elapsed_s=final_result["elapsed_seconds"],
            )

            return final_result

        except Exception as e:
            # Last resort fallback on any unexpected error
            logger.error(
                "hybrid_evaluator_unexpected_error",
                error=str(e),
                fallback="rule_based",
            )
            self._fallback_evaluations += 1
            result = _rule_based_evaluate(
                question_text=question_text,
                answer_text=answer_text,
                expected_keywords=expected_keywords,
                difficulty=difficulty,
            )
            result["elapsed_seconds"] = round(time.time() - start_time, 2)
            result["evaluation_mode"] = "error_fallback"
            return result

    def _blend_results(
        self,
        llm_result: Optional[Dict[str, Any]],
        semantic_result: Optional[Dict[str, float]],
        question_text: str,
        answer_text: str,
        expected_keywords: List[str],
        difficulty: str,
    ) -> Dict[str, Any]:
        """
        Blend LLM evaluation with semantic similarity scores.

        Blending strategy:
        - If both available: 70% LLM + 30% semantic
        - If only LLM: 100% LLM
        - If only semantic: scale to 0-10 and use as primary
        - If neither: fall back to rule-based
        """
        # Case 1: Both available — optimal blending
        if llm_result and semantic_result and llm_result.get("evaluation_mode") == "agentic":
            llm_score = llm_result["score"]
            semantic_score = semantic_result.get("overall_score", 5.0)

            # Blend scores
            blended_score = (
                self._config.blend_llm_weight * llm_score +
                self._config.blend_semantic_weight * semantic_score
            )
            blended_score = round(max(0.0, min(10.0, blended_score)), 1)

            # Use LLM result as base, adjust score
            result = dict(llm_result)
            result["score"] = int(round(blended_score))
            result["evaluation_mode"] = "hybrid"
            result["semantic_score"] = round(semantic_score, 2)
            result["llm_raw_score"] = llm_score

            # Add concept coverage details
            if "concept_details" in semantic_result:
                result["concept_coverage"] = semantic_result["concept_details"]

            # Re-generate acknowledgment with blended score
            result["acknowledgment"] = self._generate_acknowledgment(blended_score)

            return result

        # Case 2: Only LLM available
        if llm_result and llm_result.get("evaluation_mode") == "agentic":
            result = dict(llm_result)
            result["score"] = int(round(result["score"]))
            return result

        # Case 3: Only semantic available (LLM failed/timed out)
        if semantic_result:
            semantic_score = semantic_result.get("overall_score", 5.0)
            # Fall back to rule-based but enhance with semantic data
            result = _rule_based_evaluate(
                question_text=question_text,
                answer_text=answer_text,
                expected_keywords=expected_keywords,
                difficulty=difficulty,
            )
            # Blend rule-based with semantic
            rule_score = result["score"]
            enhanced_score = 0.5 * float(rule_score) + 0.5 * semantic_score
            result["score"] = int(round(max(0.0, min(10.0, enhanced_score))))
            result["evaluation_mode"] = "semantic_enhanced"
            result["semantic_score"] = round(semantic_score, 2)
            result["acknowledgment"] = self._generate_acknowledgment(enhanced_score)
            return result

        # Case 4: Nothing worked — pure rule-based
        result = _rule_based_evaluate(
            question_text=question_text,
            answer_text=answer_text,
            expected_keywords=expected_keywords,
            difficulty=difficulty,
        )
        return result

    def _generate_acknowledgment(self, score: float) -> str:
        """Generate acknowledgment based on score."""
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
# BACKWARD-COMPATIBLE WRAPPER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

_hybrid_instance: Optional[HybridEvaluator] = None


def get_hybrid_evaluator() -> HybridEvaluator:
    """Get or create the global HybridEvaluator singleton."""
    global _hybrid_instance
    if _hybrid_instance is None:
        _hybrid_instance = HybridEvaluator()
    return _hybrid_instance


async def evaluate_answer_agentic(
    question_text: str,
    answer_text: str,
    expected_keywords: list = None,
    difficulty: str = "medium",
    category: str = "technical",
) -> Dict[str, Any]:
    """
    Async wrapper for agentic evaluation.

    BACKWARD COMPATIBLE with the original evaluate_answer() return format:
    - score: int (0-10)
    - strengths: List[str]
    - gaps: List[str]
    - model_answer_hint: str
    - acknowledgment: str
    - keywords_found: List[str]
    - keywords_missed: List[str]

    Plus additional fields:
    - feedback: str
    - follow_up_question: Optional[str]
    - reasoning: str
    - evaluation_mode: str
    """
    evaluator = get_hybrid_evaluator()
    result = await evaluator.evaluate(
        question_text=question_text,
        answer_text=answer_text,
        expected_keywords=expected_keywords or [],
        difficulty=difficulty,
        category=category,
    )

    # Ensure backward-compatible fields exist
    result.setdefault("keywords_found", [])
    result.setdefault("keywords_missed", [])
    result.setdefault("model_answer_hint", "")
    result.setdefault("acknowledgment", "📝 Response noted.")
    result.setdefault("strengths", [])
    result.setdefault("gaps", [])

    return result
