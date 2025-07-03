-- COMPLETE database schema fix - all columns conversation_manager.py expects
-- This fixes ALL missing columns at once instead of piecemeal

DROP TABLE IF EXISTS conversations CASCADE;

CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    conversation_key TEXT UNIQUE NOT NULL,
    channel TEXT,
    "user" TEXT,
    state TEXT DEFAULT 'initial',
    context JSONB DEFAULT '{}',
    logo_url TEXT,
    logo_analysis JSONB,
    selected_products JSONB DEFAULT '[]',
    product_selected JSONB,
    logo_info JSONB,
    team_info JSONB DEFAULT '{}',
    selected_variants JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity BIGINT,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    pending_request TEXT,
    recent_creation BOOLEAN
);

CREATE INDEX idx_conversations_key ON conversations(conversation_key);
CREATE INDEX idx_conversations_channel_user ON conversations(channel, "user");
CREATE INDEX idx_conversations_last_activity ON conversations(last_activity);