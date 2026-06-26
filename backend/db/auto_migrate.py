"""
Auto-Migration — Ensures all required tables and columns exist.

Runs on startup. Uses raw SQL with IF NOT EXISTS / ADD COLUMN IF NOT EXISTS
so it's safe to run multiple times.
"""

from sqlalchemy import text
from backend.core.logging import get_logger

logger = get_logger("backend.db.auto_migrate")

MIGRATION_SQL = """
-- Ensure users table has all required columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'candidate';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;

-- Ensure interview_sessions has all columns
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS reference_photo_path VARCHAR(500);
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS face_embedding JSONB;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS average_score FLOAT;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS recommendation VARCHAR(100);
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS overall_feedback TEXT;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS current_question_index INTEGER DEFAULT 0;
ALTER TABLE interview_sessions ADD COLUMN IF NOT EXISTS user_id UUID;

-- Ensure answers table has all columns
DO $$ BEGIN
    ALTER TABLE answers ADD COLUMN IF NOT EXISTS strengths JSONB DEFAULT '[]';
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE answers ADD COLUMN IF NOT EXISTS improvements JSONB DEFAULT '[]';
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE answers ADD COLUMN IF NOT EXISTS model_answer_hint TEXT DEFAULT '';
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

-- Ensure proctor_logs has all columns
DO $$ BEGIN
    ALTER TABLE proctor_logs ADD COLUMN IF NOT EXISTS snapshot_path VARCHAR(500);
EXCEPTION WHEN undefined_table THEN NULL;
END $$;

DO $$ BEGIN
    ALTER TABLE proctor_logs ADD COLUMN IF NOT EXISTS risk_score FLOAT;
EXCEPTION WHEN undefined_table THEN NULL;
END $$;
"""


async def run_auto_migration(engine):
    """
    Run safe migrations to ensure all columns exist.
    Should be called AFTER init_db() (which creates tables).
    """
    try:
        async with engine.begin() as conn:
            # Split and execute each statement separately
            for statement in MIGRATION_SQL.strip().split(";"):
                stmt = statement.strip()
                if stmt and not stmt.startswith("--"):
                    try:
                        await conn.execute(text(stmt + ";"))
                    except Exception as e:
                        # Log but don't crash — some ALTER may fail if column exists
                        error_msg = str(e)
                        if "already exists" not in error_msg and "does not exist" not in error_msg:
                            logger.warning("migration_statement_warning", error=error_msg[:100])

        logger.info("auto_migration_completed")
    except Exception as e:
        logger.error("auto_migration_failed", error=str(e))
        # Don't crash the app — analytics will return empty data gracefully
