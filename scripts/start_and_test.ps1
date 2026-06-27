# ============================================
# AI Interview Assistant — Quick Start & Validate
# ============================================
# Usage: .\scripts\start_and_test.ps1
# 
# This script:
#   1. Validates all imports
#   2. Runs the test suite (if pytest installed)
#   3. Starts the backend server
# ============================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Interview Assistant — Validator" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Activate venv if exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Yellow
    . .\venv\Scripts\Activate.ps1
} else {
    Write-Host "[1/4] No venv found, using system Python" -ForegroundColor Yellow
}

# Step 2: Validate imports
Write-Host "[2/4] Validating backend imports..." -ForegroundColor Yellow
try {
    python scripts/validate_backend.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Validation failed! Fix errors above before running." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  ⚠️  Validation script failed: $_" -ForegroundColor Red
    Write-Host "  Continuing anyway..." -ForegroundColor Yellow
}

# Step 3: Run tests (optional)
Write-Host ""
Write-Host "[3/4] Running tests..." -ForegroundColor Yellow
try {
    $pytestInstalled = python -c "import pytest" 2>$null
    if ($LASTEXITCODE -eq 0) {
        pytest tests/ -x -q --tb=short 2>&1 | Select-Object -First 30
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ⚠️  Some tests failed. Check output above." -ForegroundColor Yellow
        } else {
            Write-Host "  ✅ All tests passed!" -ForegroundColor Green
        }
    } else {
        Write-Host "  ⚠️  pytest not installed. Run: pip install -r tests/requirements-test.txt" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Could not run tests: $_" -ForegroundColor Yellow
}

# Step 4: Start server
Write-Host ""
Write-Host "[4/4] Starting backend server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "  🚀 Server: http://localhost:8000" -ForegroundColor Green
Write-Host "  📚 Docs:   http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  ❤️  Health: http://localhost:8000/health" -ForegroundColor Green
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Press Ctrl+C to stop" -ForegroundColor DarkGray
Write-Host ""

python run_backend.py
