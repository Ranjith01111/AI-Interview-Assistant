"""
Answer Evaluator — Scores interview answers using keyword matching and TF-IDF similarity.

No external APIs. No LLMs. Uses:
- Keyword overlap scoring against expected_keywords
- Answer length/quality heuristics
- TF-IDF cosine similarity (scikit-learn) for semantic relevance
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

from .question_bank import Question


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single answer."""
    score: float  # 0.0 - 10.0
    keywords_found: List[str] = field(default_factory=list)
    keywords_missed: List[str] = field(default_factory=list)
    keyword_score: float = 0.0  # 0.0 - 10.0
    length_score: float = 0.0  # 0.0 - 10.0
    relevance_score: float = 0.0  # 0.0 - 10.0
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    model_answer_hint: str = ""
    confidence: float = 0.0  # How confident the evaluator is (0-1)


# Scoring weights
KEYWORD_WEIGHT = 0.50  # 50% keyword matching
LENGTH_WEIGHT = 0.20  # 20% answer length/quality
RELEVANCE_WEIGHT = 0.30  # 30% relevance/similarity

# Length thresholds (in words)
MIN_WORDS_EASY = 20
MIN_WORDS_MEDIUM = 40
MIN_WORDS_HARD = 60
IDEAL_WORDS_EASY = 80
IDEAL_WORDS_MEDIUM = 150
IDEAL_WORDS_HARD = 250
MAX_WORDS_PENALTY = 500  # Penalty for being too verbose

# Filler/low-quality patterns
FILLER_PATTERNS = [
    r'\b(um+|uh+|like|basically|actually|literally|you know|i mean|so yeah)\b',
    r'\b(i think maybe|i\'m not sure|i don\'t know|no idea)\b',
    r'\b(etc|and so on|and stuff|things like that)\b',
]

# Quality indicator patterns
QUALITY_INDICATORS = [
    r'\b(for example|such as|specifically|in particular)\b',
    r'\b(because|therefore|consequently|as a result|this means)\b',
    r'\b(first|second|third|additionally|furthermore|moreover)\b',
    r'\b(trade-off|advantage|disadvantage|comparison|versus)\b',
    r'\b(in production|in practice|real-world|at scale)\b',
]


