-- ============================================================
-- AI Interview Assistant — PostgreSQL Initialization Script
-- Runs once on first container start (if pgdata volume is empty)
-- ============================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set default search path
ALTER DATABASE interview_assistant SET search_path TO public;

-- Connection limits for the app user
-- (The main postgres superuser created by POSTGRES_USER is used for now;
--  for extra hardening create a separate app user here)

-- Performance settings (applied per-session, set server-wide in postgresql.conf)
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_min_duration_statement = '500';   -- log queries > 500ms
ALTER SYSTEM SET log_connections = 'on';
ALTER SYSTEM SET log_disconnections = 'on';
