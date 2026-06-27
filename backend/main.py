"""
FastAPI Main Application Entry Point — Production v2.1 (Resilient)

AI Interview Assistant Backend
================================
RESILIENCE FEATURES:
  • All route imports are try/except wrapped — app starts even if some fail
  • Redis is optional — app runs without caching if Redis is down
  • Database init failures are caught and logged (not crash)
  • Global exception handler prevents raw 500 tracebacks to client
  • Health endpoint always works regardless of DB/Redis state
"""

from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.security import configure_cors
from backend.core.logging import setup_logging, get_logger
from backend.db.session import init_db, close_db, async_engine
from backend.db.redis import init_redis, close_redis
from backend.core.rate_limiter import limiter
from backend.core.middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware, RequestBodySizeLimitMiddleware


# ── Structured logger ────────────────────────────────────────────────────────
logger = get_logger("backend.main")


# ══════════════════════════════════════════════════════════════════════════════
# SAFE ROUTE IMPORTS — App starts even if some routes fail to import
# ══════════════════════════════════════════════════════════════════════════════

_loaded_routers = []
_failed_imports = []


def _safe_import_router(module_path: str, attr: str = "router"):
    """Import a router safely. Returns the router or None."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        return router
    except Exception as e:
        _failed_imports.append(f"{module_path}: {e}")
        return None


# Core routes (these should always work)
resume_router = _safe_import_router("backend.routes.resume_routes")
interview_router = _safe_import_router("backend.routes.interview_routes")
health_router = _safe_import_router("backend.routes.health_routes")
auth_router = _safe_import_router("backend.routes.auth_routes")
voice_router = _safe_import_router("backend.routes.voice_routes")
proctor_router = _safe_import_router("backend.routes.proctor_routes")
coding_router = _safe_import_router("backend.routes.coding_routes")
analytics_router = _safe_import_router("backend.routes.analytics_routes")
tts_router = _safe_import_router("backend.routes.tts_routes")

# Optional recruiter routes (may fail if models not migrated yet)
recruiter_router = _safe_import_router("backend.routes.recruiter_routes")
notes_router = _safe_import_router("backend.routes.notes_routes")
export_router = _safe_import_router("backend.routes.export_routes")
proctoring_detail_router = _safe_import_router("backend.routes.proctoring_detail_routes")


# ══════════════════════════════════════════════════════════════════════════════
# Application Lifecycle (startup / shutdown) — FULLY RESILIENT
# ══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown with graceful error handling at every step."""

    # ── STARTUP ──────────────────────────────────────────────────────────────
    setup_logging()
    logger.info(
        "starting_application",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    if _failed_imports:
        for msg in _failed_imports:
            logger.warning("route_import_failed", detail=msg)
        print(f"⚠️  {len(_failed_imports)} route(s) failed to import — app starting without them")

    # 1. Database initialization (with error recovery)
    db_ready = False
    try:
        import backend.models  # noqa: F401 — registers all ORM models with Base
        await init_db()
        logger.info("database_tables_created")
        db_ready = True
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        print(f"⚠️  Database init failed: {e}")

    # 2. Auto-migration (skip if DB not ready)
    if db_ready:
        try:
            from backend.db.auto_migrate import run_auto_migration
            await run_auto_migration(async_engine)
            logger.info("auto_migration_complete")
        except Exception as e:
            logger.warning("auto_migration_failed", error=str(e))

    # 3. Seed challenges (skip if DB not ready)
    if db_ready:
        try:
            from backend.db.session import AsyncSessionLocal
            from backend.seed_challenges import seed_default_challenges
            async with AsyncSessionLocal() as db:
                added = await seed_default_challenges(db)
                if added:
                    logger.info("seeded_coding_challenges", count=added)
        except Exception as e:
            logger.warning("seed_challenges_failed", error=str(e))

    # 4. Redis initialization (OPTIONAL — app works without it)
    redis_ready = False
    try:
        await init_redis()
        redis_ready = True
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        print(f"⚠️  Redis not available: {e} — app running without cache")

    logger.info(
        "application_ready",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        db_ready=db_ready,
        redis_ready=redis_ready,
        routes_loaded=len([r for r in _loaded_routers if r]),
        routes_failed=len(_failed_imports),
    )

    yield  # ← Application runs here

    # ── SHUTDOWN ─────────────────────────────────────────────────────────────
    logger.info("shutting_down")
    try:
        await close_redis()
    except Exception:
        pass
    try:
        await close_db()
    except Exception:
        pass
    logger.info("shutdown_complete")


# ══════════════════════════════════════════════════════════════════════════════
# Create FastAPI application
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI-powered mock interview system with resume analysis, "
                "real-time feedback, and scoring — backed by PostgreSQL + Redis.",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL EXCEPTION HANDLER — No more raw 500s to the client
# ══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch ALL unhandled exceptions and return clean JSON."""
    tb = traceback.format_exc()
    logger.error(
        "unhandled_exception",
        path=str(request.url.path),
        method=request.method,
        error=str(exc),
        traceback=tb,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "detail": "Internal server error. Please try again.",
            "error_type": type(exc).__name__,
        },
    )


# ── Wire Rate Limiter ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ══════════════════════════════════════════════════════════════════════════════
# Middleware
# ══════════════════════════════════════════════════════════════════════════════
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestBodySizeLimitMiddleware, max_body_size=12 * 1024 * 1024)
app.add_middleware(SecurityHeadersMiddleware)
configure_cors(app)


# ══════════════════════════════════════════════════════════════════════════════
# Register Routers (only those that imported successfully)
# ══════════════════════════════════════════════════════════════════════════════

_all_routers = [
    (auth_router, "/api/v1"),
    (resume_router, "/api/v1"),
    (interview_router, "/api/v1"),
    (voice_router, "/api/v1"),
    (proctor_router, "/api/v1"),
    (coding_router, "/api/v1"),
    (analytics_router, "/api/v1"),
    (tts_router, "/api/v1"),
    (health_router, ""),
    (recruiter_router, "/api/v1"),
    (notes_router, "/api/v1"),
    (export_router, "/api/v1"),
    (proctoring_detail_router, "/api/v1"),
]

for router, prefix in _all_routers:
    if router is not None:
        try:
            app.include_router(router, prefix=prefix) if prefix else app.include_router(router)
            _loaded_routers.append(router)
        except Exception as e:
            print(f"⚠️  Failed to register router: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Root Endpoint (always works)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint — shows API info"""
    return {
        "message": "🚀 AI Interview Assistant API is running!",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "routes_loaded": len(_loaded_routers),
        "routes_failed": len(_failed_imports),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Run the server (for direct execution)
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting AI Interview Assistant Backend v2.1 (Resilient)...")
    print(f"   → Running at: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"   → API Docs: http://localhost:{settings.BACKEND_PORT}/docs")

    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
    )
