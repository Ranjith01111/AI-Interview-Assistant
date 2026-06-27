"""
Semantic Matcher — Embedding-based similarity scoring using nomic-embed-text.

Replaces TF-IDF with real semantic understanding via local embeddings.
Provides concept coverage analysis for expected keywords/concepts.

100% local. Uses Ollama's nomic-embed-text model.
"""

import asyncio
import math
from typing import Dict, List, Optional, Tuple

from .agent_config import get_agentic_config
from .ollama_client import get_ollama_client, OllamaClient

# ── Logger Setup ─────────────────────────────────────────────────────────────
try:
    from backend.core.logging import get_logger
    logger = get_logger("backend.agentic.semantic_matcher")
except ImportError:
    import logging
    logger = logging.getLogger("agentic.semantic_matcher")


# ══════════════════════════════════════════════════════════════════════════════
# VECTOR MATH UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    Returns:
        Float between -1.0 and 1.0 (typically 0.0 to 1.0 for text embeddings)
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def normalize_similarity(raw_sim: float) -> float:
    """
    Normalize cosine similarity from [-1, 1] range to [0, 1] range.
    Text embeddings are typically in [0.3, 0.95] range, so we
    apply a calibrated scaling that maps:
        0.3 -> 0.0 (unrelated)
        0.6 -> 0.5 (somewhat related)
        0.85+ -> 1.0 (very similar)
    """
    # Linear scaling with floor and ceiling
    floor = 0.3
    ceiling = 0.85
    if raw_sim <= floor:
        return 0.0
    if raw_sim >= ceiling:
        return 1.0
    return (raw_sim - floor) / (ceiling - floor)


# ══════════════════════════════════════════════════════════════════════════════
# SEMANTIC MATCHER CLASS
# ══════════════════════════════════════════════════════════════════════════════

