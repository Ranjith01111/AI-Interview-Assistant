# AI Interview Assistant — Technical Architecture Report

**Version:** 2.1.0 (Standalone/Offline)  
**Date:** 2026-06-27  
**Author:** Ranjith V  
**Mode:** Fully Offline — No External APIs Required

---

## 🧠 AI & NLP Approach

### Model Architecture: **Rule-Based NLP + Statistical Scoring**

This project uses a **fully self-contained NLP engine** — no LLMs, no cloud APIs, no internet required. All AI functionality is powered by:

| Component | Algorithm/Technique | Purpose |
|-----------|-------------------|---------|
| Resume Parser | **Regex + Keyword Matching** (80+ skill patterns) | Extract skills, experience, projects, education from PDF resumes |
| Question Generator | **Template Bank + Weighted Random Selection** | Select relevant questions from a 500-question bank based on detected skills & experience level |
| Answer Evaluator | **TF-IDF + Keyword Matching + Cosine Similarity** | Score candidate answers against expected keywords and model answers |
| Feedback Generator | **Rule-Based Scoring + Template Feedback** | Generate per-question strengths/weaknesses and final interview summary |
| Difficulty Calibration | **Experience-Based Heuristic** | Adjusts question difficulty based on candidate's years of experience |

### Why No LLM?
- **Zero cost** — runs completely free
- **Zero latency** — no API calls, instant responses
- **Full privacy** — all data stays local
- **Works offline** — no internet dependency

---

## 🤖 AI Agent Architecture

### Interview Agent: **State Machine Pattern**

The interview agent (`backend/services/interview_agent.py`) is NOT an LLM agent. It's a deterministic **finite state machine**:

```
States:
  WAITING_FOR_ANSWER → EVALUATING → PROVIDING_FEEDBACK → NEXT_QUESTION → COMPLETED

Transitions:
  User sends answer → Agent evaluates (keyword scoring) → Returns feedback + next question
```

**Agent Components:**
- **State Management** — Tracks current question index, conversation history, scores
- **Persistence** — Agent state saved in Redis between requests (stateless backend)
- **Evaluation Pipeline** — Answer → keyword extraction → TF-IDF scoring → threshold check → feedback template
- **No Follow-ups** — Configurable via `AGENT_MAX_FOLLOW_UPS=0` (disabled)

---

## 📊 Algorithms Used

### 1. Resume Parsing Algorithm

```
Input: Raw PDF text
Pipeline:
  1. Section Detection — regex patterns for "Experience", "Skills", "Projects", "Education"
  2. Skill Extraction — 80+ regex patterns match against 14 skill categories
  3. Experience Calculation — date range parsing (e.g., "2020-Present" → 4 years)
  4. Project Extraction — identifies project blocks with tech stacks
  5. Name Detection — first line / header heuristic
Output: ParsedResume { skills[], experience_years, skill_categories{}, projects[] }
```

### 2. Question Selection Algorithm

```
Input: skills[], experience_level, num_questions
Pipeline:
  1. Skill → Category Mapping (e.g., "react" → ["react"], "docker" → ["docker"])
  2. Difficulty Range Selection (easy: [easy], mid: [easy,medium], senior: [medium,hard])
  3. Distribution Split — 70% technical, 30% behavioral/HR
  4. Category-Balanced Sampling — ensure each detected skill category is represented
  5. Random shuffle for natural ordering
Output: List[Question] with id, text, topic, difficulty, category, expected_keywords
```

### 3. Answer Evaluation Algorithm

```
Input: candidate_answer, expected_keywords[], model_answer_hint
Pipeline:
  1. Text Preprocessing — lowercase, remove stopwords, tokenize
  2. Keyword Match Score — count of expected keywords found (0-10 scale)
  3. TF-IDF Vectorization — convert both answer and model_answer to TF-IDF vectors
  4. Cosine Similarity — measure semantic overlap between candidate answer and model answer
  5. Combined Score — weighted: 60% keyword match + 40% cosine similarity
  6. Threshold Classification:
     - 8-10: Excellent (strong hire)
     - 6-7.9: Good (hire)
     - 4-5.9: Average (maybe)
     - 0-3.9: Below expectations (no hire)
Output: { score: int, strengths: [], improvements: [], feedback: str }
```

