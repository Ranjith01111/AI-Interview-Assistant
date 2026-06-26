"""
Anti-Repetition Engine — FAISS-backed Question Deduplication

Prevents the generation of semantically duplicate interview questions
within a session. Uses OpenAI embeddings + FAISS cosine-similarity
search with a configurable threshold (default: 0.85).

Workflow:
  1. Initialize with session_id → load existing embeddings from DB/Redis
  2. For each candidate question → generate embedding → search FAISS index
  3. If max similarity ≥ threshold → reject as duplicate
  4. If unique → add to index + persist embedding to DB

Key Design Decisions:
  - Uses faiss.IndexFlatIP (Inner Product on L2-normalized vectors = cosine similarity)
  - Embeddings from OpenAI text-embedding-3-small (1536 dims)
  - Persists to PostgreSQL for cross-session historical lookups
  - Caches the live FAISS index in Redis for session-duration speed
"""

import uuid as uuid_mod
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.models.question_embedding import QuestionEmbedding
from backend.models.schemas import InterviewQuestion
from backend.services import session_service

logger = get_logger("backend.services.anti_repetition")

# ── Constants ────────────────────────────────────────────────────────
EMBEDDING_DIM = 1536  # text-embedding-3-small output dimensionality


class AntiRepetitionEngine:
    """
    FAISS-backed deduplication engine for interview questions.

    Maintains an in-memory FAISS index of L2-normalized question embeddings.
    Cosine similarity is computed via inner product on normalized vectors.

    Usage:
        engine = AntiRepetitionEngine()
        await engine.initialize(session_id, db)
        unique_questions = await engine.deduplicate_batch(questions, db)
    """

    def __init__(self) -> None:
        self.session_id: Optional[str] = None
        self.session_uuid: Optional[uuid_mod.UUID] = None
        self.threshold: float = settings.SIMILARITY_THRESHOLD
        self.max_retries: int = settings.MAX_DEDUP_RETRIES

        # FAISS index — Inner Product on L2-normalized vectors = cosine similarity
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(EMBEDDING_DIM)

        # Parallel list of question texts (for logging which question was duplicated)
        self._stored_texts: List[str] = []

        # Embedding model — OpenAI via LangChain
        self._embeddings_model: Optional[OpenAIEmbeddings] = None

    # ── Initialization ───────────────────────────────────────────────

    async def initialize(
        self,
        session_id: str,
        db: AsyncSession,
    ) -> None:
        """
        Initialize the engine for a specific session.

        Loads any previously stored embeddings from PostgreSQL and
        rebuilds the FAISS index so that new questions are checked
        against the full history.

        Args:
            session_id: The active interview session ID
            db: Async SQLAlchemy session
        """
        self.session_id = session_id
        self.session_uuid = uuid_mod.UUID(session_id)

        # Initialize the embedding model
        self._embeddings_model = OpenAIEmbeddings(
            model=settings.OPENROUTER_EMBEDDING_MODEL,
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": settings.OPENROUTER_SITE_URL,
                "X-OpenRouter-Title": settings.OPENROUTER_SITE_NAME,
            },
        )

        # Try loading cached FAISS index from Redis first
        cached_data = await session_service.get_dedup_index(session_id)
        if cached_data is not None:
            try:
                self._deserialize_index(cached_data)
                logger.info(
                    "dedup_index_loaded_from_cache",
                    session_id=session_id,
                    num_vectors=self.index.ntotal,
                )
                return
            except Exception as e:
                logger.warning(
                    "dedup_cache_load_failed_rebuilding",
                    error=str(e),
                )

        # Fallback: load from PostgreSQL
        await self._load_from_database(db)

        logger.info(
            "anti_repetition_engine_initialized",
            session_id=session_id,
            existing_embeddings=self.index.ntotal,
            threshold=self.threshold,
        )

    # ── Core API ─────────────────────────────────────────────────────

    async def is_duplicate(
        self,
        question_text: str,
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if a question is semantically too similar to any stored question.

        Args:
            question_text: The candidate question to check

        Returns:
            Tuple of:
              - is_dup (bool): True if similarity ≥ threshold
              - max_score (float): Highest cosine similarity found (0.0 if index empty)
              - matched_text (str | None): The most similar stored question text
        """
        if self.index.ntotal == 0:
            return False, 0.0, None

        embedding = await self._generate_embedding(question_text)
        query_vector = embedding.reshape(1, -1)

        # Search for the single nearest neighbour
        scores, indices = self.index.search(query_vector, k=1)
        max_score = float(scores[0][0])
        matched_idx = int(indices[0][0])

        if max_score >= self.threshold:
            matched_text = (
                self._stored_texts[matched_idx]
                if 0 <= matched_idx < len(self._stored_texts)
                else None
            )
            return True, max_score, matched_text

        return False, max_score, None

    async def add_question(
        self,
        question_text: str,
        question_id: int,
        db: AsyncSession,
    ) -> None:
        """
        Add a new question's embedding to the FAISS index AND persist
        it to PostgreSQL + Redis cache.

        Args:
            question_text: The question string
            question_id: The question's DB primary key
            db: Async SQLAlchemy session
        """
        embedding = await self._generate_embedding(question_text)

        # Add to FAISS index
        self.index.add(embedding.reshape(1, -1))
        self._stored_texts.append(question_text)

        # Persist to PostgreSQL
        db_embedding = QuestionEmbedding(
            session_id=self.session_uuid,
            question_id=question_id,
            question_text=question_text,
            embedding_vector=embedding.tobytes(),
            embedding_model=settings.OPENROUTER_EMBEDDING_MODEL,
        )
        db.add(db_embedding)

        # Update Redis cache
        await self._save_to_cache()

        logger.debug(
            "embedding_added",
            question_id=question_id,
            index_size=self.index.ntotal,
        )

    async def deduplicate_batch(
        self,
        questions: List[InterviewQuestion],
        db: AsyncSession,
    ) -> List[InterviewQuestion]:
        """
        Filter a batch of questions, keeping only those that are
        sufficiently unique relative to all previously accepted questions.

        This is the main entry point for the context engine integration.
        For each question:
          1. Check similarity against the FAISS index
          2. If duplicate → reject and log
          3. If unique → add to index + persist

        Args:
            questions: List of candidate InterviewQuestion objects
            db: Async SQLAlchemy session

        Returns:
            Filtered list with duplicates removed
        """
        if not questions:
            return []

        accepted: List[InterviewQuestion] = []
        rejected_count = 0

        for q in questions:
            is_dup, score, matched = await self.is_duplicate(q.question)

            if is_dup:
                rejected_count += 1
                logger.info(
                    "rejected_duplicate_question",
                    question=q.question[:80],
                    similarity=round(score, 4),
                    matched_to=matched[:80] if matched else "unknown",
                    session_id=self.session_id,
                )
                continue

            # Accept the question — add to index
            # Note: question_id here is the in-memory numbering;
            # the actual DB PK is assigned after flush.
            # We use a placeholder and the text itself for the embedding record.
            await self._add_to_index_only(q.question)
            accepted.append(q)

        if rejected_count:
            logger.info(
                "dedup_batch_complete",
                session_id=self.session_id,
                submitted=len(questions),
                accepted=len(accepted),
                rejected=rejected_count,
            )

        return accepted

    async def persist_accepted_embeddings(
        self,
        questions: List[InterviewQuestion],
        question_id_map: Dict[int, int],
        db: AsyncSession,
    ) -> None:
        """
        Persist embeddings for accepted questions after they have been
        flushed to PostgreSQL and have real primary keys.

        Called by question_service.py after db.flush() assigns IDs.

        Args:
            questions: The accepted InterviewQuestion list
            question_id_map: Maps question.id (1-based) → DB primary key
            db: Async SQLAlchemy session
        """
        for q in questions:
            db_pk = question_id_map.get(q.id)
            if db_pk is None:
                continue

            embedding = await self._generate_embedding(q.question)

            db_embedding = QuestionEmbedding(
                session_id=self.session_uuid,
                question_id=db_pk,
                question_text=q.question,
                embedding_vector=embedding.tobytes(),
                embedding_model=settings.OPENROUTER_EMBEDDING_MODEL,
            )
            db.add(db_embedding)

        # Update Redis cache with final state
        await self._save_to_cache()

        logger.info(
            "embeddings_persisted",
            session_id=self.session_id,
            count=len(questions),
            total_index_size=self.index.ntotal,
        )

    # ── Internal Helpers ─────────────────────────────────────────────

    async def _generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate a single L2-normalized embedding vector.

        Args:
            text: The text to embed

        Returns:
            numpy float32 array of shape (1536,), L2-normalized
        """
        raw = await self._embeddings_model.aembed_query(text)
        vec = np.array(raw, dtype=np.float32)

        # L2-normalize so inner product = cosine similarity
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec

    async def _add_to_index_only(self, question_text: str) -> None:
        """
        Add a question embedding to the in-memory FAISS index
        WITHOUT persisting to DB. Used during batch deduplication
        so that later questions in the same batch are checked
        against earlier ones.

        Args:
            question_text: The question string
        """
        embedding = await self._generate_embedding(question_text)
        self.index.add(embedding.reshape(1, -1))
        self._stored_texts.append(question_text)

    async def _load_from_database(self, db: AsyncSession) -> None:
        """
        Load all existing embeddings for this session from PostgreSQL
        and rebuild the FAISS index.

        Args:
            db: Async SQLAlchemy session
        """
        result = await db.execute(
            select(QuestionEmbedding).where(
                QuestionEmbedding.session_id == self.session_uuid
            )
        )
        rows = result.scalars().all()

        if not rows:
            logger.debug("no_existing_embeddings", session_id=self.session_id)
            return

        # Reconstruct vectors
        vectors = []
        for row in rows:
            vec = np.frombuffer(row.embedding_vector, dtype=np.float32)
            if vec.shape[0] == EMBEDDING_DIM:
                vectors.append(vec)
                self._stored_texts.append(row.question_text)
            else:
                logger.warning(
                    "skipping_malformed_embedding",
                    question_id=row.question_id,
                    expected_dim=EMBEDDING_DIM,
                    actual_dim=vec.shape[0],
                )

        if vectors:
            matrix = np.vstack(vectors).astype(np.float32)
            self.index.add(matrix)

        logger.info(
            "loaded_embeddings_from_db",
            session_id=self.session_id,
            loaded=len(vectors),
            skipped=len(rows) - len(vectors),
        )

    async def _save_to_cache(self) -> None:
        """Serialize the current FAISS index + texts and cache in Redis."""
        if self.session_id is None:
            return

        try:
            data = self._serialize_index()
            await session_service.save_dedup_index(self.session_id, data)
        except Exception as e:
            logger.warning("dedup_cache_save_failed", error=str(e))

    def _serialize_index(self) -> bytes:
        """
        Serialize the FAISS index + stored texts into a single
        bytes payload for Redis storage.

        Format: [4 bytes: num_texts] + [texts as newline-joined UTF-8] + [FAISS bytes]
        """
        import struct
        import io

        # Serialize FAISS index
        faiss_bytes = faiss.serialize_index(self.index)

        # Serialize texts
        texts_payload = "\n".join(self._stored_texts).encode("utf-8")

        # Pack: [len(texts_payload):4 bytes] + [texts_payload] + [faiss_bytes]
        header = struct.pack("<I", len(texts_payload))
        return header + texts_payload + bytes(faiss_bytes)

    def _deserialize_index(self, data: bytes) -> None:
        """
        Restore the FAISS index + stored texts from serialized bytes.

        Args:
            data: The raw bytes from Redis cache
        """
        import struct

        # Unpack header
        texts_len = struct.unpack("<I", data[:4])[0]
        texts_payload = data[4:4 + texts_len]
        faiss_data = data[4 + texts_len:]

        # Restore texts
        self._stored_texts = texts_payload.decode("utf-8").split("\n") if texts_len > 0 else []

        # Restore FAISS index
        faiss_array = np.frombuffer(faiss_data, dtype=np.uint8)
        self.index = faiss.deserialize_index(faiss_array)


# ── Module-level convenience function ────────────────────────────────

async def create_engine(
    session_id: str,
    db: AsyncSession,
) -> AntiRepetitionEngine:
    """
    Factory function: create and initialize an AntiRepetitionEngine.

    Args:
        session_id: The active interview session ID
        db: Async SQLAlchemy session

    Returns:
        Initialized AntiRepetitionEngine ready for deduplication
    """
    engine = AntiRepetitionEngine()
    await engine.initialize(session_id, db)
    return engine
