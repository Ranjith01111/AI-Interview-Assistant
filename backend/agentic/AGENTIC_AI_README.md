# 🧠 Agentic AI Engine — Integration Guide

## Overview

The Agentic AI Engine transforms the AI Interview Assistant from a keyword-matching system into an intelligent, reasoning-powered evaluation platform. It uses **three local Ollama models** working together:

| Model | Role | Purpose |
| --- | --- | --- |
| `deepseek-r1` | Evaluator | Chain-of-thought reasoning for answer scoring |
| `llama3` | Conductor | Natural conversation flow and transitions |
| `nomic-embed-text` | Matcher | Semantic similarity and concept coverage |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    InterviewAgentV2                            │
│            (Orchestrator — process_answer)                     │
└──────────────┬────────────────────────────┬──────────────────┘
               │                            │
┌──────────────▼──────────────┐  ┌──────────▼──────────────────┐
│      HybridEvaluator        │  │    InterviewConductor        │
│   (Score blending layer)    │  │   (Natural conversation)     │
│   70% LLM + 30% Semantic    │  │   Uses: llama3               │
└─────┬──────────────┬────────┘  └──────────────────────────────┘
      │              │
┌─────▼──────┐  ┌───▼────────────┐
│ Evaluator  │  │ SemanticMatcher │
│   Agent    │  │  (embeddings)   │
│ deepseek-r1│  │ nomic-embed-text│
└─────┬──────┘  └───┬────────────┘
      │              │
┌─────▼──────────────▼────────┐
│        OllamaClient         │
│   (async HTTP via httpx)    │
│   http://localhost:11434    │
└─────────────────────────────┘

```

## Key Features

### 1. Deep Answer Evaluation (EvaluatorAgent)

- Chain-of-thought reasoning via deepseek-r1
- Structured JSON output with scores, strengths, gaps
- Considers difficulty level and question category
- Generates targeted follow-up questions for weak answers

### 2. Semantic Understanding (SemanticMatcher)

- Real semantic similarity via nomic-embed-text embeddings
- Concept coverage analysis (did they explain the concept, even without exact keywords?)
- Question-answer relevance scoring
- Embedding cache for performance

### 3. Natural Conversation (InterviewConductor)

- Warm, personalized introductions
- Context-aware transitions between questions
- Intelligent follow-up question generation
- Encouraging, specific closing messages

### 4. Graceful Degradation (HybridEvaluator)

- **Ollama available**: Full agentic evaluation (LLM + semantic blending)
- **Ollama unavailable**: Automatic fallback to rule-based scoring
- **Partial failure**: Blends whatever is available
- **Never crashes**: Every path has a safe fallback

### 5. Follow-up Questions

- Triggered when score < threshold (default: 5.0)
- Also triggered for very brief answers (< 15 words)
- Maximum 1 follow-up per question (configurable)
- Follow-up answers can improve the original score

---

## Installation

### Prerequisites

1. **Ollama installed and running:**```bash
# Install Ollama (if not already)
# Windows: Download from https://ollama.ai

# Pull required models
ollama pull deepseek-r1
ollama pull llama3
ollama pull nomic-embed-text

# Verify Ollama is running
curl http://localhost:11434/api/tags

```
2. **httpx available** (should already be installed via FastAPI):```bash
pip install httpx

```

### File Placement

Copy the `agentic/` folder to your backend:

```
E:\AI Interview Assistant\backend\
├── agentic/                        ← NEW: This entire folder
│   ├── __init__.py
│   ├── agent_config.py
│   ├── ollama_client.py
│   ├── evaluator_agent.py
│   ├── interview_conductor.py
│   ├── semantic_matcher.py
│   ├── hybrid_evaluator.py
│   └── interview_agent_v2.py
├── core/
├── models/
├── nlp_engine/                     ← UNCHANGED: Still available as fallback
├── routes/
├── services/
│   ├── interview_agent.py          ← UNCHANGED: v1 still works
│   └── ...
└── main.py