### 4. Proctoring Algorithm (Client-Side)

```
Detection Methods:
  1. Face Presence — WebRTC camera + frame capture every 15s → server analysis
  2. Tab Switch — visibilitychange event listener
  3. Fullscreen Exit — fullscreenchange event (Esc = auto-terminate)
  4. Voice Detection — Web Audio API frequency analysis (threshold: avg > 45)
  5. Copy Prevention — clipboard event blocked

Risk Scoring:
  - Each violation type has a weight (tab switch = HIGH, voice = MEDIUM)
  - 3 voice violations → auto-terminate session
  - Fullscreen exit → immediate termination
```

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Browser                         │
│              Vite SPA (localhost:5173)                    │
│                                                          │
│   ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────┐  │
│   │  Login  │  │Dashboard │  │Interview│  │ Voice  │  │
│   └────┬────┘  └────┬─────┘  └────┬────┘  └───┬────┘  │
│        └─────────────┼─────────────┼───────────┘        │
│                      │ REST API (JWT Bearer)             │
└──────────────────────┼───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│              FastAPI Backend (localhost:8000)              │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                    Routes Layer                       │ │
│  │  /auth  /resume  /interview  /voice  /proctor       │ │
│  │  /coding  /analytics  /health                        │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │               Services Layer                         │ │
│  │  interview_agent  question_service  resume_service   │ │
│  │  session_service  auth_service  proctor_service      │ │
│  └───────────────────────┬─────────────────────────────┘ │
│                          │                                │
│  ┌───────────────────────▼─────────────────────────────┐ │
│  │          NLP Engine (Standalone, No APIs)            │ │
│  │                                                      │ │
│  │  resume_parser ─── Regex + 80 skill patterns        │ │
│  │  question_bank ─── 500 questions × 14 categories    │ │
│  │  question_generator ─ Weighted selection algorithm   │ │
│  │  answer_evaluator ── TF-IDF + keyword scoring       │ │
│  │  feedback_generator ─ Template-based feedback        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
└────────┬───────────────────────────┬─────────────────────┘
         │                           │
