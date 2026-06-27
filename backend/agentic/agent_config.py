"""
Agentic AI Configuration — Centralized settings for the Ollama-powered evaluation system.

All settings are dataclass-based with sensible defaults for local development.
In production, these are overridden by the main Settings class in backend/core/config.py.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgenticConfig:
    """
    Configuration for the Agentic AI evaluation system.

    Attributes:
        ollama_base_url: Base URL for the local Ollama instance
        evaluation_model: Model used for chain-of-thought answer evaluation (deepseek-r1)
        conversation_model: Model used for natural interview flow (llama3)
        embedding_model: Model used for semantic similarity (nomic-embed-text)
        temperature: Generation temperature (lower = more deterministic)
        max_follow_ups: Maximum follow-up questions per answer (0 = disabled)
        follow_up_threshold: Score threshold below which follow-ups are triggered
        timeout_seconds: Maximum time to wait for LLM response
        embed_timeout_seconds: Maximum time to wait for embedding response
        fallback_to_rules: If True, use rule-based scoring when Ollama is unavailable
        blend_llm_weight: Weight given to LLM evaluation (vs semantic) when blending
        blend_semantic_weight: Weight given to semantic similarity when blending
        max_retries: Number of retries for failed Ollama requests
        retry_delay: Seconds between retries
    """

    # ── Ollama Connection ─────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"

    # ── Model Selection ───────────────────────────────────────────────────
    evaluation_model: str = "deepseek-r1"       # Chain-of-thought evaluation
    conversation_model: str = "llama3"           # Natural interview conversation
    embedding_model: str = "nomic-embed-text"    # Semantic similarity embeddings

    # ── Generation Parameters ─────────────────────────────────────────────
    temperature: float = 0.3
    eval_temperature: float = 0.2   # Slightly lower for consistent scoring
    chat_temperature: float = 0.5   # Slightly higher for natural conversation
    max_tokens_eval: int = 1024     # Max tokens for evaluation response
    max_tokens_chat: int = 512      # Max tokens for conversation response

    # ── Follow-up Behavior ────────────────────────────────────────────────
    max_follow_ups: int = 1                     # Max follow-up questions per answer
    follow_up_threshold: float = 5.0            # Ask follow-up if score < this
    follow_up_min_answer_words: int = 15        # Ask follow-up if answer shorter than this

    # ── Timeouts & Reliability ────────────────────────────────────────────
    timeout_seconds: int = 60                   # LLM generation timeout
    embed_timeout_seconds: int = 10             # Embedding timeout
    health_check_timeout: int = 5               # Health check timeout
    max_retries: int = 1                        # Retries on transient failures
    retry_delay: float = 1.0                    # Seconds between retries

    # ── Fallback & Blending ───────────────────────────────────────────────
    fallback_to_rules: bool = True              # Use rule-based if Ollama unavailable
    blend_llm_weight: float = 0.70              # 70% LLM evaluation score
    blend_semantic_weight: float = 0.30         # 30% semantic similarity score

    # ── Logging ───────────────────────────────────────────────────────────
    log_reasoning: bool = True                  # Log chain-of-thought reasoning
    log_raw_responses: bool = False             # Log full LLM response text (verbose)


# ══════════════════════════════════════════════════════════════════════════════
# SINGLETON CONFIG — populated from backend.core.config.settings at import time
# ══════════════════════════════════════════════════════════════════════════════

_config_instance: Optional[AgenticConfig] = None


def get_agentic_config() -> AgenticConfig:
    """
    Get or create the agentic configuration singleton.

    Reads from backend.core.config.settings if available, otherwise uses defaults.
    """
    global _config_instance
    if _config_instance is not None:
        return _config_instance

    try:
        from backend.core.config import settings
        _config_instance = AgenticConfig(
            ollama_base_url=getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"),
            evaluation_model=getattr(settings, "OLLAMA_EVAL_MODEL", "deepseek-r1"),
            conversation_model=getattr(settings, "OLLAMA_CHAT_MODEL", "llama3"),
            embedding_model=getattr(settings, "OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            timeout_seconds=getattr(settings, "OLLAMA_TIMEOUT", 60),
            max_follow_ups=getattr(settings, "AGENT_MAX_FOLLOW_UPS", 1),
            fallback_to_rules=getattr(settings, "USE_LOCAL_NLP", True),
        )
    except ImportError:
        _config_instance = AgenticConfig()

    return _config_instance


def reset_config() -> None:
    """Reset the singleton — useful for testing."""
    global _config_instance
    _config_instance = None
