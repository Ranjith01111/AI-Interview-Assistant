"""
FastAPI Main Application Entry Point

AI Interview Assistant Backend
================================
Endpoints:
  POST /resume/upload              - Upload PDF resume
  POST /interview/generate-questions/{session_id} - Generate interview questions
  POST /interview/start/{session_id}              - Start the interview
  POST /interview/chat                            - Send answer, get feedback
  GET  /interview/summary/{session_id}            - Get final summary
  GET  /health                                    - Health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.resume_routes import router as resume_router
from backend.routes.interview_routes import router as interview_router
from utils.config import settings

# ============================================
# Create FastAPI application
# ============================================
app = FastAPI(
    title="AI Interview Assistant",
    description="Agentic AI-powered mock interview system with resume analysis and feedback",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI at /docs
    redoc_url="/redoc",    # ReDoc at /redoc
)

# ============================================
# CORS Middleware
# Allows the Streamlit frontend to communicate with this backend
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Register Routers
# ============================================
app.include_router(resume_router, prefix="/api/v1")
app.include_router(interview_router, prefix="/api/v1")


# ============================================
# Root & Health Check Endpoints
# ============================================
@app.get("/")
async def root():
    """Root endpoint - shows API info"""
    return {
        "message": "🚀 AI Interview Assistant API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": settings.OPENROUTER_MODEL,
        "embedding_model": settings.OPENROUTER_EMBEDDING_MODEL,
    }


# ============================================
# Run the server (for direct execution)
# ============================================
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting AI Interview Assistant Backend...")
    print(f"   → Model: {settings.OPENROUTER_MODEL}")
    print(f"   → Running at: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"   → API Docs: http://localhost:{settings.BACKEND_PORT}/docs")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,  # Auto-reload on code changes during development
    )