┌────────▼────────┐        ┌────────▼────────┐
│   PostgreSQL    │        │     Redis       │
│  (port 5433)   │        │  (port 6379)    │
│                 │        │                 │
│  11 tables:     │        │  Stores:        │
│  users          │        │  - session meta │
│  interview_ses  │        │  - questions    │
│  questions      │        │  - agent state  │
│  answers        │        │  - rate limits  │
│  proctor_logs   │        │                 │
│  analytics      │        │                 │
│  audit_logs     │        │                 │
│  resumes        │        │                 │
│  coding_*       │        │                 │
└─────────────────┘        └─────────────────┘
```

---

## 🔧 Tech Stack (Actual — Current)

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.115 | Async REST API framework |
| **SQLAlchemy 2.0** | 2.0+ | Async ORM (asyncpg driver) |
| **Pydantic v2** | 2.7.4 | Request/response validation |
| **Redis** | 7 | Session cache + rate-limit state |
| **PostgreSQL** | 16 | Relational data store |
| **structlog** | — | Structured JSON logging |
| **SlowAPI** | — | Rate limiting |
| **bcrypt** | — | Password hashing |
| **PyJWT** | — | JWT token generation |
| **pdfplumber** | — | PDF text extraction |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Vanilla JS (ES Modules)** | Zero-framework SPA |
| **Vite 5** | Dev server + bundler |
| **Web Speech API** | Browser-native STT/TTS (voice interview) |
| **Web Audio API** | Voice detection for proctoring |
| **WebRTC (getUserMedia)** | Camera access for proctoring |
| **Custom CSS Design System** | Dark mode + gold (#f5b800) palette |

### What's NOT Used (Removed)
| Previously Used | Status | Replaced By |
|----------------|--------|-------------|
| ~~OpenRouter API~~ | ❌ Removed | Local NLP engine |
| ~~LangChain~~ | ❌ Removed | State machine agent |
| ~~GPT-4o / GPT-4o-mini~~ | ❌ Removed | TF-IDF + keyword scoring |
| ~~FAISS~~ | ❌ Removed | Template bank (no vectors needed) |
| ~~OpenAI Embeddings~~ | ❌ Removed | Not needed |
| ~~Ollama~~ | ❌ Not used | Not needed |
| ~~MediaPipe~~ | ❌ Not used | Client-side WebRTC only |

---

## 🔊 Voice Interview System

### Architecture: **Browser-Native Speech APIs**

| Component | Technology | Details |
|-----------|-----------|---------|
| Speech-to-Text (STT) | `window.SpeechRecognition` | Browser built-in, no API |
| Text-to-Speech (TTS) | `window.speechSynthesis` | Browser built-in, no API |
| Silence Detection | Timer-based (3.5s timeout) | Auto-submits after silence |
| Interview Logic | Same backend `/interview/chat` API | Reuses text interview evaluation |

### Flow:
```
1. AI speaks question (TTS) → 2. User answers (STT) → 3. Backend evaluates → 4. AI speaks feedback (TTS) → repeat
```

---

## 📊 Question Bank Statistics

| Category | Questions | Difficulty Distribution |
|----------|-----------|----------------------|
| Python | 50 | Easy: 15, Medium: 20, Hard: 15 |
| JavaScript | 50 | Easy: 15, Medium: 20, Hard: 15 |
| React | 35 | Easy: 10, Medium: 15, Hard: 10 |
| SQL | 35 | Easy: 10, Medium: 15, Hard: 10 |
| AWS/Cloud | 30 | Easy: 8, Medium: 12, Hard: 10 |
| Docker/DevOps | 30 | Easy: 8, Medium: 12, Hard: 10 |
| Machine Learning | 30 | Easy: 8, Medium: 12, Hard: 10 |
| System Design | 40 | Easy: 10, Medium: 15, Hard: 15 |
| DSA | 40 | Easy: 12, Medium: 15, Hard: 13 |
| API Design | 25 | Easy: 8, Medium: 10, Hard: 7 |
| Git | 20 | Easy: 8, Medium: 8, Hard: 4 |
| Testing | 25 | Easy: 8, Medium: 10, Hard: 7 |
| Security | 25 | Easy: 8, Medium: 10, Hard: 7 |
| Behavioral/HR | 65 | Easy: 25, Medium: 25, Hard: 15 |
| **TOTAL** | **500** | |

---

## 🔐 Security Architecture

| Layer | Implementation |
|-------|---------------|
| Authentication | JWT access + refresh tokens (configurable expiry) |
| Password Storage | bcrypt (cost factor 12) |
| Rate Limiting | SlowAPI — 60/min general, 10/min auth |
| CORS | Whitelist-based origin control |
| Security Headers | CSP, X-Frame-Options, X-Content-Type-Options, HSTS |
| Input Validation | Pydantic v2 strict schemas on all endpoints |
| Session Isolation | UUID-based session IDs, Redis-scoped data |
| Proctoring | Client-side camera + audio monitoring |

---

## 📈 Scoring & Evaluation Model

```
Per-Question Score (0-10):
  = (keyword_match_score × 0.6) + (tfidf_cosine_similarity × 10 × 0.4)

Final Interview Score:
  = average(all_question_scores)

Recommendation Logic:
  score >= 8.0  → "Strong Hire"
  score >= 6.5  → "Hire"
  score >= 5.0  → "Maybe — needs improvement"
  score < 5.0   → "No Hire"
```

---

*Generated by Amazon Quick — 2026-06-27*
