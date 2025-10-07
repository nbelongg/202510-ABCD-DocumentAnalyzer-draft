-- Migration 001: Analyzer Schema for PostgreSQL
-- Created: 2025-10-07
-- Purpose: Create analyzer tables for document analysis functionality

-- Create analyzer_sessions table
CREATE TABLE IF NOT EXISTS analyzer_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    document_type VARCHAR(100),
    user_role VARCHAR(100),
    organization_id VARCHAR(255),
    sections JSONB,
    summary TEXT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analyzer_user_sessions ON analyzer_sessions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_analyzer_session_id ON analyzer_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_analyzer_org ON analyzer_sessions(organization_id);

-- Create analyzer_followups table
CREATE TABLE IF NOT EXISTS analyzer_followups (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    answer TEXT,
    section VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analyzer_followup_session ON analyzer_followups(session_id);
CREATE INDEX IF NOT EXISTS idx_analyzer_followup_user ON analyzer_followups(user_id);

-- Create analyzer_feedback table
CREATE TABLE IF NOT EXISTS analyzer_feedback (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    section VARCHAR(100),
    feedback BOOLEAN,
    feedback_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analyzer_feedback_session ON analyzer_feedback(session_id);

-- Create analyzer_prompts table
CREATE TABLE IF NOT EXISTS analyzer_prompts (
    prompt_id SERIAL PRIMARY KEY,
    prompt_label VARCHAR(50) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    organization_id VARCHAR(255),
    base_prompt TEXT NOT NULL,
    customization_prompt TEXT,
    system_prompt TEXT,
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 4000,
    use_corpus BOOLEAN DEFAULT TRUE,
    corpus_id VARCHAR(100),
    num_examples INT DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (prompt_label, document_type, organization_id)
);

CREATE INDEX IF NOT EXISTS idx_analyzer_prompts_label ON analyzer_prompts(prompt_label);
CREATE INDEX IF NOT EXISTS idx_analyzer_prompts_type ON analyzer_prompts(document_type);
CREATE INDEX IF NOT EXISTS idx_analyzer_prompts_org ON analyzer_prompts(organization_id);

-- Add comments for documentation
COMMENT ON TABLE analyzer_sessions IS 'Stores document analysis sessions';
COMMENT ON TABLE analyzer_followups IS 'Stores follow-up questions for analysis sessions';
COMMENT ON TABLE analyzer_feedback IS 'Stores user feedback on analysis';
COMMENT ON TABLE analyzer_prompts IS 'Stores prompts configuration for analysis';
