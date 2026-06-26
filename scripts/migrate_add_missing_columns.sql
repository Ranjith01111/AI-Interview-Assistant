-- ============================================================
-- AI Interview Assistant — Database Migration Script
-- Adds all missing columns/tables to match current ORM models
-- Run with: psql -U postgres -d interview_assistant -f scripts/migrate_add_missing_columns.sql
-- ============================================================

-- ── interview_sessions: Add missing columns ─────────────────
ALTER TABLE interview_sessions 
  ADD COLUMN IF NOT EXISTS reference_photo_path VARCHAR(500),
  ADD COLUMN IF NOT EXISTS face_embedding JSONB;

-- ── Ensure 'resumes' table exists ───────────────────────────
CREATE TABLE IF NOT EXISTS resumes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file_name VARCHAR(255) NOT NULL,
  content TEXT,
  file_path VARCHAR(512),
  file_type VARCHAR(100),
  size_bytes INTEGER,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_resumes_user_id ON resumes(user_id);

-- ── Ensure 'coding_challenges' table exists ─────────────────
CREATE TABLE IF NOT EXISTS coding_challenges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  difficulty VARCHAR(50) NOT NULL DEFAULT 'Medium',
  template_code JSONB NOT NULL DEFAULT '{}',
  test_cases JSONB NOT NULL DEFAULT '[]',
  time_limit FLOAT NOT NULL DEFAULT 2.0,
  memory_limit INTEGER NOT NULL DEFAULT 128,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Ensure 'coding_submissions' table exists ────────────────
CREATE TABLE IF NOT EXISTS coding_submissions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES interview_sessions(id) ON DELETE CASCADE,
  challenge_id UUID NOT NULL REFERENCES coding_challenges(id) ON DELETE CASCADE,
  language VARCHAR(50) NOT NULL,
  code TEXT NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'Pending',
  score INTEGER NOT NULL DEFAULT 0,
  results JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_coding_submissions_session_id ON coding_submissions(session_id);
CREATE INDEX IF NOT EXISTS ix_coding_submissions_challenge_id ON coding_submissions(challenge_id);

-- ── Ensure 'proctor_logs' table exists ──────────────────────
CREATE TABLE IF NOT EXISTS proctor_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
  event_type VARCHAR(50) NOT NULL,
  client_ip VARCHAR(45),
  user_agent TEXT,
  details JSONB,
  snapshot_path VARCHAR(500),
  risk_score FLOAT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_proctor_logs_session_id ON proctor_logs(session_id);
CREATE INDEX IF NOT EXISTS ix_proctor_logs_event_type ON proctor_logs(event_type);

-- ── Ensure 'analytics' table exists ─────────────────────────
CREATE TABLE IF NOT EXISTS analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
  metric_name VARCHAR(100) NOT NULL,
  metric_value FLOAT NOT NULL,
  details JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_analytics_session_id ON analytics(session_id);
CREATE INDEX IF NOT EXISTS ix_analytics_metric_name ON analytics(metric_name);

-- ── Ensure 'audit_logs' table exists ────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action VARCHAR(50) NOT NULL,
  resource VARCHAR(500),
  ip_address VARCHAR(45),
  user_agent TEXT,
  details JSONB,
  status VARCHAR(20) NOT NULL DEFAULT 'success',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);

-- ── Ensure 'question_embeddings' table exists ───────────────
CREATE TABLE IF NOT EXISTS question_embeddings (
  id SERIAL PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES interview_sessions(id) ON DELETE CASCADE,
  question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  question_text TEXT NOT NULL,
  embedding_vector BYTEA NOT NULL,
  embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_question_embeddings_session_id ON question_embeddings(session_id);
CREATE INDEX IF NOT EXISTS ix_question_embeddings_question_id ON question_embeddings(question_id);

-- ── Done ────────────────────────────────────────────────────
SELECT 'Migration completed successfully! All columns and tables are up to date.' AS status;
