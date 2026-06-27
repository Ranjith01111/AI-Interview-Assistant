"""
Feedback Generator — Converts raw evaluation scores into human-readable feedback.

Generates encouraging, specific, and actionable feedback for interview practice.
"""

from typing import List, Dict, Optional
from .answer_evaluator import EvaluationResult
from .question_bank import Question


# Score tier thresholds
EXCELLENT_THRESHOLD = 8.5
GOOD_THRESHOLD = 7.0
ADEQUATE_THRESHOLD = 5.0
NEEDS_WORK_THRESHOLD = 3.0

# Encouragement messages by score tier
TIER_MESSAGES = {
    "excellent": [
        "Outstanding answer! You demonstrated deep understanding.",
        "Excellent response! This shows strong expertise in this area.",
        "Impressive answer! You covered the key concepts thoroughly.",
        "Great job! This level of detail would impress interviewers.",
        "Superb! Your answer shows both breadth and depth of knowledge.",
    ],
    "good": [
        "Good answer! You covered the main concepts well.",
        "Solid response with good technical understanding.",
        "Well done! A few more details could make this even stronger.",
        "Good foundation — adding examples would elevate this further.",
        "Nice work! You hit most of the important points.",
    ],
    "adequate": [
        "Decent start, but there's room for more depth.",
        "You've got the basics — let's work on adding more detail.",
        "A reasonable answer that could be strengthened with specifics.",
        "Good effort! Focus on the concepts mentioned below to improve.",
        "You're on the right track — let's fill in some gaps.",
    ],
    "needs_work": [
        "This topic needs more study. Focus on the key concepts below.",
        "Let's work on building your knowledge in this area.",
        "The answer needs more substance. Review the model answer for guidance.",
        "Don't worry — this is a learning opportunity. Study the concepts below.",
        "Keep practicing! Focus on the specific areas mentioned below.",
    ],
    "minimal": [
        "Try to provide a more complete answer next time.",
        "This needs significant improvement. Review the model answer carefully.",
        "Let's focus on building foundational knowledge in this area.",
        "Study the key concepts below and try again with more detail.",
        "Don't give up — review the hints and try to explain each concept.",
    ],
}

# Transition words for natural-sounding feedback
TRANSITIONS = {
    "strengths": ["Specifically, ", "In particular, ", "Notably, ", "Impressively, "],
    "improvements": ["To strengthen your answer, ", "For improvement, ", "Next time, ", "Consider: "],
}


