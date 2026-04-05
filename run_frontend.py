"""
Convenience script to run the Streamlit frontend.
Run this from the project root: python run_frontend.py
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    print("=" * 55)
    print("  🎯 AI Interview Assistant - Frontend")
    print("=" * 55)
    print("  🌐 Opening at: http://localhost:8501")
    print("  ⚠️  Make sure backend is running first!")
    print("=" * 55)
    print()
    
    # Run streamlit from the project root
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "frontend/app.py",
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark",
    ])
