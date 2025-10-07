-- Migration 004: Admin Schema for PostgreSQL
-- Created: 2025-10-07
-- Purpose: Add admin functionality for prompts, organizations, and user management

-- Create prompts table (for all prompt types)
CREATE TABLE IF NOT EXISTS prompts (
    id SERIAL PRIMARY KEY,
    prompt_id VARCHAR(255) UNIQUE NOT NULL,
    prompt_type VARCHAR(100) NOT NULL,
    prompt_name VARCHAR(255) NOT NULL,
    prompt_text TEXT NOT NULL,
    description TEXT,
    version VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prompts_type ON prompts(prompt_type);
CREATE INDEX IF NOT EXISTS idx_prompts_active ON prompts(is_active);
CREATE INDEX IF NOT EXISTS idx_prompts_name ON prompts(prompt_name);

-- Create organizations table
CREATE TABLE IF NOT EXISTS organizations (
    id SERIAL PRIMARY KEY,
    organization_id VARCHAR(255) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    organization_type VARCHAR(100),
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    settings JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orgs_active ON organizations(is_active);
CREATE INDEX IF NOT EXISTS idx_orgs_name ON organizations(organization_name);

-- Create guidelines table (linked to organizations)
CREATE TABLE IF NOT EXISTS guidelines (
    id SERIAL PRIMARY KEY,
    guideline_id VARCHAR(255) UNIQUE NOT NULL,
    organization_id VARCHAR(255) NOT NULL,
    guideline_name VARCHAR(255) NOT NULL,
    guideline_text TEXT NOT NULL,
    guideline_category VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_guidelines_org ON guidelines(organization_id);
CREATE INDEX IF NOT EXISTS idx_guidelines_active ON guidelines(is_active);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    organization_id VARCHAR(255),
    user_role VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- Create api_keys table for API access
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    key_name VARCHAR(255),
    permissions JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON api_keys(api_key);

-- Add comments
COMMENT ON TABLE prompts IS 'Stores all types of prompts for the system';
COMMENT ON TABLE organizations IS 'Stores organization information';
COMMENT ON TABLE guidelines IS 'Stores organization-specific guidelines';
COMMENT ON TABLE users IS 'Stores user information';
COMMENT ON TABLE api_keys IS 'Stores API keys for authentication';
COMMENT ON COLUMN prompts.metadata IS 'Additional metadata for prompts (JSONB)';
COMMENT ON COLUMN organizations.settings IS 'Organization settings (JSONB)';
COMMENT ON COLUMN api_keys.permissions IS 'API key permissions (JSONB)';