class AnswerEvaluator:
    """Evaluates interview answers using keyword matching and TF-IDF similarity."""

    def __init__(self):
        if HAS_SKLEARN:
            self._vectorizer = TfidfVectorizer(
                stop_words='english',
                max_features=5000,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
        else:
            self._vectorizer = None

    def evaluate(
        self,
        answer: str,
        question: Question,
        strict: bool = False,
    ) -> EvaluationResult:
        """
        Evaluate an answer against a question's expected criteria.

        Args:
            answer: The candidate's answer text
            question: The Question object with expected_keywords
            strict: If True, use stricter scoring thresholds

        Returns:
            EvaluationResult with detailed breakdown
        """
        if not answer or not answer.strip():
            return EvaluationResult(
                score=0.0,
                keywords_missed=question.expected_keywords.copy(),
                improvements=["No answer was provided. Try to give a detailed response."],
                model_answer_hint=question.model_answer_hint,
                confidence=1.0,
            )

        # Normalize the answer
        answer_clean = self._normalize_text(answer)
        answer_lower = answer_clean.lower()

        # 1. Keyword scoring (50% weight)
        keyword_result = self._score_keywords(answer_lower, question.expected_keywords)

        # 2. Length/quality scoring (20% weight)
        length_result = self._score_length(answer_clean, question.difficulty)

        # 3. Relevance scoring (30% weight)
        relevance_result = self._score_relevance(
            answer_clean, question.text, question.model_answer_hint
        )

        # Calculate weighted final score
        raw_score = (
            keyword_result["score"] * KEYWORD_WEIGHT +
            length_result["score"] * LENGTH_WEIGHT +
            relevance_result["score"] * RELEVANCE_WEIGHT
        )

        # Apply quality bonuses/penalties
        quality_modifier = self._calculate_quality_modifier(answer_clean)
        final_score = max(0.0, min(10.0, raw_score + quality_modifier))

        # Round to 1 decimal
        final_score = round(final_score, 1)

        # Generate strengths and improvements
        strengths = self._identify_strengths(
            keyword_result, length_result, relevance_result, answer_clean
        )
        improvements = self._identify_improvements(
            keyword_result, length_result, relevance_result, answer_clean, question
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            keyword_result, length_result, answer_clean
        )

        return EvaluationResult(
            score=final_score,
            keywords_found=keyword_result["found"],
            keywords_missed=keyword_result["missed"],
            keyword_score=round(keyword_result["score"], 1),
            length_score=round(length_result["score"], 1),
            relevance_score=round(relevance_result["score"], 1),
            strengths=strengths,
            improvements=improvements,
            model_answer_hint=question.model_answer_hint,
            confidence=confidence,
        )

    def evaluate_batch(
        self,
        answers: List[str],
        questions: List[Question],
    ) -> List[EvaluationResult]:
        """Evaluate multiple answers at once."""
        if len(answers) != len(questions):
            raise ValueError("Number of answers must match number of questions")
        return [
            self.evaluate(answer, question)
            for answer, question in zip(answers, questions)
        ]

    def get_overall_score(self, results: List[EvaluationResult]) -> Dict:
        """Calculate overall interview score from multiple evaluations."""
        if not results:
            return {"overall": 0.0, "count": 0}

        scores = [r.score for r in results]
        total_found = sum(len(r.keywords_found) for r in results)
        total_expected = total_found + sum(len(r.keywords_missed) for r in results)

        return {
            "overall": round(sum(scores) / len(scores), 1),
            "highest": max(scores),
            "lowest": min(scores),
            "count": len(results),
            "keyword_coverage": round(
                (total_found / max(total_expected, 1)) * 100, 1
            ),
            "strong_answers": sum(1 for s in scores if s >= 7.0),
            "weak_answers": sum(1 for s in scores if s < 4.0),
        }

    # ─── Internal Scoring Methods ─────────────────────────────────────────

    def _score_keywords(
        self, answer_lower: str, expected_keywords: List[str]
    ) -> Dict:
        """Score based on keyword matching."""
        found = []
        missed = []

        for keyword in expected_keywords:
            keyword_lower = keyword.lower()
            # Check for exact match or close variations
            if self._keyword_present(answer_lower, keyword_lower):
                found.append(keyword)
            else:
                missed.append(keyword)

        # Calculate score: percentage of keywords found, scaled to 10
        if not expected_keywords:
            score = 5.0  # Neutral if no keywords defined
        else:
            ratio = len(found) / len(expected_keywords)
            # Non-linear scoring: reward getting most keywords
            score = self._keyword_ratio_to_score(ratio)

        return {"score": score, "found": found, "missed": missed}

    def _keyword_present(self, text: str, keyword: str) -> bool:
        """Check if a keyword (or its variations) is present in text."""
        # Direct match
        if keyword in text:
            return True

        # Word boundary match (handles partial word matches)
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text):
            return True

        # Handle common variations
        variations = self._get_keyword_variations(keyword)
        for variation in variations:
            if variation in text:
                return True

        return False

    def _get_keyword_variations(self, keyword: str) -> List[str]:
        """Generate common variations of a keyword."""
        variations = []

        # Hyphenation variations
        if '-' in keyword:
            variations.append(keyword.replace('-', ' '))
            variations.append(keyword.replace('-', ''))
        elif ' ' in keyword:
            variations.append(keyword.replace(' ', '-'))
            variations.append(keyword.replace(' ', ''))

        # Common abbreviations
        abbrevs = {
            "object-oriented": ["oop", "oo"],
            "database": ["db"],
            "application": ["app"],
            "configuration": ["config"],
            "repository": ["repo"],
            "continuous integration": ["ci"],
            "continuous deployment": ["cd"],
            "function": ["func", "fn"],
            "implementation": ["impl"],
            "authentication": ["auth", "authn"],
            "authorization": ["authz"],
            "infrastructure": ["infra"],
        }

        if keyword in abbrevs:
            variations.extend(abbrevs[keyword])

        # Plural/singular
        if keyword.endswith('s') and len(keyword) > 3:
            variations.append(keyword[:-1])
        elif not keyword.endswith('s'):
            variations.append(keyword + 's')

        return variations

    def _keyword_ratio_to_score(self, ratio: float) -> float:
        """Convert keyword match ratio to a score using a curve."""
        # Use a slightly generous curve:
        # 0% → 0, 25% → 3, 50% → 5.5, 75% → 7.5, 100% → 10
        if ratio <= 0:
            return 0.0
        elif ratio >= 1.0:
            return 10.0
        else:
            # Slight S-curve for more nuanced scoring
            return 10.0 * (1 - (1 - ratio) ** 1.5)

    def _score_length(self, answer: str, difficulty: str) -> Dict:
        """Score based on answer length appropriateness."""
        words = answer.split()
        word_count = len(words)

        # Get thresholds based on difficulty
        if difficulty == "easy":
            min_words = MIN_WORDS_EASY
            ideal_words = IDEAL_WORDS_EASY
        elif difficulty == "medium":
            min_words = MIN_WORDS_MEDIUM
            ideal_words = IDEAL_WORDS_MEDIUM
        else:
            min_words = MIN_WORDS_HARD
            ideal_words = IDEAL_WORDS_HARD

        # Score calculation
        if word_count < min_words // 2:
            # Very short: heavy penalty
            score = max(1.0, (word_count / min_words) * 4.0)
        elif word_count < min_words:
            # Short: moderate penalty
            score = 3.0 + (word_count - min_words // 2) / (min_words // 2) * 3.0
        elif word_count <= ideal_words:
            # Good range
            progress = (word_count - min_words) / max(1, ideal_words - min_words)
            score = 6.0 + progress * 4.0
        elif word_count <= MAX_WORDS_PENALTY:
            # Slightly verbose but acceptable
            score = 9.0
        else:
            # Too verbose: slight penalty
            excess_ratio = (word_count - MAX_WORDS_PENALTY) / MAX_WORDS_PENALTY
            score = max(6.0, 9.0 - excess_ratio * 3.0)

        return {"score": min(10.0, score), "word_count": word_count}

    def _score_relevance(
        self, answer: str, question_text: str, model_hint: str
    ) -> Dict:
        """Score relevance using TF-IDF similarity."""
        if not HAS_SKLEARN or not model_hint:
            # Fallback: simple word overlap
            return self._fallback_relevance(answer, question_text, model_hint)

        try:
            # Combine question + model hint as reference
            reference = f"{question_text} {model_hint}"

            # Fit TF-IDF on both texts
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            tfidf_matrix = vectorizer.fit_transform([reference, answer])

            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

            # Convert similarity (0-1) to score (0-10)
            # Similarity > 0.3 is usually quite relevant for interview answers
            score = min(10.0, similarity * 25.0)  # Scale up: 0.4 similarity → 10

            return {"score": max(0.0, score), "similarity": similarity}

        except Exception:
            return self._fallback_relevance(answer, question_text, model_hint)

    def _fallback_relevance(
        self, answer: str, question_text: str, model_hint: str
    ) -> Dict:
        """Fallback relevance scoring using word overlap (no sklearn needed)."""
        reference_words = set(
            re.findall(r'\b\w{3,}\b', f"{question_text} {model_hint}".lower())
        )
        answer_words = set(re.findall(r'\b\w{3,}\b', answer.lower()))

        # Remove very common words
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'has',
            'have', 'been', 'with', 'this', 'that', 'from', 'they',
            'will', 'would', 'there', 'their', 'what', 'about', 'which',
            'when', 'make', 'like', 'time', 'very', 'your', 'how',
        }
        reference_words -= stopwords
        answer_words -= stopwords

        if not reference_words:
            return {"score": 5.0, "similarity": 0.5}

        overlap = reference_words & answer_words
        ratio = len(overlap) / len(reference_words)

        score = min(10.0, ratio * 15.0)  # Scale: 0.67 overlap → 10
        return {"score": max(0.0, score), "similarity": ratio}

    def _calculate_quality_modifier(self, answer: str) -> float:
        """Calculate bonus/penalty based on answer quality indicators."""
        modifier = 0.0
        answer_lower = answer.lower()

        # Penalty for filler words
        filler_count = 0
        for pattern in FILLER_PATTERNS:
            matches = re.findall(pattern, answer_lower)
            filler_count += len(matches)

        if filler_count > 5:
            modifier -= 1.0
        elif filler_count > 2:
            modifier -= 0.5

        # Bonus for quality indicators (examples, structure, reasoning)
        quality_count = 0
        for pattern in QUALITY_INDICATORS:
            matches = re.findall(pattern, answer_lower)
            quality_count += len(matches)

        if quality_count >= 4:
            modifier += 1.0
        elif quality_count >= 2:
            modifier += 0.5

        # Bonus for structured answer (numbered points, bullet-like)
        if re.search(r'(?:^|\n)\s*(?:\d+[.):]|\-|\*|•)', answer):
            modifier += 0.3

        return modifier

    def _calculate_confidence(
        self, keyword_result: Dict, length_result: Dict, answer: str
    ) -> float:
        """Calculate confidence in the evaluation (0-1)."""
        confidence = 0.5  # Base confidence

        # More keywords defined = more confident in keyword scoring
        total_keywords = len(keyword_result["found"]) + len(keyword_result["missed"])
        if total_keywords >= 8:
            confidence += 0.2
        elif total_keywords >= 5:
            confidence += 0.1

        # Longer answers give more signal
        word_count = length_result.get("word_count", 0)
        if word_count > 50:
            confidence += 0.2
        elif word_count > 20:
            confidence += 0.1

        # Very short answers: low confidence in evaluation
        if word_count < 10:
            confidence = 0.3

        return min(1.0, confidence)

    def _identify_strengths(
        self,
        keyword_result: Dict,
        length_result: Dict,
        relevance_result: Dict,
        answer: str,
    ) -> List[str]:
        """Identify strengths in the answer."""
        strengths = []

        # Keywords
        found = keyword_result["found"]
        if len(found) >= 5:
            strengths.append(f"Excellent coverage of key concepts ({len(found)} relevant terms used)")
        elif len(found) >= 3:
            strengths.append(f"Good mention of important concepts: {', '.join(found[:4])}")

        # Length
        if length_result["score"] >= 8.0:
            strengths.append("Well-detailed response with appropriate depth")

        # Relevance
        if relevance_result["score"] >= 7.0:
            strengths.append("Highly relevant and on-topic response")

        # Quality indicators
        answer_lower = answer.lower()
        if re.search(r'\b(for example|such as|e\.g\.)', answer_lower):
            strengths.append("Good use of examples to illustrate points")
        if re.search(r'\b(trade-off|pros? and cons?|advantage|disadvantage)', answer_lower):
            strengths.append("Shows awareness of trade-offs")
        if re.search(r'\b(in practice|production|real-world|at scale)', answer_lower):
            strengths.append("Demonstrates practical/production experience")

        return strengths[:5]  # Limit to top 5

    def _identify_improvements(
        self,
        keyword_result: Dict,
        length_result: Dict,
        relevance_result: Dict,
        answer: str,
        question: Question,
    ) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        missed = keyword_result["missed"]

        # Missed keywords
        if len(missed) >= 5:
            top_missed = missed[:4]
            improvements.append(
                f"Consider discussing: {', '.join(top_missed)}"
            )
        elif len(missed) >= 2:
            improvements.append(
                f"Could strengthen by mentioning: {', '.join(missed[:3])}"
            )

        # Length issues
        word_count = length_result.get("word_count", 0)
        if word_count < 20:
            improvements.append(
                "Answer is very brief. Try to elaborate with examples and reasoning."
            )
        elif word_count < 40 and question.difficulty in ("medium", "hard"):
            improvements.append(
                "Consider adding more detail, examples, or trade-off analysis."
            )
        elif word_count > MAX_WORDS_PENALTY:
            improvements.append(
                "Answer is quite lengthy. Consider being more concise and focused."
            )

        # Relevance
        if relevance_result["score"] < 4.0:
            improvements.append(
                "The response could be more focused on the specific question asked."
            )

        # Structure
        if word_count > 80 and not re.search(r'(?:^|\n)\s*(?:\d+[.):]|\-|\*|•|first|second)', answer.lower()):
            improvements.append(
                "Consider structuring longer answers with numbered points or clear sections."
            )

        # Examples
        if not re.search(r'\b(for example|such as|e\.g\.|instance)', answer.lower()):
            if question.difficulty in ("medium", "hard"):
                improvements.append(
                    "Adding specific examples would strengthen the answer."
                )

        return improvements[:5]  # Limit to top 5

    def _normalize_text(self, text: str) -> str:
        """Normalize text for evaluation."""
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text


