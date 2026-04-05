"""
Convenience script to run the FastAPI backend server.
Run this from the project root: python run_backend.py
"""
import uvicorn
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 55)
    print("  🚀 AI Interview Assistant - Backend Server")
    print("=" * 55)
    print("  📡 API URL:   http://localhost:8000")
    print("  📚 API Docs:  http://localhost:8000/docs") 
    print("  🔍 ReDoc:     http://localhost:8000/redoc")
    print("=" * 55)
    print()
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