class FeedbackGenerator:
    """Generates human-readable feedback from evaluation results."""

    def __init__(self, encouraging: bool = True):
        """
        Args:
            encouraging: If True, always include positive framing and encouragement
        """
        self.encouraging = encouraging

    def generate_feedback(
        self,
        result: EvaluationResult,
        question: Optional[Question] = None,
    ) -> Dict[str, str]:
        """
        Generate comprehensive feedback from an evaluation result.

        Returns dict with keys:
            - summary: One-line score summary
            - encouragement: Motivational message
            - strengths: What was done well
            - improvements: Specific areas to improve
            - model_answer_hint: Reference answer hint
            - score_breakdown: Detailed score explanation
        """
        tier = self._get_tier(result.score)

        feedback = {
            "summary": self._generate_summary(result.score, tier),
            "encouragement": self._generate_encouragement(tier, result),
            "strengths": self._format_strengths(result),
            "improvements": self._format_improvements(result),
            "model_answer_hint": self._format_model_hint(result.model_answer_hint),
            "score_breakdown": self._format_score_breakdown(result),
        }

        return feedback

    def generate_short_feedback(self, result: EvaluationResult) -> str:
        """Generate a single concise feedback string."""
        tier = self._get_tier(result.score)
        parts = []

        # Score
        parts.append(f"Score: {result.score}/10")

        # Quick summary
        if tier in ("excellent", "good"):
            if result.keywords_found:
                parts.append(f"✓ Strong points: {', '.join(result.keywords_found[:3])}")
        if result.keywords_missed and tier not in ("excellent",):
            parts.append(f"→ Could mention: {', '.join(result.keywords_missed[:3])}")

        return " | ".join(parts)

    def generate_interview_summary(
        self,
        results: List[EvaluationResult],
        questions: Optional[List[Question]] = None,
    ) -> Dict[str, str]:
        """
        Generate overall interview performance summary.

        Args:
            results: List of all evaluation results from the interview
            questions: Optional list of corresponding questions

        Returns:
            Dict with overall feedback sections
        """
        if not results:
            return {
                "overall_score": "N/A",
                "performance_level": "No answers evaluated",
                "summary": "No responses were recorded for this interview.",
                "strengths_summary": "",
                "improvement_areas": "",
                "recommendation": "",
            }

        scores = [r.score for r in results]
        avg_score = sum(scores) / len(scores)
        tier = self._get_tier(avg_score)

        # Aggregate strengths and weaknesses
        all_found = []
        all_missed = []
        for r in results:
            all_found.extend(r.keywords_found)
            all_missed.extend(r.keywords_missed)

        # Find most common strengths/gaps
        found_counts = self._count_items(all_found)
        missed_counts = self._count_items(all_missed)

        # Category performance (if questions provided)
        category_scores = {}
        if questions:
            for q, r in zip(questions, results):
                cat = q.category
                if cat not in category_scores:
                    category_scores[cat] = []
                category_scores[cat].append(r.score)

        summary = {
            "overall_score": f"{avg_score:.1f}/10",
            "performance_level": self._tier_to_level(tier),
            "summary": self._generate_overall_summary(avg_score, tier, len(results)),
            "strengths_summary": self._generate_strengths_summary(
                found_counts, scores, category_scores
            ),
            "improvement_areas": self._generate_improvement_summary(
                missed_counts, scores, category_scores
            ),
            "recommendation": self._generate_recommendation(avg_score, tier),
            "score_distribution": self._format_score_distribution(scores),
        }

        if category_scores:
            summary["category_breakdown"] = self._format_category_breakdown(
                category_scores
            )

        return summary

    # ─── Private Methods ──────────────────────────────────────────────────

    def _get_tier(self, score: float) -> str:
        """Determine score tier."""
        if score >= EXCELLENT_THRESHOLD:
            return "excellent"
        elif score >= GOOD_THRESHOLD:
            return "good"
        elif score >= ADEQUATE_THRESHOLD:
            return "adequate"
        elif score >= NEEDS_WORK_THRESHOLD:
            return "needs_work"
        else:
            return "minimal"

    def _tier_to_level(self, tier: str) -> str:
        """Convert tier to human-readable level."""
        levels = {
            "excellent": "Excellent — Interview Ready",
            "good": "Good — Strong Performance",
            "adequate": "Adequate — Some Areas Need Work",
            "needs_work": "Developing — Significant Study Needed",
            "minimal": "Beginning — Foundational Gaps to Address",
        }
        return levels.get(tier, "Unknown")

    def _generate_summary(self, score: float, tier: str) -> str:
        """Generate one-line score summary."""
        emoji_map = {
            "excellent": "🌟",
            "good": "✅",
            "adequate": "📝",
            "needs_work": "📚",
            "minimal": "🔄",
        }
        emoji = emoji_map.get(tier, "")
        return f"{emoji} Score: {score}/10 — {self._tier_to_level(tier)}"

    def _generate_encouragement(
        self, tier: str, result: EvaluationResult
    ) -> str:
        """Generate encouraging message based on tier."""
        import random
        messages = TIER_MESSAGES.get(tier, TIER_MESSAGES["adequate"])
        message = random.choice(messages)

        # Add specific positive note if possible
        if result.keywords_found and tier in ("excellent", "good"):
            top_keyword = result.keywords_found[0]
            message += f" Your mention of '{top_keyword}' shows solid understanding."

        return message

    def _format_strengths(self, result: EvaluationResult) -> str:
        """Format strengths section."""
        if not result.strengths:
            if result.score >= GOOD_THRESHOLD:
                return "Your answer demonstrates good overall understanding of the topic."
            return ""

        lines = ["What you did well:"]
        for i, strength in enumerate(result.strengths, 1):
            lines.append(f"  {i}. {strength}")

        return "\n".join(lines)

    def _format_improvements(self, result: EvaluationResult) -> str:
        """Format improvements section."""
        if not result.improvements:
            if result.score >= EXCELLENT_THRESHOLD:
                return "No major gaps identified — excellent coverage!"
            return ""

        lines = ["Areas to improve:"]
        for i, improvement in enumerate(result.improvements, 1):
            lines.append(f"  {i}. {improvement}")

        return "\n".join(lines)

    def _format_model_hint(self, hint: str) -> str:
        """Format model answer hint."""
        if not hint:
            return ""
        return f"💡 Key points for a strong answer:\n  {hint}"

    def _format_score_breakdown(self, result: EvaluationResult) -> str:
        """Format detailed score breakdown."""
        lines = [
            "Score breakdown:",
            f"  • Keyword coverage: {result.keyword_score}/10 "
            f"({len(result.keywords_found)} of {len(result.keywords_found) + len(result.keywords_missed)} key terms)",
            f"  • Answer depth: {result.length_score}/10",
            f"  • Relevance: {result.relevance_score}/10",
        ]
        return "\n".join(lines)

    def _generate_overall_summary(
        self, avg_score: float, tier: str, num_questions: int
    ) -> str:
        """Generate overall interview summary paragraph."""
        if tier == "excellent":
            return (
                f"Outstanding performance across {num_questions} questions! "
                f"Your average score of {avg_score:.1f}/10 indicates strong readiness "
                f"for technical interviews. You demonstrate deep knowledge and can "
                f"articulate complex concepts clearly."
            )
        elif tier == "good":
            return (
                f"Good performance on {num_questions} questions with an average of "
                f"{avg_score:.1f}/10. You show solid understanding of core concepts. "
                f"Focus on the improvement areas below to move from good to great."
            )
        elif tier == "adequate":
            return (
                f"You answered {num_questions} questions with an average of "
                f"{avg_score:.1f}/10. You have a foundation to build on, but several "
                f"areas need deepening. Focus your study on the gaps identified below."
            )
        else:
            return (
                f"Your performance on {num_questions} questions (average {avg_score:.1f}/10) "
                f"suggests more preparation is needed. Don't be discouraged — use the "
                f"feedback below to guide focused study. Practice explaining concepts "
                f"out loud to build fluency."
            )

    def _generate_strengths_summary(
        self,
        found_counts: Dict[str, int],
        scores: List[float],
        category_scores: Dict[str, List[float]],
    ) -> str:
        """Generate strengths summary for the full interview."""
        lines = []

        # Strong answers
        strong = sum(1 for s in scores if s >= 7.0)
        if strong > 0:
            lines.append(f"• {strong} of {len(scores)} answers were strong (7+/10)")

        # Top categories
        if category_scores:
            best_cats = sorted(
                category_scores.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
                reverse=True,
            )[:3]
            for cat, cat_scores in best_cats:
                avg = sum(cat_scores) / len(cat_scores)
                if avg >= 6.0:
                    lines.append(f"• Strong in {cat.replace('_', ' ').title()}: {avg:.1f}/10")

        # Most-demonstrated concepts
        if found_counts:
            top_concepts = sorted(found_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            concept_list = ", ".join(c[0] for c in top_concepts)
            lines.append(f"• Frequently demonstrated concepts: {concept_list}")

        return "\n".join(lines) if lines else "Keep practicing to build strengths!"

    def _generate_improvement_summary(
        self,
        missed_counts: Dict[str, int],
        scores: List[float],
        category_scores: Dict[str, List[float]],
    ) -> str:
        """Generate improvement areas summary."""
        lines = []

        # Weak answers
        weak = sum(1 for s in scores if s < 4.0)
        if weak > 0:
            lines.append(f"• {weak} of {len(scores)} answers need significant improvement")

        # Weakest categories
        if category_scores:
            worst_cats = sorted(
                category_scores.items(),
                key=lambda x: sum(x[1]) / len(x[1]),
            )[:2]
            for cat, cat_scores in worst_cats:
                avg = sum(cat_scores) / len(cat_scores)
                if avg < 6.0:
                    lines.append(f"• Focus on {cat.replace('_', ' ').title()}: {avg:.1f}/10")

        # Most-missed concepts
        if missed_counts:
            top_missed = sorted(missed_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            missed_list = ", ".join(m[0] for m in top_missed)
            lines.append(f"• Key concepts to study: {missed_list}")

        return "\n".join(lines) if lines else "Minor improvements needed — keep up the good work!"

    def _generate_recommendation(self, avg_score: float, tier: str) -> str:
        """Generate actionable recommendation."""
        if tier == "excellent":
            return (
                "🎯 Recommendation: You're interview-ready! Practice mock interviews "
                "to refine delivery and timing. Focus on system design scenarios for "
                "senior-level discussions."
            )
        elif tier == "good":
            return (
                "🎯 Recommendation: Practice 2-3 weak areas daily. Focus on explaining "
                "concepts with specific examples and trade-offs. Try teaching topics "
                "to deepen understanding."
            )
        elif tier == "adequate":
            return (
                "🎯 Recommendation: Dedicate focused study time to gaps above. "
                "Write notes on each missed concept. Practice answering out loud "
                "with a timer (aim for 2-3 minutes per answer)."
            )
        else:
            return (
                "🎯 Recommendation: Start with fundamentals. Read documentation "
                "and tutorials for each missed concept. Practice explaining basic "
                "concepts in your own words before tackling harder questions."
            )

    def _format_score_distribution(self, scores: List[float]) -> str:
        """Format score distribution as a simple text histogram."""
        bins = {"9-10 ⭐": 0, "7-8 ✅": 0, "5-6 📝": 0, "3-4 📚": 0, "0-2 🔄": 0}
        for s in scores:
            if s >= 9:
                bins["9-10 ⭐"] += 1
            elif s >= 7:
                bins["7-8 ✅"] += 1
            elif s >= 5:
                bins["5-6 📝"] += 1
            elif s >= 3:
                bins["3-4 📚"] += 1
            else:
                bins["0-2 🔄"] += 1

        lines = ["Score distribution:"]
        for label, count in bins.items():
            bar = "█" * count + "░" * (len(scores) - count)
            lines.append(f"  {label}: {bar} ({count})")

        return "\n".join(lines)

    def _format_category_breakdown(
        self, category_scores: Dict[str, List[float]]
    ) -> str:
        """Format per-category score breakdown."""
        lines = ["Performance by category:"]
        sorted_cats = sorted(
            category_scores.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True,
        )
        for cat, scores in sorted_cats:
            avg = sum(scores) / len(scores)
            count = len(scores)
            emoji = "🟢" if avg >= 7 else "🟡" if avg >= 5 else "🔴"
            cat_display = cat.replace("_", " ").title()
            lines.append(f"  {emoji} {cat_display}: {avg:.1f}/10 ({count} questions)")

        return "\n".join(lines)

    def _count_items(self, items: List[str]) -> Dict[str, int]:
        """Count occurrences of items."""
        counts: Dict[str, int] = {}
        for item in items:
            counts[item] = counts.get(item, 0) + 1
        return counts

# ── Convenience functions (matches service imports) ────────────────────
_feedback_instance = None

def generate_feedback(result_dict, question_text: str = None) -> dict:
    """Convenience function to generate feedback."""
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = FeedbackGenerator()
        
    from .answer_evaluator import EvaluationResult
    if isinstance(result_dict, dict):
        # Only pass fields that exist in EvaluationResult
        valid_keys = EvaluationResult.__dataclass_fields__.keys()
        filtered_dict = {k: v for k, v in result_dict.items() if k in valid_keys}
        result = EvaluationResult(**filtered_dict)
    else:
        result = result_dict
        
    return _feedback_instance.generate_feedback(result=result)

def generate_final_summary(results: list = None, scores: list = None, candidate_name: str = "Candidate", total_questions: int = 0) -> dict:
    """Convenience function to generate overall summary."""
    global _feedback_instance
    if _feedback_instance is None:
        _feedback_instance = FeedbackGenerator()

    # Accept both 'results' and 'scores' as the data list
    data = results if results is not None else (scores if scores is not None else [])

    # If data contains score dicts from the agent (not EvaluationResult), handle them
    if data and isinstance(data[0], dict) and "score" in data[0] and "question" in data[0]:
        # These are agent-format score entries, build a summary directly
        total = len(data)
        avg_score = sum(d.get("score", 0) for d in data) / max(total, 1)
        
        strengths_all = []
        gaps_all = []
        for d in data:
            strengths_all.extend(d.get("strengths", []))
            gaps_all.extend(d.get("gaps", d.get("improvements", [])))
        
        # Deduplicate
        top_strengths = list(dict.fromkeys(strengths_all))[:5]
        top_gaps = list(dict.fromkeys(gaps_all))[:5]
        
        # Generate recommendation
        if avg_score >= 8:
            recommendation = "Strong Hire"
            overall = f"Excellent performance by {candidate_name}! Strong command of concepts with clear communication."
        elif avg_score >= 6:
            recommendation = "Hire"
            overall = f"{candidate_name} demonstrated solid knowledge with some areas for growth."
        elif avg_score >= 4:
            recommendation = "Maybe"
            overall = f"{candidate_name} shows potential but needs improvement in several areas."
        else:
            recommendation = "No Hire"
            overall = f"{candidate_name} needs significant preparation before proceeding."
        
        return {
            "candidate_name": candidate_name,
            "total_questions": total_questions or total,
            "questions_answered": total,
            "average_score": round(avg_score, 1),
            "recommendation": recommendation,
            "overall_feedback": overall,
            "strengths": top_strengths,
            "improvements": top_gaps,
            "score_breakdown": [
                {
                    "question": d.get("question", f"Q{i+1}"), 
                    "score": d.get("score", 0),
                    "answer": d.get("answer", ""),
                    "feedback": d.get("acknowledgment", "") or ", ".join(d.get("gaps", d.get("improvements", [])))
                }
                for i, d in enumerate(data)
            ],
        }

    from .answer_evaluator import EvaluationResult
    eval_results = []
    for r in data:
        if isinstance(r, dict):
            valid_keys = EvaluationResult.__dataclass_fields__.keys()
            filtered_dict = {k: v for k, v in r.items() if k in valid_keys}
            eval_results.append(EvaluationResult(**filtered_dict))
        else:
            eval_results.append(r)
            
    return _feedback_instance.generate_interview_summary(results=eval_results)

