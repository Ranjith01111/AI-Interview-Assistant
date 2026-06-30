# 🤖 AI Interview Assistant

<div align="center">

![Version](https://img.shields.io/badge/version-2.1.0-gold?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

**An enterprise-grade, AI-powered mock interview platform with real-time proctoring, voice interviews, coding assessments, and recruiter analytics — fully self-contained with a custom NLP engine.**

[Features](#-features) · [Architecture](#️-architecture) · [Quick Start](#-quick-start) · [API Docs](#-api-reference) · [Project Structure](#-project-structure)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [AI & NLP Engine](#-ai--nlp-engine)
- [Tech Stack](#️-tech-stack)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## 🌟 Overview

**AI Interview Assistant** is a full-stack, production-ready mock interview platform that uses a **custom-built NLP engine** to simulate realistic technical interviews. Candidates upload their resume, the system parses it to generate tailored questions, then conducts a conversational interview with real-time feedback, scoring, and a comprehensive final report.

### Key Differentiator: **Zero External API Dependency**

Unlike typical AI interview tools that rely on expensive cloud APIs (OpenAI, Anthropic, etc.), this platform runs **100% offline** with:
- ✅ No API keys required
- ✅ Zero cost per interview
- ✅ Complete data privacy (everything stays local)
- ✅ Instant response times (no network latency)
- ✅ Works without internet

The platform supports **text interviews**, **voice interviews**, **live coding assessments**, and **AI-driven proctoring** — suitable for both individual candidate practice and enterprise recruitment pipelines.

### 🚀 Recent Updates (v2.2.0)
- **Coding Sandbox Enhancements**: Stabilized cross-platform code execution for Python, JavaScript, C++, and Java. Fixed `asyncio` subprocess compatibility issues on Windows and improved compiler fallback logic.
- **Backend Resilience Framework**: Implemented robust HTTP 500 defenses including global payload sniffing, strict 15-second database timeouts, exponential backoff for external service calls, and Redis-based mutex locks to prevent race conditions.
- **Streamlined Interview Flow**: Unified text and coding assessments into a seamless progression with automated transitions, enforced full-screen proctoring, and comprehensive dual-score final reports.
- **Recruiter Registration Fixed**: Resolved backend schema and validation logic issues preventing recruiter sign-ups.

---

## ✨ Features

### 🎯 Candidate Experience

| Feature | Description |
|---|---|
| **Resume Upload & Parsing** | Upload PDF resumes; NLP extracts skills, projects, and experience using 80+ regex patterns across 14 skill categories |
| **AI-Powered Interviews** | Custom NLP agent conducts interviews with context-aware question selection based on resume analysis |
| **Voice Interviews** | Full speech-to-text and text-to-speech interview mode using browser-native Web Speech API (no cloud STT/TTS) |
| **Live Coding Assessments** | In-browser code editor with multi-language sandbox execution (Python, JavaScript, C++, Java, SQL) |
| **Real-Time Feedback** | Instant per-answer scoring using TF-IDF + keyword matching with strengths, weaknesses, and improvements |
| **Interview Summary** | Detailed final report with overall score, per-question breakdown, and hiring recommendation |

### 🛡️ Proctoring & Integrity

| Feature | Description |
|---|---|
| **Face Detection** | WebRTC camera monitoring with frame capture every 15 seconds |
| **Fullscreen Enforcement** | Mandatory fullscreen mode; exiting (Esc) auto-terminates the session |
| **Tab Switch Detection** | `visibilitychange` event listener flags focus-loss in real time |
| **Voice Detection** | Web Audio API frequency analysis detects speaking (3 violations = auto-terminate) |
| **Copy Prevention** | Clipboard events blocked during proctored sessions |
| **Draggable Camera Widget** | Minimizable, repositionable proctor monitor overlay |

### 👩‍💼 Recruiter & Admin Tools

| Feature | Description |
|---|---|
| **Recruiter Dashboard** | View all candidate sessions, scores, and full interview summaries |
| **Analytics Dashboard** | Platform-wide metrics — completion rates, score distributions, skill frequency |
| **Role-Based Access Control** | Separate flows for `candidate`, `recruiter`, and `admin` roles enforced via JWT |
| **Audit Trails** | Structured logging of all API actions via structlog |

### 👤 User Roles & Access

The platform supports three roles with separate UIs and permissions:

| Role | Access | Dashboard |
|------|--------|-----------|
| **Candidate** | Take interviews, view own scores, upload resume | `/dashboard` — My Interviews (KPIs + session history) |
| **Recruiter** | View all candidates, review scores, deactivate users, analytics | `/recruiter` — Candidate Management table + session list |
| **Admin** | Full platform control + user management | `/recruiter` + all admin API endpoints |

#### How to Register as Recruiter

On the **Register** page, select the **role** field:
- `candidate` — default (takes interviews)
- `recruiter` — reviews candidates (no interview access)
- `admin` — full control

Or via API:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "HR Manager", "email": "hr@company.com", "password": "SecurePass123!", "role": "recruiter"}'
```

### ⚙️ Platform & Infrastructure

| Feature | Description |
|---|---|
| **JWT Authentication** | Secure access + refresh token flow with configurable expiry |
| **Rate Limiting** | Per-endpoint rate limiting via SlowAPI (60 req/min default, 10/min on auth) |
| **Auto-Migration** | Schema migrations run automatically on startup — no manual steps needed |
| **Question Anti-Repetition** | Category-balanced selection algorithm ensures variety across sessions |
| **Structured Logging** | JSON-structured logs via structlog with full request tracing |
| **Docker-First Infra** | PostgreSQL and Redis run in isolated, health-checked Docker containers |

---

## 🧠 AI & NLP Engine

### Architecture: Rule-Based NLP + Statistical Scoring

The system uses a **custom-built NLP engine** (`backend/nlp_engine/`) with 6 modules:

| Module | Algorithm | Purpose |
|--------|-----------|---------|
| `resume_parser.py` | Regex + Keyword Matching (80+ patterns) | Extract skills, experience, projects from PDF resumes |
| `question_bank.py` | Curated Template Database | **500 questions** across 14 categories |
| `question_generator.py` | Weighted Random Selection + Difficulty Calibration | Select relevant questions based on skills & experience |
| `answer_evaluator.py` | **TF-IDF + Cosine Similarity + Keyword Matching** | Score answers (0-10) with detailed breakdown |
| `feedback_generator.py` | Rule-Based Template System | Generate per-question and final summary feedback |
| `interview_agent.py` | **Finite State Machine** | Manage interview flow, track state, provide responses |

### Scoring Formula

```
Per-Question Score (0-10):
  = (keyword_match_score × 0.6) + (tfidf_cosine_similarity × 10 × 0.4)

Final Score = average(all_question_scores)

Recommendation:
  ≥ 8.0 → "Strong Hire"
  ≥ 6.5 → "Hire"  
  ≥ 5.0 → "Maybe — needs improvement"
  < 5.0 → "No Hire"
```

### Question Bank Statistics

| Category | Count | Topics |
|----------|-------|--------|
| Python | 50 | OOP, generators, decorators, async, memory management |
| JavaScript | 50 | Closures, prototypes, event loop, ES6+, promises |
| React | 35 | Hooks, lifecycle, state management, performance |
| SQL | 35 | Joins, indexes, normalization, query optimization |
| AWS/Cloud | 30 | EC2, S3, Lambda, VPC, IAM, architecture patterns |
| Docker/DevOps | 30 | Containers, CI/CD, orchestration, networking |
| Machine Learning | 30 | Algorithms, metrics, feature engineering, deployment |
| System Design | 40 | Scalability, caching, load balancing, microservices |
| DSA | 40 | Arrays, trees, graphs, DP, sorting, searching |
| API Design | 25 | REST, GraphQL, versioning, authentication |
| Git | 20 | Branching, merging, rebasing, workflows |
| Testing | 25 | Unit, integration, TDD, mocking, coverage |
| Security | 25 | OWASP, encryption, auth patterns, vulnerabilities |
| Behavioral/HR | 65 | STAR method, leadership, conflict, motivation |
| **TOTAL** | **500** | |

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|-----------|---------|
| **[FastAPI](https://fastapi.tiangolo.com/)** | Async Python web framework |
| **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** | Async ORM with `asyncpg` driver |
| **[Pydantic v2](https://docs.pydantic.dev/)** | Request/response validation & settings |
| **[Redis](https://redis.io/)** | Session caching, agent state, rate-limit state |
| **[PostgreSQL 16](https://www.postgresql.org/)** | Relational data store (11 tables) |
| **[structlog](https://www.structlog.org/)** | Structured, production-grade logging |
| **[SlowAPI](https://slowapi.readthedocs.io/)** | Rate limiting middleware |
| **[bcrypt](https://github.com/pyca/bcrypt)** | Password hashing (cost factor 12) |
| **[PyJWT](https://pyjwt.readthedocs.io/)** | JWT token generation & verification |
| **[pdfplumber](https://github.com/jsvine/pdfplumber)** | PDF text extraction |
| **Custom NLP Engine** | TF-IDF scoring, keyword matching, resume parsing |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Vanilla JavaScript (ES Modules)** | Zero-framework SPA with hash-based routing |
| **[Vite 5](https://vitejs.dev/)** | Lightning-fast dev server and production bundler |
| **Web Speech API** | Browser-native STT (SpeechRecognition) & TTS (SpeechSynthesis) |
| **Web Audio API** | Voice detection for proctoring |
| **WebRTC (getUserMedia)** | Camera access for face monitoring |
| **Custom CSS Design System** | Dark-mode UI with gold (#f5b800) accent palette |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| **[PostgreSQL 16](https://www.postgresql.org/)** | Primary relational database |
| **[Redis 7](https://redis.io/)** | Cache and session store |
| **[Docker & Docker Compose](https://docs.docker.com/)** | Containerised service orchestration |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Client Browser                             │
│                 Vite SPA (http://localhost:5173)                  │
│                                                                  │
│   ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌────────────────┐  │
│   │  Login  │  │Dashboard │  │Interview│  │ Voice Interview│  │
│   │  Page   │  │(KPIs +   │  │(Text +  │  │ (Speech API +  │  │
│   │         │  │ Sessions)│  │ Proctor)│  │  NLP Backend)  │  │
│   └────┬────┘  └────┬─────┘  └────┬────┘  └───────┬────────┘  │
│        └─────────────┼─────────────┼───────────────┘            │
│                      │ REST API (JWT Bearer Auth)                │
└──────────────────────┼──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                  FastAPI Backend (localhost:8000)                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      Routes Layer                           │ │
│  │  /auth  /resume  /interview  /voice  /proctor  /coding     │ │
│  │  /analytics  /health                                        │ │
│  └───────────────────────────┬────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼────────────────────────────────┐ │
│  │                   Services Layer                            │ │
│  │  interview_agent (State Machine)                            │ │
│  │  question_service · resume_service · session_service        │ │
│  │  auth_service · proctor_service · sandbox_service           │ │
│  └───────────────────────────┬────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼────────────────────────────────┐ │
│  │           NLP Engine (100% Local, No APIs)                  │ │
│  │                                                             │ │
│  │  ┌──────────────┐  ┌─────────────────┐  ┌──────────────┐  │ │
│  │  │Resume Parser │  │ Question Bank   │  │  Answer      │  │ │
│  │  │80+ patterns  │  │ 500 questions   │  │  Evaluator   │  │ │
│  │  │14 categories │  │ 14 categories   │  │  TF-IDF +    │  │ │
│  │  │              │  │ 3 difficulties  │  │  Cosine Sim  │  │ │
│  │  └──────────────┘  └─────────────────┘  └──────────────┘  │ │
│  │  ┌──────────────────┐  ┌─────────────────────────────────┐│ │
│  │  │Question Generator│  │ Feedback Generator              ││ │
│  │  │Weighted selection│  │ Template-based scoring report    ││ │
│  │  │Difficulty calib. │  │ Strengths + improvements        ││ │
│  │  └──────────────────┘  └─────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────────┘ │
└────────┬───────────────────────────────────┬────────────────────┘
         │                                   │
┌────────▼────────────┐            ┌────────▼────────────┐
│    PostgreSQL        │            │       Redis          │
│   (port 5433)        │            │    (port 6379)       │
│                      │            │                      │
│  11 tables:          │            │  Stores:             │
│  • users             │            │  • session metadata  │
│  • interview_sessions│            │  • questions cache   │
│  • questions         │            │  • agent state       │
│  • answers           │            │  • interview state   │
│  • proctor_logs      │            │  • rate-limit keys   │
│  • analytics         │            │  • parsed resumes    │
│  • audit_logs        │            │                      │
│  • resumes           │            │                      │
│  • coding_challenges │            │                      │
│  • coding_submissions│            │                      │
│  • question_embeddings│           │                      │
└──────────────────────┘            └──────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker Desktop | Latest (for PostgreSQL + Redis) |
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
# PostgreSQL — Docker manages this automatically
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/interview_assistant

# Redis — Docker manages this automatically
REDIS_URL=redis://localhost:6379/0

# Security — generate strong secrets:
# python scripts/generate_secrets.py
SECRET_KEY=your-64-char-hex-secret
JWT_SECRET_KEY=your-128-char-hex-secret

# NLP Engine (no API keys needed!)
USE_LOCAL_NLP=true
OPENROUTER_API_KEY=          # Leave empty — not needed
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

> The backend auto-creates all database tables and runs migrations on first launch. No manual migration steps needed.

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
| `DATABASE_URL` | ✅ | — | PostgreSQL async connection string |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` | Redis connection URL |
| `SECRET_KEY` | ✅ | — | App secret key (64 hex chars minimum) |
| `JWT_SECRET_KEY` | ✅ | — | JWT signing key (128 hex chars minimum) |
| `USE_LOCAL_NLP` | ❌ | `true` | Use local NLP engine (no external APIs) |
| `OPENROUTER_API_KEY` | ❌ | `""` | Optional — leave empty for offline mode |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `1440` | Access token lifetime in minutes |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | ❌ | `7` | Refresh token lifetime in days |
| `DEBUG` | ❌ | `true` | Enable debug mode |
| `ALLOWED_ORIGINS` | ❌ | `localhost:5173,8501,3000` | Comma-separated CORS origins |
| `RATE_LIMIT_DEFAULT` | ❌ | `60/minute` | Default API rate limit |
| `RATE_LIMIT_AUTH` | ❌ | `10/minute` | Auth endpoint rate limit |
| `AGENT_MAX_FOLLOW_UPS` | ❌ | `0` | Number of follow-up questions (0 = disabled) |
| `AGENT_TEMPERATURE` | ❌ | `0.4` | NLP scoring sensitivity |

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
GET    /api/v1/auth/me                    Get current user profile

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
GET    /api/v1/tts/speak                   Text-to-speech audio generation

# Proctoring
POST   /api/v1/proctor/analyze-frame       Analyze webcam frame for violations
POST   /api/v1/proctor/log-event           Record a proctoring event
GET    /api/v1/proctor/session-report/{session_id}   Get proctoring report

# Analytics
GET    /api/v1/analytics/overview          Platform KPIs (total, avg score, pass rate)
GET    /api/v1/analytics/history           Session history with scores
GET    /api/v1/analytics/skills            Skill frequency analysis
GET    /api/v1/analytics/strengths-weaknesses   Aggregated strengths/improvements
GET    /api/v1/analytics/performance-trend      Score trend over time

# Health
GET    /health                             Returns DB + Redis connectivity status
```

---

## 📁 Project Structure

```
AI-Interview-Assistant/
├── backend/
│   ├── core/                    # Config, security, logging, middleware
│   │   ├── config.py            # Pydantic-settings with env validation
│   │   ├── security.py          # JWT auth, bcrypt, CORS, RBAC
│   │   ├── middleware.py        # Request logging + security headers
│   │   ├── logging.py           # structlog configuration
│   │   └── rate_limiter.py      # SlowAPI limiter singleton
│   ├── db/                      # Database layer
│   │   ├── session.py           # Async SQLAlchemy engine + session factory
│   │   ├── redis.py             # Redis connection pool
│   │   ├── base.py              # Declarative base + mixins
│   │   └── auto_migrate.py      # Auto-adds missing columns on startup
│   ├── models/                  # SQLAlchemy ORM models + Pydantic schemas
│   │   ├── user.py              # User accounts and roles
│   │   ├── interview.py         # Interview sessions
│   │   ├── question.py          # Generated questions
│   │   ├── answer.py            # Candidate answers with scores
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── proctor_log.py       # Proctoring event log
│   │   ├── analytics.py         # Analytics aggregation
│   │   ├── coding_challenge.py  # Coding challenge definitions
│   │   └── coding_submission.py # Code submission results
│   ├── routes/                  # FastAPI API routers
│   │   ├── auth_routes.py       # /api/v1/auth
│   │   ├── interview_routes.py  # /api/v1/interview
│   │   ├── resume_routes.py     # /api/v1/resume
│   │   ├── coding_routes.py     # /api/v1/coding
│   │   ├── voice_routes.py      # /api/v1/voice
│   │   ├── proctor_routes.py    # /api/v1/proctor
│   │   ├── analytics_routes.py  # /api/v1/analytics
│   │   └── health_routes.py     # /health
│   ├── services/                # Business logic layer
│   │   ├── interview_agent.py   # State-machine interview conductor
│   │   ├── question_service.py  # Question generation orchestrator
│   │   ├── interview_service.py # Interview flow manager
│   │   ├── resume_service.py    # Resume upload + parse pipeline
│   │   ├── session_service.py   # Redis session state management
│   │   ├── auth_service.py      # Registration, login, tokens
│   │   ├── context_engine.py    # Project-context question generation
│   │   └── audit_service.py     # Console-based audit logging
│   ├── nlp_engine/              # 🧠 Custom NLP Engine (NO external APIs)
│   │   ├── __init__.py          # Package exports
│   │   ├── resume_parser.py     # Regex-based resume extraction (80+ patterns)
│   │   ├── question_bank.py     # 500 questions × 14 categories × 3 difficulties
│   │   ├── question_generator.py # Skill-based selection with calibration
│   │   ├── answer_evaluator.py  # TF-IDF + keyword scoring engine
│   │   └── feedback_generator.py # Template-based feedback generation
│   ├── alembic/                 # Production database migrations
│   └── main.py                  # FastAPI app entry point + lifespan
├── frontend/
│   └── src/
│       ├── api/                 # HTTP client + request helpers
│       │   ├── client.js        # Fetch wrapper with JWT refresh
│       │   └── index.js         # API module exports
│       ├── components/          # Reusable UI components
│       │   ├── Navbar.js        # Top navigation with user menu
│       │   ├── ProctorMonitor.js # Draggable webcam + fullscreen + violations
│       │   ├── VoiceConsole.js  # Speech recognition console
│       │   ├── Sidebar.js       # Navigation sidebar
│       │   └── Toast.js         # Notification toasts
│       ├── pages/               # Page-level renderers
│       │   ├── LoginPage.js     # Auth (login + register)
│       │   ├── CandidateDashboard.js  # KPIs + session history
│       │   ├── InterviewFlow.js       # Multi-step interview controller
│       │   ├── VoiceInterview.js      # Standalone voice HR interview
│       │   ├── RecruiterDashboard.js  # Admin view of all sessions
│       │   ├── AnalyticsDashboard.js  # Platform analytics
│       │   └── steps/                 # Interview step panels
│       │       ├── Step1Upload.js     # Resume upload
│       │       ├── Step2Questions.js  # Question generation
│       │       ├── Step3Interview.js  # Text/voice chat (proctored)
│       │       ├── Step4Coding.js     # Live coding assessment
│       │       └── Step5Summary.js    # Final report
│       └── styles/              # CSS design system
│           ├── main.css         # Design tokens (dark + gold theme)
│           ├── auth.css         # Login/register styles
│           ├── components.css   # Component styles
│           ├── interview.css    # Interview panel styles
│           └── dashboard.css    # Dashboard & analytics styles
├── scripts/
│   ├── migrate_add_missing_columns.sql  # Manual DB migration
│   └── generate_secrets.py              # Secure secret key generator
├── docker-compose.yml           # Development: PostgreSQL + Redis
├── docker-compose.prod.yml      # Production: full stack
├── requirements.txt             # Python dependencies
├── run_backend.py               # Backend launcher
├── run_frontend.py              # Frontend launcher
├── start.ps1                    # Windows one-click startup
├── cleanup.ps1                  # Clear cache + Redis
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── .dockerignore                # Docker build exclusions
├── TECHNICAL_REPORT.md          # Detailed AI/algorithm documentation
└── ISSUES_REPORT.md             # Bug fix history
```

---

## 🔒 Security

| Layer | Implementation |
|-------|---------------|
| Authentication | JWT access + refresh tokens (configurable expiry) |
| Password Storage | bcrypt (cost factor 12) |
| Rate Limiting | SlowAPI — 60/min general, 10/min auth |
| CORS | Whitelist-based origin control |
| Security Headers | CSP, X-Frame-Options, X-Content-Type-Options, HSTS |
| Input Validation | Pydantic v2 strict schemas on all endpoints |
| Session Isolation | UUID-based session IDs, Redis-scoped data |
| Proctoring | Fullscreen enforcement + camera + audio + tab monitoring |

---

## 🧪 Diagnostics

```bash
# Verify database and Redis connectivity
python diagnose.py

# Clean all cached bytecode + Redis
.\cleanup.ps1
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

Built with ❤️ using **FastAPI · Custom NLP Engine · TF-IDF · PostgreSQL · Redis · Vite**

**Fully offline. Zero cost. Complete privacy.**

**[⭐ Star this repo if you find it useful!](https://github.com/Ranjith01111/AI-Interview-Assistant)**

</div>
