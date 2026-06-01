-- ============================================================
-- InternHub Database Migration
-- Paste this entire script into Supabase SQL Editor and run
-- Project: wbdkhydmfoxjktlyezax
-- ============================================================

-- 1. Enable extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create tables

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname VARCHAR(100),
    token_version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);
CREATE INDEX ix_users_email ON users (email);

CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    job_type VARCHAR(50),
    salary_min INTEGER,
    salary_max INTEGER,
    description TEXT,
    skills TEXT[],
    source VARCHAR(50) NOT NULL,
    source_url TEXT NOT NULL,
    source_hash VARCHAR(64) UNIQUE NOT NULL,
    dedup_key VARCHAR(64) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true NOT NULL,
    posted_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_jobs_posted_at ON jobs (posted_at DESC);
CREATE INDEX idx_jobs_job_type ON jobs (job_type);
CREATE INDEX idx_jobs_city ON jobs (city);
CREATE INDEX idx_jobs_skills ON jobs USING GIN (skills);
CREATE INDEX idx_jobs_is_active_posted ON jobs (is_active, posted_at DESC) WHERE is_active = true;
CREATE INDEX idx_jobs_title_trgm ON jobs USING GIN (title gin_trgm_ops);
CREATE INDEX idx_jobs_company_trgm ON jobs USING GIN (company gin_trgm_ops);

CREATE TYPE frequency_enum AS ENUM ('daily', 'weekly');

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id),
    keywords TEXT[],
    cities TEXT[],
    job_types TEXT[],
    frequency frequency_enum DEFAULT 'daily' NOT NULL,
    enabled BOOLEAN DEFAULT true NOT NULL,
    last_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE application_status_enum AS ENUM ('applied', 'screening', 'interview', 'offer', 'rejected', 'closed');

CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    status application_status_enum DEFAULT 'applied' NOT NULL,
    notes TEXT,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

CREATE INDEX idx_applications_user_status ON applications (user_id, status);

CREATE TABLE digest_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    is_sent BOOLEAN DEFAULT false NOT NULL,
    matched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_digest_queue_unique ON digest_queue (user_id, job_id);

-- 3. Verification
SELECT 'Migration complete!' AS status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
SELECT extname, extversion FROM pg_extension WHERE extname IN ('pg_trgm', 'uuid-ossp');
