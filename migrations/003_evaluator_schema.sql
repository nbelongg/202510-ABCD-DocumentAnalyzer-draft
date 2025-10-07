-- Migration 003: Evaluator Schema for PostgreSQL
-- Created: 2025-10-07
-- Purpose: Add proposal evaluator functionality with three-part analysis

-- Create evaluator_sessions table
CREATE TABLE IF NOT EXISTS evaluator_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    document_type VARCHAR(100) DEFAULT 'Proposal',
    organization_id VARCHAR(255),
    guideline_id VARCHAR(255),
    proposal_text TEXT,
    proposal_url VARCHAR(500),
    tor_text TEXT,
    tor_url VARCHAR(500),
    internal_analysis JSONB,
    external_analysis JSONB,
    delta_analysis JSONB,
    overall_score FLOAT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluator_user_sessions ON evaluator_sessions(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_evaluator_session_id ON evaluator_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluator_org ON evaluator_sessions(organization_id);

-- Create evaluator_followups table
CREATE TABLE IF NOT EXISTS evaluator_followups (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    answer TEXT,
    section VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluator_followup_session ON evaluator_followups(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluator_followup_user ON evaluator_followups(user_id);

-- Create evaluator_feedback table
CREATE TABLE IF NOT EXISTS evaluator_feedback (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    section VARCHAR(100),
    feedback BOOLEAN,
    feedback_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluator_feedback_session ON evaluator_feedback(session_id);

-- Create evaluator_guidelines table (organization-specific evaluation guidelines)
CREATE TABLE IF NOT EXISTS evaluator_guidelines (
    id SERIAL PRIMARY KEY,
    guideline_id VARCHAR(255) UNIQUE NOT NULL,
    organization_id VARCHAR(255) NOT NULL,
    guideline_name VARCHAR(255) NOT NULL,
    guideline_text TEXT NOT NULL,
    guideline_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluator_guideline_org ON evaluator_guidelines(organization_id);
CREATE INDEX IF NOT EXISTS idx_evaluator_guideline_active ON evaluator_guidelines(is_active);

-- Add comments
COMMENT ON TABLE evaluator_sessions IS 'Stores proposal evaluation sessions';
COMMENT ON TABLE evaluator_followups IS 'Stores follow-up questions for evaluations';
COMMENT ON TABLE evaluator_feedback IS 'Stores user feedback on evaluations';
COMMENT ON TABLE evaluator_guidelines IS 'Stores organization-specific evaluation guidelines';
COMMENT ON COLUMN evaluator_sessions.internal_analysis IS 'P_Internal analysis results (JSONB)';
COMMENT ON COLUMN evaluator_sessions.external_analysis IS 'P_External analysis results (JSONB)';
COMMENT ON COLUMN evaluator_sessions.delta_analysis IS 'P_Delta gap analysis results (JSONB)';