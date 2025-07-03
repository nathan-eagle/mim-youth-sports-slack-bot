-- MINIMAL WORKING SCHEMA
-- Just the essential tables to make the bot work

CREATE TABLE conversations (
    conversation_key TEXT PRIMARY KEY,
    state TEXT DEFAULT 'initial',
    context JSONB DEFAULT '{}',
    created_at BIGINT DEFAULT EXTRACT(EPOCH FROM NOW()),
    last_activity BIGINT DEFAULT EXTRACT(EPOCH FROM NOW())
);

CREATE TABLE product_designs (
    id TEXT PRIMARY KEY,
    product_name TEXT,
    color TEXT,
    mockup_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);