class SemanticMatcher:
    """
    Uses nomic-embed-text for semantic similarity scoring.

    Provides:
    - Pairwise similarity between answer and question/expected content
    - Concept coverage: how well each expected concept is covered in the answer
    - Relevance scoring: overall semantic relevance of answer to question

    Usage:
        matcher = SemanticMatcher()
        sim = await matcher.compute_similarity("text A", "text B")
        coverage = await matcher.find_concept_coverage(answer, ["concept1", "concept2"])
    """

    def __init__(self, client: Optional[OllamaClient] = None):
        self._client = client or get_ollama_client()
        self._config = get_agentic_config()
        self._model = self._config.embedding_model
        # Simple cache to avoid re-embedding the same text
        self._cache: Dict[str, List[float]] = {}
        self._cache_max_size: int = 100

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for a text string.

        Uses an in-memory cache to avoid redundant API calls within a session.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None if embedding failed
        """
        if not text or not text.strip():
            return None

        # Check cache
        cache_key = text.strip()[:500]  # Truncate for cache key
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get embedding from Ollama
        embedding = await self._client.embed(self._model, text.strip())

        if embedding is not None:
            # Cache management — evict oldest if full
            if len(self._cache) >= self._cache_max_size:
                # Remove first item (approximate LRU)
                first_key = next(iter(self._cache))
                del self._cache[first_key]
            self._cache[cache_key] = embedding

        return embedding

    async def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute semantic similarity between two texts.

        Args:
            text_a: First text
            text_b: Second text

        Returns:
            Normalized similarity score from 0.0 (unrelated) to 1.0 (identical meaning)
        """
        if not text_a or not text_b:
            return 0.0

        # Get embeddings concurrently
        emb_a, emb_b = await asyncio.gather(
            self.get_embedding(text_a),
            self.get_embedding(text_b),
        )

        if emb_a is None or emb_b is None:
            logger.warning("semantic_similarity_failed", reason="embedding_unavailable")
            return 0.0

        raw_sim = cosine_similarity(emb_a, emb_b)
        normalized = normalize_similarity(raw_sim)

        logger.debug(
            "semantic_similarity_computed",
            raw=round(raw_sim, 4),
            normalized=round(normalized, 4),
            text_a_len=len(text_a),
            text_b_len=len(text_b),
        )

        return normalized

    async def find_concept_coverage(
        self,
        answer: str,
        expected_concepts: List[str],
    ) -> Dict[str, float]:
        """
        Determine how well each expected concept is covered in the answer.

        This embeds the answer and each concept, then computes similarity.
        A high score means the answer semantically covers that concept,
        even without using the exact keyword.

        Args:
            answer: The candidate's answer text
            expected_concepts: List of concepts/keywords expected in a good answer

        Returns:
            Dict mapping each concept to its coverage score (0.0 - 1.0)
        """
        if not answer or not expected_concepts:
            return {c: 0.0 for c in expected_concepts}

        # Get answer embedding
        answer_emb = await self.get_embedding(answer)
        if answer_emb is None:
            return {c: 0.0 for c in expected_concepts}

        # Get concept embeddings concurrently
        concept_embeddings = await asyncio.gather(
            *[self.get_embedding(concept) for concept in expected_concepts]
        )

        coverage: Dict[str, float] = {}
        for concept, concept_emb in zip(expected_concepts, concept_embeddings):
            if concept_emb is None:
                coverage[concept] = 0.0
            else:
                raw_sim = cosine_similarity(answer_emb, concept_emb)
                coverage[concept] = normalize_similarity(raw_sim)

        logger.info(
            "concept_coverage_computed",
            num_concepts=len(expected_concepts),
            avg_coverage=round(
                sum(coverage.values()) / max(len(coverage), 1), 3
            ),
            covered_above_50=sum(1 for v in coverage.values() if v > 0.5),
        )

        return coverage

    async def compute_relevance_score(
        self,
        question: str,
        answer: str,
        model_answer_hint: str = "",
    ) -> float:
        """
        Compute overall relevance of the answer to the question.

        If a model answer hint is available, also compares to that for
        a more calibrated score.

        Args:
            question: The interview question
            answer: The candidate's answer
            model_answer_hint: Optional model/ideal answer for comparison

        Returns:
            Relevance score from 0.0 to 1.0
        """
        # Similarity to question (baseline relevance)
        q_similarity = await self.compute_similarity(question, answer)

        if model_answer_hint:
            # Also compare to model answer for calibrated scoring
            model_similarity = await self.compute_similarity(model_answer_hint, answer)
            # Weighted blend: model answer comparison is more informative
            relevance = 0.3 * q_similarity + 0.7 * model_similarity
        else:
            relevance = q_similarity

        return min(1.0, max(0.0, relevance))

    async def compute_overall_semantic_score(
        self,
        question: str,
        answer: str,
        expected_concepts: List[str],
        model_answer_hint: str = "",
    ) -> Dict[str, float]:
        """
        Compute a comprehensive semantic evaluation.

        Returns:
            Dict with:
                - relevance_score: How relevant the answer is to the question
                - concept_coverage_score: Average coverage of expected concepts
                - overall_score: Blended semantic score (0-10 scale)
                - concept_details: Per-concept coverage
        """
        # Run all computations concurrently
        relevance_task = self.compute_relevance_score(question, answer, model_answer_hint)
        coverage_task = self.find_concept_coverage(answer, expected_concepts)

        relevance, coverage = await asyncio.gather(relevance_task, coverage_task)

        # Calculate average concept coverage
        if coverage:
            avg_coverage = sum(coverage.values()) / len(coverage)
        else:
            avg_coverage = 0.0

        # Blend into overall score (0-10)
        # 60% concept coverage + 40% relevance
        overall = (0.6 * avg_coverage + 0.4 * relevance) * 10.0

        return {
            "relevance_score": round(relevance, 4),
            "concept_coverage_score": round(avg_coverage, 4),
            "overall_score": round(min(10.0, max(0.0, overall)), 2),
            "concept_details": {k: round(v, 3) for k, v in coverage.items()},
        }

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()


# ══════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL SINGLETON
# ══════════════════════════════════════════════════════════════════════════════

_matcher_instance: Optional[SemanticMatcher] = None


def get_semantic_matcher() -> SemanticMatcher:
    """Get or create the global SemanticMatcher singleton."""
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = SemanticMatcher()
    return _matcher_instance
