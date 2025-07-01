#!/usr/bin/env python3
"""
Clear old single-variant products so new master products get created
"""

import os
from dotenv import load_dotenv
from database_service import DatabaseService

# Load environment variables
load_dotenv()

def clear_old_products():
    """Clear old product designs so new master products get created"""
    print("🧹 Clearing old single-variant products")
    print("=" * 50)
    
    database_service = DatabaseService()
    
    # Target image ID that's been used in testing
    target_image_id = "685d8aee5638948d7abca30a"
    
    try:
        if database_service.supabase:
            # Query for products with this image ID
            result = database_service.supabase.table("product_designs").select("*").eq("team_logo_image_id", target_image_id).eq("status", "active").execute()
            
            if result.data:
                print(f"Found {len(result.data)} existing product designs:")
                for design in result.data:
                    product_id = design.get('printify_product_id')
                    blueprint_id = design.get('blueprint_id')
                    name = design.get('name', 'Unknown')
                    default_variant = design.get('default_variant_id')
                    
                    print(f"  - {name} (Blueprint: {blueprint_id}, Product: {product_id}, Variant: {default_variant})")
                
                # Update all to inactive status so new ones get created
                update_result = database_service.supabase.table("product_designs").update({"status": "inactive"}).eq("team_logo_image_id", target_image_id).eq("status", "active").execute()
                
                print(f"\n✅ Marked {len(result.data)} products as inactive")
                print("🔄 New master products will be created on next request")
                
            else:
                print("No existing products found with target image ID")
                
        else:
            print("❌ Supabase not available - using file storage")
            # For file storage, would need to update the JSON file
            print("Manual cleanup needed for file-based storage")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clear_old_products()