# Database Setup Instructions

## The Problem
The Slack bot is failing because the Supabase database tables don't exist:
```
ERROR: relation "public.conversations" does not exist
```

## Quick Fix Required

### Step 1: Go to Supabase Dashboard
1. Visit https://supabase.com/dashboard
2. Select your project: `poxxdmruvbuuvhixdvfk.supabase.co`
3. Go to **SQL Editor** in the left sidebar

### Step 2: Run This SQL
Copy and paste this entire SQL script:

```sql
-- Create conversations table for storing chat state
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

-- Create product designs table for storing custom designs
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

-- Create product variants table
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

-- Create customer orders table
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

-- Create order items table
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

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_key ON conversations(conversation_key);
CREATE INDEX IF NOT EXISTS idx_product_designs_printify_id ON product_designs(printify_product_id);
CREATE INDEX IF NOT EXISTS idx_customer_orders_email ON customer_orders(email);
```

### Step 3: Test the Fix
After running the SQL, the bot should work properly. The error will be gone and conversations will be saved to the database.

## Additional Issues Fixed

### OpenAI Version Issue
The local environment had OpenAI v1.54 but the code expects v0.28. This is fixed by:

```bash
pip install openai==0.28
```

### Requirements.txt Update
Make sure your requirements.txt includes:
```
openai==0.28
supabase==2.16.0
```

## Why This Happened
The previous testing used fallback/mock data when the database tables didn't exist, so the local tests passed but production failed. Now with proper database setup, both local and production will work correctly.