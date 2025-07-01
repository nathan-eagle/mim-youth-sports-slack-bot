#!/usr/bin/env python3
"""
Get Printify Shop ID and test mockup creation
"""

import os
import json
import requests
from product_service import ProductService
from printify_service import PrintifyService

def get_printify_shop_id():
    """Get the shop ID from Printify API"""
    api_token = os.getenv('PRINTIFY_API_TOKEN')
    if not api_token:
        print("❌ PRINTIFY_API_TOKEN not found in environment")
        return None
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get("https://api.printify.com/v1/shops.json", headers=headers)
        if response.status_code == 200:
            shops = response.json()
            print(f"🏪 Found {len(shops)} shop(s):")
            for shop in shops:
                shop_id = shop.get('id')
                shop_title = shop.get('title', 'Untitled Shop')
                print(f"   Shop ID: {shop_id} - {shop_title}")
            
            return shops[0].get('id') if shops else None
        else:
            print(f"❌ Failed to get shops: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting shop ID: {e}")
        return None

def test_mockup_with_shop_id(shop_id):
    """Test mockup creation with the shop ID"""
    print(f"\n🧪 Testing mockup creation with Shop ID: {shop_id}")
    
    # Set the shop ID in environment
    os.environ['PRINTIFY_SHOP_ID'] = str(shop_id)
    
    # Create services
    product_service = ProductService()
    printify_service = PrintifyService()
    
    # Test with Jersey Tee
    product = product_service.get_product_by_id('12')
    if not product:
        print("❌ Could not get Jersey Tee from cache")
        return
    
    # Get a variant
    black_variant = product_service._find_variant_by_color('12', 'Black')
    if not black_variant:
        print("❌ Could not find black variant")
        return
    
    blueprint_id = product.get('blueprint_id')
    print_provider_id = product.get('print_provider_id') or product.get('primary_print_provider_id')
    variant_id = black_variant.get('id')
    
    print(f"📋 Test parameters:")
    print(f"   Blueprint: {blueprint_id}")
    print(f"   Provider: {print_provider_id}")
    print(f"   Variant: {variant_id} ({black_variant.get('color')}/{black_variant.get('size')})")
    print(f"   Shop ID: {shop_id}")
    
    # Use a test image ID
    test_image_id = "685d8aee5638948d7abca30a"  # From previous uploads
    
    try:
        print(f"\n🔄 Attempting to create mockup...")
        result = printify_service.create_product_design(
            blueprint_id=blueprint_id,
            print_provider_id=print_provider_id,
            variant_id=variant_id,
            image_id=test_image_id,
            product_title="Test Jersey Tee with Shop ID"
        )
        
        if result.get("success"):
            print(f"✅ SUCCESS! Mockup created successfully")
            print(f"   Product ID: {result.get('product_id')}")
            print(f"   Mockup URL: {result.get('mockup_url')}")
            return True
        else:
            print(f"❌ FAILED: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during mockup creation: {e}")
        return False

def main():
    print("🔍 GETTING PRINTIFY SHOP ID AND TESTING MOCKUP CREATION")
    print("=" * 60)
    
    # Get shop ID
    shop_id = get_printify_shop_id()
    if not shop_id:
        print("❌ Could not get shop ID")
        return
    
    # Test mockup creation
    success = test_mockup_with_shop_id(shop_id)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 SUCCESS! Mockup creation works with shop ID")
        print(f"💡 Remember to set PRINTIFY_SHOP_ID={shop_id} in production")
    else:
        print("❌ Mockup creation still failed even with shop ID")
        print("   Additional investigation needed")

if __name__ == "__main__":
    main()