-- Supabase table setup for MiM Youth Sports Bot
-- Run this in your Supabase SQL editor to create required tables

-- 1. Conversations table for storing chat state
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    conversation_key TEXT UNIQUE NOT NULL,
    state TEXT DEFAULT 'initial',
    context JSONB DEFAULT '{}',
    logo_url TEXT,
    logo_analysis JSONB,
    selected_products JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Product designs table for storing custom designs
CREATE TABLE IF NOT EXISTS product_designs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    logo_url TEXT,
    logo_analysis JSONB,
    printify_product_id TEXT,
    blueprint_id INTEGER,
    print_provider_id INTEGER,
    base_variant_id INTEGER,
    image_id TEXT,
    mockup_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Product variants table for storing available variants
CREATE TABLE IF NOT EXISTS product_variants (
    id SERIAL PRIMARY KEY,
    design_id INTEGER REFERENCES product_designs(id) ON DELETE CASCADE,
    variant_id INTEGER NOT NULL,
    color TEXT,
    size TEXT,
    price_cents INTEGER,
    mockup_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Customer orders table for order management
CREATE TABLE IF NOT EXISTS customer_orders (
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

-- 5. Order items table for individual items within orders
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES customer_orders(id) ON DELETE CASCADE,
    design_id INTEGER REFERENCES product_designs(id),
    variant_id INTEGER,
    quantity INTEGER DEFAULT 1,
    unit_price_cents INTEGER,
    total_price_cents INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_key ON conversations(conversation_key);
CREATE INDEX IF NOT EXISTS idx_product_designs_printify_id ON product_designs(printify_product_id);
CREATE INDEX IF NOT EXISTS idx_product_variants_design_id ON product_variants(design_id);
CREATE INDEX IF NOT EXISTS idx_customer_orders_email ON customer_orders(email);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);

-- Update timestamps trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add update triggers
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_designs_updated_at BEFORE UPDATE ON product_designs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customer_orders_updated_at BEFORE UPDATE ON customer_orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS) for better security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_designs ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- Create policies to allow service role full access
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