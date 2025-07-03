-- COMPLETE DATABASE SCHEMA FIX
-- This creates ALL tables with ALL columns that the code expects
-- Run this once and all database errors will be fixed

-- Drop existing tables to start fresh
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS customer_orders CASCADE;
DROP TABLE IF EXISTS product_variants CASCADE;
DROP TABLE IF EXISTS product_designs CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;

-- 1. Conversations table (fixed timestamp handling)
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
    created_at BIGINT,  -- Unix timestamp as integer
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity BIGINT,  -- Unix timestamp as integer
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    pending_request TEXT,
    recent_creation BOOLEAN
);

-- 2. Product designs table (with ALL columns database_service.py expects)
CREATE TABLE product_designs (
    id TEXT PRIMARY KEY,  -- UUID string
    product_name TEXT,
    product_id TEXT,
    variant_id INTEGER,
    color TEXT,
    size TEXT,
    mockup_url TEXT,
    logo_url TEXT,
    price DECIMAL(10,2),
    printify_data JSONB DEFAULT '{}',
    created_at TEXT,  -- ISO timestamp string
    status TEXT DEFAULT 'active',
    -- Also keep original columns for compatibility
    name TEXT,
    description TEXT,
    logo_analysis JSONB,
    printify_product_id TEXT,
    blueprint_id INTEGER,
    print_provider_id INTEGER,
    base_variant_id INTEGER,
    image_id TEXT,
    price_cents INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Product variants table
CREATE TABLE product_variants (
    id SERIAL PRIMARY KEY,
    design_id INTEGER REFERENCES product_designs(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL,
    color TEXT,
    size TEXT,
    price_cents INTEGER,
    mockup_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Customer orders table
CREATE TABLE customer_orders (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    name TEXT,
    phone TEXT,
    address JSONB,
    stripe_payment_intent_id TEXT,
    total_amount_cents INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES customer_orders(id) ON DELETE CASCADE,
    design_id INTEGER REFERENCES product_designs(id),
    variant_id INTEGER,
    quantity INTEGER DEFAULT 1,
    unit_price_cents INTEGER,
    total_price_cents INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_conversations_key ON conversations(conversation_key);
CREATE INDEX idx_conversations_channel_user ON conversations(channel, "user");
CREATE INDEX idx_conversations_last_activity ON conversations(last_activity);
CREATE INDEX idx_product_designs_printify_id ON product_designs(printify_product_id);
CREATE INDEX idx_product_variants_design_id ON product_variants(design_id);
CREATE INDEX idx_customer_orders_email ON customer_orders(email);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- Enable Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_designs ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
CREATE POLICY "Enable all operations for service role" ON conversations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON product_designs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON product_variants
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON customer_orders
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Enable all operations for service role" ON order_items
    FOR ALL USING (auth.role() = 'service_role');