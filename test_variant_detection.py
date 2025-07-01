#!/usr/bin/env python3
"""
Test the old product detection and variant support logic
"""

import os
from dotenv import load_dotenv
from printify_service import PrintifyService

# Load environment variables
load_dotenv()

def test_variant_detection():
    """Test if old products support new variants"""
    print("🔍 Testing variant detection on old vs new products")
    print("=" * 60)
    
    printify_service = PrintifyService()
    
    # Test old single-variant product (should fail for other variants)
    old_product_id = "6864030828ceaed3c7031f23"
    
    # Test different variants
    test_variants = [
        (18099, "Black"),      # Original variant (should work)
        (18395, "Navy"),       # Different variant (should fail on old product)
        (18355, "Light Blue")  # Different variant (should fail on old product)
    ]
    
    print(f"🔍 Testing old product: {old_product_id}")
    
    for variant_id, color in test_variants:
        print(f"   Testing {color} variant {variant_id}...")
        
        result = printify_service.get_variant_mockup(old_product_id, variant_id)
        mockup_url = result.get("mockup_url")
        
        if mockup_url:
            print(f"   ✅ {color}: Supported - {mockup_url}")
        else:
            print(f"   ❌ {color}: Not supported (will trigger new product creation)")
    
    print(f"\n🆕 Testing new master product approach...")
    
    # Create new master product
    master_result = printify_service.create_product_design(
        blueprint_id=12,
        print_provider_id=99,
        variant_id=18099,  # Start with black
        image_id="685d8aee5638948d7abca30a",
        product_title="Test New Master Product"
    )
    
    if master_result.get("success"):
        new_product_id = master_result.get("product_id")
        print(f"✅ Created new master product: {new_product_id}")
        
        # Test if it supports multiple variants
        for variant_id, color in test_variants[1:]:  # Skip black, test others
            print(f"   Testing {color} variant {variant_id} on new product...")
            
            result = printify_service.get_variant_mockup(new_product_id, variant_id)
            mockup_url = result.get("mockup_url")
            
            if mockup_url:
                print(f"   ✅ {color}: Supported - {mockup_url}")
            else:
                print(f"   ❌ {color}: Not supported")
    else:
        print(f"❌ Failed to create new master product: {master_result.get('error')}")

if __name__ == "__main__":
    test_variant_detection()