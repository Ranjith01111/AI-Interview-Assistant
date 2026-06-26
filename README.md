# 🤖 AI Interview Assistant

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-gold?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

**An enterprise-grade, AI-powered mock interview platform with real-time proctoring, voice interviews, coding assessments, and recruiter analytics — powered by GPT-4o and LangChain.**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Docs](#-api-reference) · [Project Structure](#-project-structure)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## 🌟 Overview

**AI Interview Assistant** is a full-stack, production-ready mock interview platform that leverages Large Language Models (LLMs) to simulate realistic technical interviews. Candidates upload their resume, the AI parses it to generate tailored questions, then conducts a conversational interview with real-time feedback, scoring, and a comprehensive final report.

The platform supports **text interviews**, **voice interviews**, **live coding assessments**, and **AI-driven proctoring** — making it suitable for both individual candidate practice and enterprise recruitment pipelines.

---

## ✨ Features

### 🎯 Candidate Experience

| Feature | Description |
|---|---|
| **Resume Upload & Parsing** | Upload PDF resumes; AI extracts skills, projects, and experience to craft personalised questions |
| **AI-Powered Interviews** | GPT-4o conducts realistic interviews with context-aware, memory-backed conversational flow |
| **Voice Interviews** | Full speech-to-text and text-to-speech interview mode with real-time transcription |
| **Live Coding Assessments** | In-browser code editor with multi-language sandbox execution (Python, JavaScript, C++, Java, SQL) |
| **Real-Time Feedback** | Instant per-answer scoring with strengths, weaknesses, and improvement suggestions |
| **Interview Summary** | Detailed final report with overall score, per-question breakdown, and hiring recommendation |

### 🛡️ Proctoring & Integrity

| Feature | Description |
|---|---|
| **Face Detection** | MediaPipe-powered face monitoring to detect candidate presence throughout the session |
| **Window Blur Detection** | Flags tab switching or window loss-of-focus events in real time |
| **Risk Score Engine** | Continuous risk scoring with LOW / MEDIUM / HIGH threat classification |
| **Event Audit Log** | Timestamped, immutable log of all proctoring events stored per session |

### 👩‍💼 Recruiter & Admin Tools

| Feature | Description |
|---|---|
| **Recruiter Dashboard** | View all candidate sessions, scores, and full interview summaries |
| **Analytics Dashboard** | Platform-wide metrics — completion rates, score distributions, skill frequency |
| **Role-Based Access Control** | Separate flows for `candidate`, `recruiter`, and `admin` roles enforced via JWT |
| **Audit Trails** | Full audit logging of all data-modifying API actions |

### ⚙️ Platform & Infrastructure

| Feature | Description |
|---|---|
| **JWT Authentication** | Secure access + refresh token flow with configurable expiry |
| **Rate Limiting** | Per-endpoint rate limiting via SlowAPI (60 req/min default, 10/min on auth) |
| **Anti-Repetition Engine** | FAISS-based semantic deduplication prevents repeated or similar questions |
| **Auto-Migration** | Schema migrations run automatically on startup — no manual Alembic steps in development |
| **Structured Logging** | JSON-structured logs via structlog with full request tracing |
| **Docker-First Infra** | PostgreSQL and Redis run in isolated, health-checked Docker containers |

---

## 🛠️ Tech Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com/)** — Async Python web framework
- **[LangChain](https://python.langchain.com/)** — LLM orchestration, conversation memory, and chains
- **[OpenRouter API](https://openrouter.ai/)** — LLM gateway supporting GPT-4o-mini & GPT-4o
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** — Async ORM with `asyncpg` driver
- **[Alembic](https://alembic.sqlalchemy.org/)** — Database schema migration management
- **[FAISS](https://faiss.ai/)** — Vector similarity search for anti-repetition
- **[Redis](https://redis.io/)** — Session caching and rate-limit state
- **[MediaPipe](https://mediapipe.dev/)** — Face detection for proctoring
- **[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — Type-safe, env-driven configuration
- **[structlog](https://www.structlog.org/)** — Structured, production-grade logging
- **[SlowAPI](https://slowapi.readthedocs.io/)** — Rate limiting middleware for FastAPI

### Frontend
- **Vanilla JavaScript (ES Modules)** — Zero-framework SPA with hash-based routing
- **[Vite 5](https://vitejs.dev/)** — Lightning-fast dev server and production bundler
- **Custom CSS Design System** — Dark-mode UI with gold accent palette and glassmorphism effects

### Infrastructure
- **[PostgreSQL 16](https://www.postgresql.org/)** — Primary relational database
- **[Redis 7](https://redis.io/)** — Cache and session store
- **[Docker & Docker Compose](https://docs.docker.com/)** — Containerised service orchestration
- **[Nginx](https://nginx.org/)** — Reverse proxy for production deployments

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│             Vite SPA  (http://localhost:5173)                    │
│     Login · Dashboard · Interview · Coding · Analytics          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / REST  (JWT Bearer Token)
┌──────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Backend                             │
│                   (http://localhost:8000)                        │
│                                                                  │
│  /api/v1/auth       → JWT auth (register / login / refresh)     │
│  /api/v1/resume     → PDF upload & AI resume parsing            │
│  /api/v1/interview  → Question gen · chat loop · summary        │
│  /api/v1/coding     → Challenge CRUD + sandbox code execution   │
│  /api/v1/voice      → STT / TTS endpoints                       │
│  /api/v1/proctor    → Proctoring event log + risk scoring       │
│  /api/v1/analytics  → Recruiter & platform-wide analytics       │
│  /health            → Database + Redis health check             │
└────────┬────────────────────────────────┬────────────────────────┘
         │                                │
┌────────▼────────┐             ┌─────────▼──────────┐
│   PostgreSQL    │             │       Redis         │
│  (port 5433)    │             │    (port 6379)      │
│                 │             │                     │
│  users          │             │  session cache      │
│  resumes        │             │  rate-limit state   │
│  interviews     │             └─────────────────────┘
│  questions      │
│  answers        │             ┌─────────────────────┐
│  coding_sub..   │             │   OpenRouter API     │
│  proctor_logs   │             │  GPT-4o / GPT-4o-mini│
│  audit_logs     │             └─────────────────────┘
└─────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker Desktop | Latest |
| Git | Any |

### 1. Clone the Repository

```bash
git clone https://github.com/Ranjith01111/AI-Interview-Assistant.git
cd AI-Interview-Assistant
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Open `.env` and set your values:

```env
# Required — get your free key at https://openrouter.ai/
OPENROUTER_API_KEY=sk-or-v1-...

# PostgreSQL — Docker manages this automatically
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/interview_assistant

# Redis — Docker manages this automatically
REDIS_URL=redis://localhost:6379/0

# Security — generate strong secrets:
# python scripts/generate_secrets.py
SECRET_KEY=your-64-char-hex-secret
JWT_SECRET_KEY=your-128-char-hex-secret
```

### 3. Start Infrastructure (PostgreSQL + Redis)

```bash
# Make sure Docker Desktop is running first
docker compose up -d postgres redis

# Verify both containers are healthy
docker ps
```

### 4. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate — Windows
.\venv\Scripts\activate

# Activate — Mac / Linux
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### 5. Start the Backend

```bash
python run_backend.py
```

> The backend auto-creates all database tables on first launch. No manual migration steps needed in development.

### 6. Start the Frontend

```bash
# In a new terminal window:
python run_frontend.py

# Or run directly with npm:
cd frontend && npm install && npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

### ⚡ One-Click Start (Windows)

```powershell
.\start.ps1
```

Automatically starts Docker Desktop, waits for health checks, then launches backend and frontend in separate terminal windows.

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | — | OpenRouter API key for LLM access |
| `OPENROUTER_MODEL` | ❌ | `openai/gpt-4o-mini` | Model for question & feedback generation |
| `AGENT_MODEL` | ❌ | `openai/gpt-4o` | Model for the interview agent |
| `DATABASE_URL` | ✅ | — | PostgreSQL async connection string |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` | Redis connection URL |
| `SECRET_KEY` | ✅ | — | App secret key (64 hex chars minimum) |
| `JWT_SECRET_KEY` | ✅ | — | JWT signing key (128 hex chars minimum) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `1440` | Access token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | Refresh token lifetime in days |
| `DEBUG` | ❌ | `true` | Enable debug mode (disables production secret validation) |
| `ALLOWED_ORIGINS` | ❌ | `localhost:5173,8501,3000` | Comma-separated CORS allowed origins |
| `RATE_LIMIT_DEFAULT` | ❌ | `60/minute` | Default API rate limit |
| `RATE_LIMIT_AUTH` | ❌ | `10/minute` | Auth endpoint rate limit |
| `AGENT_TEMPERATURE` | ❌ | `0.4` | LLM temperature (creativity) |
| `PROCTOR_FACE_MATCH_THRESHOLD` | ❌ | `0.78` | Face detection confidence threshold |
| `FAISS_INDEX_PATH` | ❌ | `./data/faiss_index` | Path for FAISS vector store |

> 💡 **Generate secure secrets instantly:**
> ```bash
> python scripts/generate_secrets.py
> ```

---

## 📡 API Reference

Full interactive documentation is available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Endpoint Overview

```
# Authentication
POST   /api/v1/auth/register              Create a new user account
POST   /api/v1/auth/login                 Authenticate and receive JWT tokens
POST   /api/v1/auth/refresh               Refresh an expired access token

# Resume
POST   /api/v1/resume/upload              Upload a PDF resume (initiates a session)

# Interview
POST   /api/v1/interview/generate-questions/{session_id}   Generate tailored questions
POST   /api/v1/interview/start/{session_id}                Start the interview session
POST   /api/v1/interview/chat                              Send answer, receive feedback
GET    /api/v1/interview/summary/{session_id}              Get final scored report

# Coding Assessment
GET    /api/v1/coding/challenges           List available coding challenges
POST   /api/v1/coding/run                  Execute candidate code against test cases
POST   /api/v1/coding/submit              Submit final solution for scoring

# Voice
POST   /api/v1/voice/transcribe            Convert audio to text (STT)
POST   /api/v1/voice/synthesize            Convert text to audio (TTS)

# Proctoring
POST   /api/v1/proctor/log-event           Record a proctoring event
GET    /api/v1/proctor/risk/{session_id}   Retrieve risk score for a session

# Analytics
GET    /api/v1/analytics/platform          Platform-wide aggregated metrics
GET    /api/v1/analytics/sessions          All sessions (recruiter-only view)

# Health
GET    /health                             Returns DB + Redis connectivity status
```

---

## 📁 Project Structure

```
AI-Interview-Assistant/
├── backend/
│   ├── core/                    # Config, security, logging, middleware, rate limiter
│   │   ├── config.py            # Pydantic-settings with full env validation
│   │   ├── security.py          # JWT auth, bcrypt hashing, CORS setup
│   │   ├── middleware.py        # Request logging + security headers middleware
│   │   ├── logging.py           # structlog configuration
│   │   └── rate_limiter.py      # SlowAPI limiter singleton
│   ├── db/                      # Database layer
│   │   ├── session.py           # Async SQLAlchemy engine + session factory
│   │   ├── redis.py             # Redis connection pool
│   │   ├── base.py              # Declarative base model
│   │   └── auto_migrate.py      # Dev-mode auto schema migration
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py              # User accounts and roles
│   │   ├── interview.py         # Interview sessions
│   │   ├── question.py          # Generated questions
│   │   ├── answer.py            # Candidate answers with scores
│   │   ├── resume.py            # Parsed resume data
│   │   ├── coding_challenge.py  # Coding challenge definitions
│   │   ├── coding_submission.py # Code submission results
│   │   ├── proctor_log.py       # Proctoring event log
│   │   ├── audit_log.py         # System audit trail
│   │   └── analytics.py         # Analytics aggregation models
│   ├── routes/                  # FastAPI API routers
│   │   ├── auth_routes.py       # /api/v1/auth
│   │   ├── interview_routes.py  # /api/v1/interview
│   │   ├── resume_routes.py     # /api/v1/resume
│   │   ├── coding_routes.py     # /api/v1/coding
│   │   ├── voice_routes.py      # /api/v1/voice
│   │   ├── proctor_routes.py    # /api/v1/proctor
│   │   ├── analytics_routes.py  # /api/v1/analytics
│   │   ├── health_routes.py     # /health
│   │   └── tts_routes.py        # Text-to-speech
│   ├── services/                # Business logic layer
│   │   ├── interview_agent.py   # LangChain GPT-4o interview agent
│   │   ├── sandbox_service.py   # Code execution engine (cross-platform)
│   │   ├── auth_service.py      # Registration, login, token management
│   │   ├── proctor_service.py   # Risk scoring and event handling
│   │   ├── session_service.py   # Session state management (Redis)
│   │   ├── context_engine.py    # Resume context extraction for questions
│   │   ├── anti_repetition.py   # FAISS-based question deduplication
│   │   ├── prompt_templates.py  # LLM prompt library
│   │   └── voice_service.py     # STT / TTS processing
│   ├── nlp_engine/              # NLP processing modules
│   │   ├── question_generator.py
│   │   ├── feedback_generator.py
│   │   ├── answer_evaluator.py
│   │   └── resume_parser.py
│   ├── alembic/                 # Production database migrations
│   │   └── versions/            # 6 versioned migration scripts
│   ├── seed_challenges.py       # Default coding challenge seeder
│   └── main.py                  # FastAPI app entry point + lifespan
├── frontend/
│   └── src/
│       ├── api/                 # HTTP client and request helpers
│       ├── components/          # Reusable UI components
│       │   ├── Navbar.js
│       │   ├── ProctorMonitor.js
│       │   ├── Toast.js
│       │   └── VoiceConsole.js
│       ├── pages/               # Page-level renderers
│       │   ├── LoginPage.js
│       │   ├── CandidateDashboard.js
│       │   ├── InterviewFlow.js
│       │   ├── RecruiterDashboard.js
│       │   ├── AnalyticsDashboard.js
│       │   ├── VoiceInterview.js
│       │   └── steps/           # Multi-step interview panels
│       └── styles/              # CSS design system (dark mode + gold palette)
├── scripts/
│   ├── generate_secrets.py      # Secure secret key generator
│   └── init-db.sql              # Manual DB initialisation script
├── docker-compose.yml           # Development: PostgreSQL + Redis
├── docker-compose.prod.yml      # Production: full stack deployment
├── requirements.txt             # Python dependencies
├── run_backend.py               # Backend convenience launcher
├── run_frontend.py              # Frontend convenience launcher
├── start.ps1                    # Windows one-click startup script
└── .env.example                 # Environment configuration template
```

---

## 🧪 Testing & Diagnostics

```bash
# Verify database and Redis connectivity
python diagnose.py

# Test sandbox code execution engine
python test_sandbox.py

# Test voice processing pipeline
python test_voice.py

# Test proctoring system
python test_proctor.py
```

---

## 🐳 Deployment

### Development (recommended)

```bash
# Start only DB + Redis in Docker; run app locally
docker compose up -d postgres redis
python run_backend.py
```

### Full Production Stack

```bash
# Set all secrets in .env first, then:
docker compose -f docker-compose.prod.yml up -d
```

---

## 🔐 Security

- All API routes (except `/health` and `/api/v1/auth/*`) require a valid **JWT Bearer token**
- Passwords hashed with **bcrypt** (cost factor 12)
- Rate limiting enforced at both auth (10 req/min) and general (60 req/min) tiers
- CORS restricted to explicitly configured origins only
- Security response headers applied globally: `CSP`, `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`
- In production mode (`DEBUG=false`), startup validation rejects any placeholder or weak secret values

---

## 🤝 Contributing

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes with a conventional commit message
4. Push the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request against `main`

### Commit Convention

```
feat:      New feature
fix:       Bug fix
docs:      Documentation changes only
refactor:  Code refactoring without behaviour change
perf:      Performance improvements
test:      Adding or updating tests
chore:     Build process or tooling changes
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Built with ❤️ using **FastAPI · LangChain · GPT-4o · PostgreSQL · Redis · Vite**

**[⭐ Star this repo if you find it useful!](https://github.com/Ranjith01111/AI-Interview-Assistant)**

</div>
