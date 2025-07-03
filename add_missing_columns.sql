-- Add missing columns to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS channel TEXT,
ADD COLUMN IF NOT EXISTS "user" TEXT,
ADD COLUMN IF NOT EXISTS team_info JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_activity BIGINT;