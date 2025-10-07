-- Migration 002: Chatbot Schema for PostgreSQL
-- Created: 2025-10-07
-- Purpose: Add chatbot functionality with context tracking and feedback

-- Create chatbot_sessions table
CREATE TABLE IF NOT EXISTS chatbot_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chatbot_user_id ON chatbot_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_user_source ON chatbot_sessions(user_id, source);
CREATE INDEX IF NOT EXISTS idx_chatbot_last_message ON chatbot_sessions(last_message_at);

-- Create chatbot_messages table
CREATE TABLE IF NOT EXISTS chatbot_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    message_role VARCHAR(20) NOT NULL,
    message_content TEXT NOT NULL,
    response_id VARCHAR(255),
    context_data JSONB,
    sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chatbot_msg_session ON chatbot_messages(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chatbot_msg_user ON chatbot_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_response_id ON chatbot_messages(response_id);

-- Create chatbot_feedback table for response feedback
CREATE TABLE IF NOT EXISTS chatbot_feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    response_id VARCHAR(255) NOT NULL,
    feedback BOOLEAN NOT NULL,
    feedback_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chatbot_feedback_response ON chatbot_feedback(response_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_feedback_user ON chatbot_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_feedback_created ON chatbot_feedback(created_at);

-- Add comments
COMMENT ON TABLE chatbot_sessions IS 'Stores chat sessions with users';
COMMENT ON TABLE chatbot_messages IS 'Stores individual chat messages with context';
COMMENT ON TABLE chatbot_feedback IS 'Stores user feedback on chat responses';
COMMENT ON COLUMN chatbot_messages.context_data IS 'Retrieved context from Pinecone (JSONB)';
COMMENT ON COLUMN chatbot_messages.sources IS 'Source documents information (JSONB)';
COMMENT ON COLUMN chatbot_sessions.source IS 'Source of chat session (e.g., WA for WhatsApp)';