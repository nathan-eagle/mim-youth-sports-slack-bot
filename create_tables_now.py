#!/usr/bin/env python3
"""
Create Supabase tables directly using the REST API
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    print("🗄️ CREATING SUPABASE TABLES")
    print("=" * 40)
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not service_key:
        print("❌ Missing Supabase credentials")
        return False
    
    # Headers for Supabase API
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    # SQL commands to create tables
    sql_commands = [
        # 1. Create conversations table
        """
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
        """,
        
        # 2. Create product_designs table
        """
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
        """,
        
        # 3. Create indexes
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_key ON conversations(conversation_key);
        CREATE INDEX IF NOT EXISTS idx_product_designs_printify_id ON product_designs(printify_product_id);
        """
    ]
    
    # Execute each SQL command
    for i, sql in enumerate(sql_commands, 1):
        print(f"🔄 Executing SQL command {i}...")
        
        try:
            # Use Supabase's SQL execution endpoint
            response = requests.post(
                f"{url}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={'sql': sql.strip()}
            )
            
            if response.status_code in [200, 201, 204]:
                print(f"✅ SQL command {i} executed successfully")
            else:
                print(f"❌ SQL command {i} failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error executing SQL command {i}: {e}")
    
    # Test if tables were created
    print("\n🔍 Testing table creation...")
    
    try:
        # Try to query conversations table
        response = requests.get(
            f"{url}/rest/v1/conversations?limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ conversations table exists and accessible")
            return True
        else:
            print(f"❌ conversations table test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Table test failed: {e}")
        return False

def main():
    success = create_tables()
    
    if success:
        print("\n🎉 DATABASE SETUP COMPLETE!")
        print("✅ Tables created successfully")
        print("✅ Slack bot should now work properly")
    else:
        print("\n❌ AUTOMATIC SETUP FAILED")
        print("\n📋 MANUAL SETUP REQUIRED:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Run this SQL:")
        print("""
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

CREATE INDEX IF NOT EXISTS idx_conversations_key ON conversations(conversation_key);
        """)

if __name__ == "__main__":
    main()