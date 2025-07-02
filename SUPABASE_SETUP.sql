-- Supabase Setup for MiM Slack Bot State Management
-- Run these commands in your Supabase SQL Editor

-- 1. Conversation States Table
CREATE TABLE IF NOT EXISTS conversation_states (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_states_user_channel 
ON conversation_states(user_id, channel_id);

CREATE INDEX IF NOT EXISTS idx_conversation_states_expires 
ON conversation_states(expires_at);

-- 2. Event Deduplication Table
CREATE TABLE IF NOT EXISTS event_deduplication (
    event_id TEXT PRIMARY KEY,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_event_dedup_expires 
ON event_deduplication(expires_at);

-- 3. Temporary Data Table (for caching)
CREATE TABLE IF NOT EXISTS temporary_data (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_temp_data_expires 
ON temporary_data(expires_at);

-- 4. Metrics Data Table
CREATE TABLE IF NOT EXISTS metrics_data (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_expires 
ON metrics_data(expires_at);

-- 5. Auto-cleanup function for expired data
CREATE OR REPLACE FUNCTION cleanup_expired_data()
RETURNS void AS $$
BEGIN
    -- Clean expired conversations
    DELETE FROM conversation_states 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    -- Clean expired events
    DELETE FROM event_deduplication 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    -- Clean expired cache
    DELETE FROM temporary_data 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
    
    -- Clean expired metrics
    DELETE FROM metrics_data 
    WHERE expires_at IS NOT NULL AND expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 6. Schedule cleanup to run every hour (optional)
-- Note: You may need to enable the pg_cron extension first
-- SELECT cron.schedule('cleanup-expired-data', '0 * * * *', 'SELECT cleanup_expired_data();');

-- Verify tables were created
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_name IN ('conversation_states', 'event_deduplication', 'temporary_data', 'metrics_data')
ORDER BY table_name, ordinal_position;