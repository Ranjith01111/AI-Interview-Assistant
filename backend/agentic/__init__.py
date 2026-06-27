"""
backend.agentic — Agentic AI Engine for the Interview Assistant.

This package provides LLM-powered evaluation, semantic matching,
and natural conversation capabilities using local Ollama models:
- deepseek-r1: Chain-of-thought answer evaluation
- llama3: Natural interview conversation
- nomic-embed-text: Semantic similarity matching

Architecture:
    ┌──────────────────────────────────────────────────────────┐
    │                  InterviewAgentV2                         │
    │          (Orchestrator — process_answer)                  │
    └──────────────┬────────────────────────┬──────────────────┘
                   │                        │
    ┌──────────────▼──────────┐  ┌──────────▼──────────────────┐
    │    HybridEvaluator      │  │   InterviewConductor         │
    │  (Score blending layer) │  │   (Natural conversation)     │
    └─────┬──────────┬────────┘  └──────────────────────────────┘
          │          │
    ┌─────▼────┐ ┌───▼────────────┐
    │ Evaluator │ │ SemanticMatcher │
    │   Agent   │ │ (embeddings)    │
    │(deepseek) │ │ (nomic-embed)   │
    └─────┬─────┘ └───┬────────────┘
          │           │
    ┌─────▼───────────▼─────┐
    │     OllamaClient       │
    │  (async HTTP to local  │
    │   Ollama instance)     │
    └────────────────────────┘

Usage:
    from backend.agentic import (
        evaluate_answer_agentic,
        get_hybrid_evaluator,
        get_interview_conductor,
        InterviewAgentV2,
        create_interview_agent,
        restore_interview_agent,
    )

    # Simple evaluation (backward-compatible with old evaluate_answer):
    result = await evaluate_answer_agentic(
        question_text="What is async/await?",
        answer_text="It's a way to write non-blocking code...",
        expected_keywords=["async", "await", "event loop"],
    )

    # Full agent flow:
    agent = await create_interview_agent(session_id, "John", 10)
    response = await agent.process_answer(user_message, questions, db)
"""

# ── Core components ──────────────────────────────────────────────────────────
from .agent_config import AgenticConfig, get_agentic_config, reset_config
from .ollama_client import OllamaClient, get_ollama_client, shutdown_ollama_client
from .semantic_matcher import SemanticMatcher, get_semantic_matcher
from .evaluator_agent import EvaluatorAgent, get_evaluator_agent
from .interview_conductor import InterviewConductor, get_interview_conductor
from .hybrid_evaluator import (
    HybridEvaluator,
    get_hybrid_evaluator,
    evaluate_answer_agentic,
)
from .interview_agent_v2 import (
    InterviewAgentV2,
    AgentStateV2,
    create_interview_agent,
    restore_interview_agent,
)

__all__ = [
    # Config
    "AgenticConfig",
    "get_agentic_config",
    "reset_config",
    # Ollama Client
    "OllamaClient",
    "get_ollama_client",
    "shutdown_ollama_client",
    # Semantic Matching
    "SemanticMatcher",
    "get_semantic_matcher",
    # Evaluation
    "EvaluatorAgent",
    "get_evaluator_agent",
    "HybridEvaluator",
    "get_hybrid_evaluator",
    "evaluate_answer_agentic",
    # Conversation
    "InterviewConductor",
    "get_interview_conductor",
    # Agent
    "InterviewAgentV2",
    "AgentStateV2",
    "create_interview_agent",
    "restore_interview_agent",
]

__version__ = "1.0.0"