```

---

## Configuration

### Add to `backend/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # ── Agentic AI (Ollama) ──────────────────────────────────────────
    USE_AGENTIC_AI: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_EVAL_MODEL: str = "deepseek-r1"
    OLLAMA_CHAT_MODEL: str = "llama3"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 60
    AGENT_MAX_FOLLOW_UPS: int = 1   # ← Change from 0 to 1

```

### Add to `.env`:

```env
# Agentic AI
USE_AGENTIC_AI=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EVAL_MODEL=deepseek-r1
OLLAMA_CHAT_MODEL=llama3
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_TIMEOUT=60
AGENT_MAX_FOLLOW_UPS=1

```

---

## Integration

### Option A: Replace interview_agent.py entirely

In your routes that use `InterviewAgent`, switch to `InterviewAgentV2`:

```python
# BEFORE (in routes/interview.py or similar):
from backend.services.interview_agent import InterviewAgent

# AFTER:
from backend.agentic import InterviewAgentV2 as InterviewAgent
from backend.agentic import create_interview_agent, restore_interview_agent

```

The `InterviewAgentV2` has the **same interface**:

- `create_new(session_id, candidate_name, total_questions)`
- `restore(session_id)`
- `process_answer(user_message, questions_cache, db) → ChatResponse`
- `generate_summary(db) → Dict`

### Option B: Conditional switching (recommended for gradual rollout)

```python
from backend.core.config import settings

if getattr(settings, "USE_AGENTIC_AI", False):
    from backend.agentic import InterviewAgentV2 as InterviewAgent
    from backend.agentic import create_interview_agent, restore_interview_agent
else:
    from backend.services.interview_agent import InterviewAgent
    # Use original factory methods

```

### Option C: Just use the evaluator (minimal change)

If you only want the improved scoring without changing the agent:

```python
# In backend/services/interview_agent.py, change the evaluation call:

# BEFORE:
from backend.nlp_engine.answer_evaluator import evaluate_answer

# AFTER:
import asyncio
from backend.agentic.hybrid_evaluator import evaluate_answer_agentic

# Then in process_answer():
evaluation = await evaluate_answer_agentic(
    question_text=question_text,
    answer_text=user_message,
    expected_keywords=expected_keywords,
)

```

Note: The agentic evaluator is async, so the calling code must be async too (which it already is in your FastAPI routes).

---

## App Lifecycle Integration

### Add to `backend/main.py`:

```python
from backend.agentic import shutdown_ollama_client

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_ollama_client()

```

---

## How It Works — Detailed Flow

### Answer Evaluation Flow

```
User submits answer
        │
        ▼
┌─ HybridEvaluator.evaluate() ─────────────────────────────────┐
│                                                               │
│  1. Check: await ollama_client.is_available()                 │
│     ├── NO → _rule_based_evaluate() → return                 │
│     └── YES ↓                                                 │
│                                                               │
│  2. Run CONCURRENTLY:                                         │
│     ├── EvaluatorAgent.evaluate_answer()  [deepseek-r1]       │
│     │     → Chain-of-thought reasoning                        │
│     │     → JSON extraction with robust parsing               │
│     │     → Returns: score, strengths, gaps, follow_up        │
│     │                                                         │
│     └── SemanticMatcher.compute_overall_semantic_score()       │
│           → Embed answer + concepts [nomic-embed-text]        │
│           → Cosine similarity per concept                     │
│           → Returns: relevance + coverage scores              │
│                                                               │
│  3. Blend results:                                            │
│     final_score = 0.70 × LLM_score + 0.30 × semantic_score   │
│                                                               │
│  4. Return unified evaluation dict                            │
└───────────────────────────────────────────────────────────────┘

```

### Follow-up Decision Flow

```
After evaluation:
        │
        ▼
Should follow-up?
├── max_follow_ups == 0 → NO (disabled)
├── follow_up_count >= max → NO (limit reached)
├── score >= threshold → NO (good enough)
├── no follow_up_question available → NO
└── score < threshold OR answer too brief → YES
        │
        ▼
Ask follow-up question
        │
        ▼
Process follow-up answer
        │
        ▼
Adjust score (follow-up can only help)
        │
        ▼
Advance to next question

