"""
Backend Validation Script — Checks imports, syntax, and configuration.

Run with:
    cd "E:\AI Interview Assistant"
    python scripts/validate_backend.py
"""

import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 65)
print("  AI Interview Assistant — Backend Validation")
print("=" * 65)
print()

errors = []
warnings = []
successes = []


def check(label, import_fn):
    try:
        import_fn()
        successes.append(f"✅ {label}")
    except Exception as e:
        errors.append(f"❌ {label} — {type(e).__name__}: {e}")


# ── Core Module Imports ────────────────────────────────────────────────
print("[1/6] Core modules...")
check("config", lambda: __import__("backend.core.config", fromlist=["settings"]))
check("security", lambda: __import__("backend.core.security", fromlist=["configure_cors"]))
check("middleware", lambda: __import__("backend.core.middleware", fromlist=["SecurityHeadersMiddleware"]))
check("rate_limiter", lambda: __import__("backend.core.rate_limiter", fromlist=["limiter"]))
check("logging", lambda: __import__("backend.core.logging", fromlist=["get_logger"]))

# ── DB Module Imports ──────────────────────────────────────────────────
print("[2/6] Database modules...")
check("db.base", lambda: __import__("backend.db.base", fromlist=["Base"]))
check("db.session", lambda: __import__("backend.db.session", fromlist=["get_db"]))
check("db.redis", lambda: __import__("backend.db.redis", fromlist=["init_redis"]))
check("db.auto_migrate", lambda: __import__("backend.db.auto_migrate", fromlist=["run_auto_migration"]))

# ── Model Imports ──────────────────────────────────────────────────────
print("[3/6] Models...")
check("models.user", lambda: __import__("backend.models.user", fromlist=["User"]))
check("models.interview", lambda: __import__("backend.models.interview", fromlist=["InterviewSession"]))
check("models.schemas", lambda: __import__("backend.models.schemas", fromlist=["ChatResponse"]))
check("models.auth_schemas", lambda: __import__("backend.models.auth_schemas", fromlist=["RegisterRequest"]))
check("models.proctor_log", lambda: __import__("backend.models.proctor_log", fromlist=["ProctorLog"]))
check("models.coding_challenge", lambda: __import__("backend.models.coding_challenge", fromlist=["CodingChallenge"]))

# ── Service Imports ────────────────────────────────────────────────────
print("[4/6] Services...")
check("auth_service", lambda: __import__("backend.services.auth_service", fromlist=["register_user"]))
check("resume_service", lambda: __import__("backend.services.resume_service", fromlist=["process_resume"]))
check("interview_agent", lambda: __import__("backend.services.interview_agent", fromlist=["InterviewAgent"]))
check("sandbox_service", lambda: __import__("backend.services.sandbox_service", fromlist=["SandboxService"]))
check("question_service", lambda: __import__("backend.services.question_service", fromlist=["generate_questions"]))
check("session_service", lambda: __import__("backend.services.session_service", fromlist=["get_agent_state"]))

# ── NLP Engine Imports ─────────────────────────────────────────────────
print("[5/6] NLP Engine...")
check("resume_parser", lambda: __import__("backend.nlp_engine.resume_parser", fromlist=["parse_resume_structured"]))
check("question_generator", lambda: __import__("backend.nlp_engine.question_generator", fromlist=["QuestionGenerator"]))
check("answer_evaluator", lambda: __import__("backend.nlp_engine.answer_evaluator", fromlist=["evaluate_answer"]))
check("feedback_generator", lambda: __import__("backend.nlp_engine.feedback_generator", fromlist=["generate_final_summary"]))
check("question_bank", lambda: __import__("backend.nlp_engine.question_bank", fromlist=["get_question_bank"]))

# ── Route Imports ──────────────────────────────────────────────────────
print("[6/6] Routes...")
check("auth_routes", lambda: __import__("backend.routes.auth_routes", fromlist=["router"]))
check("interview_routes", lambda: __import__("backend.routes.interview_routes", fromlist=["router"]))
check("resume_routes", lambda: __import__("backend.routes.resume_routes", fromlist=["router"]))
check("proctor_routes", lambda: __import__("backend.routes.proctor_routes", fromlist=["router"]))
check("coding_routes", lambda: __import__("backend.routes.coding_routes", fromlist=["router"]))
check("voice_routes", lambda: __import__("backend.routes.voice_routes", fromlist=["router"]))
check("analytics_routes", lambda: __import__("backend.routes.analytics_routes", fromlist=["router"]))
check("health_routes", lambda: __import__("backend.routes.health_routes", fromlist=["router"]))
check("tts_routes", lambda: __import__("backend.routes.tts_routes", fromlist=["router"]))

# ── Security Validation ────────────────────────────────────────────────
print()
print("─" * 65)
print("  SECURITY CHECKS")
print("─" * 65)

# Check sandbox_service for shell=True
try:
    import inspect
    from backend.services import sandbox_service
    source = inspect.getsource(sandbox_service)
    
    if "shell=True" in source and "shell=True" not in source.split("# SECURITY FIX")[0]:
        # Check if it's only in comments
        import re
        code_lines = [l for l in source.split('\n') if not l.strip().startswith('#')]
        code_only = '\n'.join(code_lines)
        if "shell=True" in code_only:
            errors.append("❌ SECURITY: shell=True found in sandbox_service.py code!")
        else:
            successes.append("✅ SECURITY: shell=True only in comments (safe)")
    else:
        successes.append("✅ SECURITY: No shell=True in sandbox execution code")
except Exception as e:
    warnings.append(f"⚠️  Could not verify sandbox security: {e}")

# Check password validation exists
try:
    from backend.services.auth_service import validate_password_strength
    successes.append("✅ SECURITY: Password validation function exists")
except ImportError:
    errors.append("❌ SECURITY: validate_password_strength not found!")

# Check sanitize_code exists
try:
    from backend.services.sandbox_service import _sanitize_code
    result = _sanitize_code("python", "import os; os.system('rm -rf /')")
    if result and "Blocked" in result:
        successes.append("✅ SECURITY: Code sanitizer blocks os.system")
    else:
        errors.append("❌ SECURITY: Code sanitizer did NOT block os.system!")
except Exception as e:
    errors.append(f"❌ SECURITY: Code sanitizer error — {e}")

# ── FastAPI App Import ─────────────────────────────────────────────────
print()
print("─" * 65)
print("  FASTAPI APPLICATION")
print("─" * 65)

try:
    from backend.main import app
    successes.append("✅ FastAPI app imported successfully")
    
    # Check routes are registered
    routes = [r.path for r in app.routes]
    expected_routes = ["/api/v1/auth/login", "/api/v1/interview/chat", "/health"]
    for route in expected_routes:
        if any(route in r for r in routes):
            successes.append(f"✅ Route registered: {route}")
        else:
            warnings.append(f"⚠️  Route not found: {route}")
except Exception as e:
    errors.append(f"❌ FastAPI app import failed — {type(e).__name__}: {e}")

# ── Summary ────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("  RESULTS")
print("=" * 65)
print()

for s in successes:
    print(f"  {s}")
for w in warnings:
    print(f"  {w}")
for e in errors:
    print(f"  {e}")

print()
print(f"  Total: {len(successes)} passed, {len(warnings)} warnings, {len(errors)} errors")
print()

if errors:
    print("  ⚠️  Some checks failed. Review errors above.")
    sys.exit(1)
else:
    print("  🎉 All checks passed! Backend is ready to run.")
    print()
    print("  Start with:")
    print('    cd "E:\\AI Interview Assistant"')
    print("    python run_backend.py")
    sys.exit(0)