# ── Convenience function (matches service imports) ────────────────────
_evaluator_instance = None

def evaluate_answer(
    question_text: str,
    answer_text: str,
    expected_keywords: list = None,
    difficulty: str = "medium",
) -> dict:
    """
    Evaluate a candidate's answer and return scoring details.
    
    This is the main entry point used by interview_agent.py.
    
    Args:
        question_text: The interview question that was asked
        answer_text: The candidate's response
        expected_keywords: List of keywords a good answer should mention
        difficulty: easy/medium/hard
    
    Returns:
        dict with: score (0-10), strengths (list), gaps (list),
        model_answer_hint (str), depth (str)
    """
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = AnswerEvaluator()
    
    # Create a Question-like object for the evaluator
    question_obj = Question(
        id="eval_q",
        text=question_text,
        topic="",
        difficulty=difficulty,
        category="technical",
        question_type="technical",
        expected_keywords=expected_keywords or [],
        model_answer_hint="",
    )
    
    result = _evaluator_instance.evaluate(
        answer=answer_text,
        question=question_obj,
    )
    
    # Convert EvaluationResult to dict with expected keys
    return {
        "score": int(round(result.score)),
        "strengths": result.strengths or [],
        "gaps": result.improvements or [],
        "model_answer_hint": result.model_answer_hint or "",
        "acknowledgment": _generate_acknowledgment(int(round(result.score))),
        "keywords_found": result.keywords_found or [],
        "keywords_missed": result.keywords_missed or [],
    }


def _generate_acknowledgment(score: int) -> str:
    """Generate a brief acknowledgment based on score."""
    if score >= 8:
        return "✅ **Excellent answer!** You demonstrated strong understanding."
    elif score >= 6:
        return "👍 **Good answer.** You covered the key points well."
    elif score >= 4:
        return "💡 **Decent attempt.** There's room to deepen your explanation."
    else:
        return "⚠️ **Needs improvement.** Try to be more specific with examples."