```

---

## Evaluation Modes

The system tags each evaluation with its mode:

| Mode | Meaning |
| --- | --- |
| `"agentic"` | Full LLM evaluation via deepseek-r1 |
| `"hybrid"` | LLM + semantic blending (best quality) |
| `"semantic_enhanced"` | Rule-based enhanced with semantic scores |
| `"rule_based"` | Pure rule-based (Ollama unavailable) |
| `"fallback"` | LLM responded but JSON parsing failed |
| `"error_fallback"` | Unexpected error, returned default |

---

## Configuration Reference

| Setting | Default | Description |
| --- | --- | --- |
| `ollama_base_url` | `http://localhost:11434` | Ollama API endpoint |
| `evaluation_model` | `deepseek-r1` | Model for scoring |
| `conversation_model` | `llama3` | Model for transitions |
| `embedding_model` | `nomic-embed-text` | Model for embeddings |
| `temperature` | `0.3` | Default generation temperature |
| `eval_temperature` | `0.2` | Evaluation temperature (lower = consistent) |
| `chat_temperature` | `0.5` | Conversation temperature (higher = natural) |
| `max_follow_ups` | `1` | Max follow-ups per question |
| `follow_up_threshold` | `5.0` | Score below which follow-up triggers |
| `timeout_seconds` | `60` | LLM generation timeout |
| `embed_timeout_seconds` | `10` | Embedding timeout |
| `fallback_to_rules` | `True` | Enable rule-based fallback |
| `blend_llm_weight` | `0.70` | Weight for LLM score in blending |
| `blend_semantic_weight` | `0.30` | Weight for semantic score in blending |

---

## Troubleshooting

### Ollama not responding

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve

# Check model availability:
ollama list

```

### Slow evaluation (>30s)

- deepseek-r1 is a large model; first call may be slow (model loading)
- Subsequent calls will be faster (model stays in memory)
- If consistently slow, reduce `max_tokens_eval` in config
- Consider using a quantized version: `ollama pull deepseek-r1:7b`

### JSON parsing errors in logs

- This is normal occasionally — the LLM sometimes wraps JSON in text
- The robust parser handles: code fences, `<think>` blocks, trailing text
- Falls back to rule-based scoring if parsing completely fails

### Import errors

- Ensure the `agentic/` folder is inside `backend/`
- Ensure `httpx` is installed: `pip install httpx`
- The package works independently — no changes to existing code required

---

## Testing

### Quick smoke test:

```python
import asyncio
from backend.agentic import get_ollama_client, evaluate_answer_agentic

async def test():
    # Test connectivity
    client = get_ollama_client()
    available = await client.is_available()
    print(f"Ollama available: {available}")
    
    if available:
        models = await client.list_models()
        print(f"Models: {models}")
    
    # Test evaluation
    result = await evaluate_answer_agentic(
        question_text="What is a Python decorator?",
        answer_text="A decorator is a function that wraps another function to add behavior. You use the @syntax above the function definition.",
        expected_keywords=["function", "wrapper", "@syntax", "higher-order", "closure"],
    )
    print(f"Score: {result['score']}/10")
    print(f"Mode: {result['evaluation_mode']}")
    print(f"Strengths: {result['strengths']}")
    print(f"Gaps: {result['gaps']}")
    print(f"Follow-up: {result.get('follow_up_question')}")

asyncio.run(test())

```

---

## Performance Characteristics

| Operation | Typical Latency | Fallback Latency |
| --- | --- | --- |
| Full evaluation (deepseek-r1) | 5-15s | <100ms (rule-based) |
| Semantic matching (nomic-embed) | 200-500ms | N/A |
| Transition generation (llama3) | 1-3s | <1ms (template) |
| Health check | <100ms | N/A |
| Embedding (cached) | <1ms | N/A |

The system is designed for interview practice where 5-15s evaluation latency is acceptable (the user is reading feedback while the next question loads).

---

## Version History

- **v1.0.0** (Current): Initial agentic engine- deepseek-r1 evaluation with chain-of-thought
- Semantic matching via nomic-embed-text
- Natural conversation via llama3
- Hybrid scoring with graceful fallback
- Follow-up question support

