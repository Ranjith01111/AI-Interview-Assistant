"""
Routes package — all FastAPI routers are registered here.
"""

from backend.routes.resume_routes import router as resume_router
from backend.routes.interview_routes import router as interview_router
from backend.routes.health_routes import router as health_router
from backend.routes.auth_routes import router as auth_router

__all__ = [
    "resume_router",
    "interview_router",
    "health_router",
    "auth_router",
]
