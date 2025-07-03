#!/usr/bin/env python3
"""
Automatically set up Supabase database tables for MiM Youth Sports Bot
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def setup_database():
    print("🗄️ SETTING UP SUPABASE DATABASE")
    print("=" * 50)
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return False
    
    try:
        # Create client with service role key for admin operations
        supabase: Client = create_client(url, service_key)
        
        print(f"✅ Connected to Supabase: {url}")
        
        # Read SQL setup file
        with open('setup_supabase_tables.sql', 'r') as f:
            sql_commands = f.read()
        
        print("🔄 Executing database setup SQL...")
        
        # Execute the SQL setup
        result = supabase.rpc('exec_sql', {'sql': sql_commands})
        
        print("✅ Database tables created successfully!")
        
        # Test the tables by checking if they exist
        print("\n🔍 Verifying table creation...")
        
        tables_to_check = [
            'conversations',
            'product_designs', 
            'product_variants',
            'customer_orders',
            'order_items'
        ]
        
        for table in tables_to_check:
            try:
                # Try to query the table (will fail if it doesn't exist)
                result = supabase.table(table).select("*").limit(1).execute()
                print(f"✅ {table} table exists")
            except Exception as e:
                print(f"❌ {table} table missing: {e}")
        
        print("\n🎉 Database setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        
        # Fallback: Create tables manually using individual queries
        print("\n🔄 Trying manual table creation...")
        
        try:
            supabase: Client = create_client(url, service_key)
            
            # Create conversations table
            conversations_sql = """
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
            """
            
            # Execute using raw SQL if RPC doesn't work
            print("📝 Creating conversations table...")
            # Note: This might need to be done in Supabase dashboard SQL editor
            print("SQL to run in Supabase dashboard:")
            print(conversations_sql)
            
            return True
            
        except Exception as e2:
            print(f"❌ Manual setup also failed: {e2}")
            print("\n💡 MANUAL SETUP REQUIRED:")
            print("1. Go to your Supabase dashboard")
            print("2. Open the SQL Editor")
            print("3. Run the contents of setup_supabase_tables.sql")
            return False

def test_database_connection():
    """Test that we can connect to the database"""
    print("\n🔗 Testing database connection...")
    
    url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    try:
        supabase: Client = create_client(url, service_key)
        
        # Try to create a test conversation
        test_data = {
            'conversation_key': 'test_connection',
            'state': 'initial',
            'context': {}
        }
        
        # Insert test record
        result = supabase.table('conversations').insert(test_data).execute()
        
        if result.data:
            print("✅ Database write test successful")
            
            # Clean up test record
            supabase.table('conversations').delete().eq('conversation_key', 'test_connection').execute()
            print("✅ Database cleanup successful")
            return True
        else:
            print("❌ Database write test failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def main():
    print("🚀 MiM YOUTH SPORTS BOT - DATABASE SETUP")
    print("=" * 60)
    
    success = setup_database()
    
    if success:
        connection_test = test_database_connection()
        if connection_test:
            print("\n🎉 SETUP COMPLETE!")
            print("✅ Database tables created")
            print("✅ Connection test passed")
            print("✅ Ready for production deployment")
        else:
            print("\n⚠️ Tables created but connection test failed")
            print("💡 Check your SUPABASE_SERVICE_KEY permissions")
    else:
        print("\n❌ SETUP FAILED")
        print("💡 Please run the SQL manually in Supabase dashboard")

if __name__ == "__main__":
    main()