"""
Convenience script to run the Vite frontend.
Run this from the project root: python run_frontend.py
"""
import subprocess
import os

if __name__ == "__main__":
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    
    print("=" * 55)
    print("  [Frontend] AI Interview Assistant - Custom Frontend")
    print("=" * 55)
    
    # Check if node_modules exists, run npm install if not
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("  [Setup] node_modules not found. Running npm install...")
        subprocess.run(["npm", "install"], cwd=frontend_dir)
        
    print("  [URL] Opening at: http://localhost:5173")
    print("  [Warning] Make sure backend is running first!")
    print("=" * 55)
    print()
    
    # Run vite from the frontend dir
    subprocess.run(["npm", "run", "dev"], cwd=frontend_dir)
