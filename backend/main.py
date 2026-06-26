"""
FastAPI Main Application Entry Point — Production v2.0

AI Interview Assistant Backend
================================
Features:
  • PostgreSQL (async) for persistent storage
  • Redis for session caching
  • Alembic for database migrations
  • Structured logging via structlog
  • CORS & security middleware
  • Health checks for DB + Redis

Endpoints:
  POST /api/v1/resume/upload                            - Upload PDF resume
  POST /api/v1/interview/generate-questions/{session_id} - Generate interview questions
  POST /api/v1/interview/start/{session_id}              - Start the interview
  POST /api/v1/interview/chat                            - Send answer, get feedback
  GET  /api/v1/interview/summary/{session_id}            - Get final summary
  GET  /health                                           - Health check (DB + Redis)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.security import configure_cors
from backend.core.logging import setup_logging, get_logger
from backend.db.session import init_db, close_db, async_engine
from backend.db.redis import init_redis, close_redis
from backend.db.auto_migrate import run_auto_migration
from backend.seed_challenges import seed_default_challenges
from backend.core.rate_limiter import limiter
from backend.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware
from backend.routes.resume_routes import router as resume_router
from backend.routes.interview_routes import router as interview_router
from backend.routes.health_routes import router as health_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.voice_routes import router as voice_router
from backend.routes.proctor_routes import router as proctor_router
from backend.routes.coding_routes import router as coding_router
from backend.routes.analytics_routes import router as analytics_router
from backend.routes.tts_routes import router as tts_router


# ── Structured logger ────────────────────────────────────────────────
logger = get_logger("backend.main")


# ============================================
# Application Lifecycle (startup / shutdown)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once on startup and once on shutdown.

    Startup:
      1. Configure structured logging
      2. Initialize PostgreSQL connection pool
      3. Initialize Redis connection pool
      4. Auto-create tables in dev mode (Alembic in production)

    Shutdown:
      1. Close Redis pool
      2. Close PostgreSQL pool
    """
    # ── STARTUP ──────────────────────────────────────────────────────
    setup_logging()
    logger.info(
        "starting_application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    # Initialize database
    logger.info("connecting_to_database", url=settings.DATABASE_URL.split("@")[-1])
    # Import all models so Base.metadata knows about all tables
    import backend.models  # noqa: F401 — registers all ORM models with Base

    await init_db()  # Auto-create tables if they don't exist
    await run_auto_migration(async_engine)  # Ensure all columns exist

    # Seed default coding challenges
    from backend.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        added = await seed_default_challenges(db)
        if added:
            logger.info("seeded_coding_challenges", count=added)

    logger.info("database_connected")

    # Initialize Redis
    logger.info("connecting_to_redis", url=settings.REDIS_URL)
    await init_redis()
    logger.info("redis_connected")

    logger.info(
        "application_ready",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        model=settings.OPENROUTER_MODEL,
    )

    yield  # ← Application runs here

    # ── SHUTDOWN ─────────────────────────────────────────────────────
    logger.info("shutting_down")
    await close_redis()
    await close_db()
    logger.info("shutdown_complete")


# ============================================
# Create FastAPI application
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI-powered mock interview system with resume analysis, "
                "real-time feedback, and scoring — backed by PostgreSQL + Redis.",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Wire Rate Limiter ────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ============================================
# Middleware
# ============================================
# RequestLoggingMiddleware logs incoming requests and processing times
app.add_middleware(RequestLoggingMiddleware)
# SecurityHeadersMiddleware applies essential security headers (CSP, XSS, Frame Options, nosniff, etc.)
app.add_middleware(SecurityHeadersMiddleware)
# CORS configuration
configure_cors(app)


# ============================================
# Register Routers
# ============================================
app.include_router(auth_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")
app.include_router(voice_router, prefix="/api/v1")
app.include_router(proctor_router, prefix="/api/v1")
app.include_router(coding_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(tts_router, prefix="/api/v1")
app.include_router(health_router)


# ============================================
# Root Endpoint
# ============================================
@app.get("/")
async def root():
    """Root endpoint — shows API info"""
    return {
        "message": "🚀 AI Interview Assistant API is running!",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "stack": {
            "framework": "FastAPI",
            "database": "PostgreSQL",
            "cache": "Redis",
            "ai": settings.OPENROUTER_MODEL,
        },
    }


# ============================================
# Run the server (for direct execution)
# ============================================
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting AI Interview Assistant Backend v2.0...")
    print(f"   → Model: {settings.OPENROUTER_MODEL}")
    print(f"   → Database: PostgreSQL")
    print(f"   → Cache: Redis")
    print(f"   → Running at: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"   → API Docs: http://localhost:{settings.BACKEND_PORT}/docs")

    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
