-- ============================================================
-- Migration: Add Candidate Pipeline Workflow
-- Description: Adds pipeline stage tracking, recruiter notes,
--              and a pipeline_history audit table.
-- Date: 2026-06-27
-- ============================================================

-- 1. Add pipeline columns to interview_sessions
-- ============================================================

ALTER TABLE interview_sessions
    ADD COLUMN pipeline_stage VARCHAR(30) NOT NULL DEFAULT 'screening';

ALTER TABLE interview_sessions
    ADD COLUMN recruiter_notes TEXT NOT NULL DEFAULT '';

ALTER TABLE interview_sessions
    ADD COLUMN pipeline_updated_by UUID NULL
        REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE interview_sessions
    ADD COLUMN stage_updated_at TIMESTAMPTZ NULL;

-- Index for fast pipeline board queries (filter by stage)
CREATE INDEX ix_interview_sessions_pipeline_stage
    ON interview_sessions(pipeline_stage);

-- Composite index for ordering within stages
CREATE INDEX ix_interview_sessions_stage_updated
    ON interview_sessions(pipeline_stage, stage_updated_at DESC NULLS LAST);


-- 2. Create pipeline_history table (audit trail)
-- ============================================================

CREATE TABLE pipeline_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL
        REFERENCES interview_sessions(id) ON DELETE CASCADE,
    from_stage VARCHAR(30) NOT NULL,
    to_stage VARCHAR(30) NOT NULL,
    changed_by UUID NULL
        REFERENCES users(id) ON DELETE SET NULL,
    notes TEXT NOT NULL DEFAULT '',
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Denormalized candidate name for fast history display
    candidate_name VARCHAR(255) NULL
);

CREATE INDEX ix_pipeline_history_session_id
    ON pipeline_history(session_id);

CREATE INDEX ix_pipeline_history_changed_at
    ON pipeline_history(changed_at DESC);

CREATE INDEX ix_pipeline_history_changed_by
    ON pipeline_history(changed_by);


-- 3. Backfill: Move completed sessions with recommendations
-- ============================================================
-- Optional: auto-categorize existing completed sessions

-- Sessions with "Strong Hire" → shortlisted
UPDATE interview_sessions
SET pipeline_stage = 'shortlisted',
    stage_updated_at = NOW()
WHERE status = 'completed'
  AND recommendation ILIKE '%strong hire%';

-- Sessions with "No Hire" → rejected
UPDATE interview_sessions
SET pipeline_stage = 'rejected',
    stage_updated_at = NOW()
WHERE status = 'completed'
  AND recommendation ILIKE '%no hire%';


-- ============================================================
-- ROLLBACK (uncomment to revert)
-- ============================================================
-- DROP INDEX IF EXISTS ix_pipeline_history_changed_by;
-- DROP INDEX IF EXISTS ix_pipeline_history_changed_at;
-- DROP INDEX IF EXISTS ix_pipeline_history_session_id;
-- DROP TABLE IF EXISTS pipeline_history;
-- DROP INDEX IF EXISTS ix_interview_sessions_stage_updated;
-- DROP INDEX IF EXISTS ix_interview_sessions_pipeline_stage;
-- ALTER TABLE interview_sessions DROP COLUMN IF EXISTS stage_updated_at;
-- ALTER TABLE interview_sessions DROP COLUMN IF EXISTS pipeline_updated_by;
-- ALTER TABLE interview_sessions DROP COLUMN IF EXISTS recruiter_notes;
-- ALTER TABLE interview_sessions DROP COLUMN IF EXISTS pipeline_stage;
