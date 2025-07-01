#!/usr/bin/env python3
"""
Test the new master product approach - single product with all variants
"""

import os
from dotenv import load_dotenv
from product_service import ProductService
from printify_service import PrintifyService

# Load environment variables
load_dotenv()

def test_master_product_approach():
    """Test creating one product with all variants and getting different color mockups"""
    print("🧪 Testing Master Product Approach")
    print("=" * 60)
    
    product_service = ProductService()
    printify_service = PrintifyService()
    
    # Test with Jersey Tee
    product_id = '12'  # Unisex Jersey Short Sleeve Tee
    product = product_service.get_product_by_id(product_id)
    
    if not product:
        print(f"❌ Product {product_id} not found")
        return False
    
    print(f"🎯 Testing: {product.get('title')}")
    print(f"   Blueprint: {product.get('blueprint_id')}")
    print(f"   Provider: {product.get('print_provider_id')}")
    
    # Test image ID
    test_image_id = "685d8aee5638948d7abca30a"
    
    # Get available variants for this product
    variants = product_service.get_product_variants(product_id)
    print(f"   Available variants: {len(variants)}")
    
    # Test creating product with black variant first (master product)
    black_variant = product_service._find_variant_by_color(product_id, 'Black')
    if not black_variant:
        print("❌ Could not find black variant")
        return False
    
    print(f"\n📦 Step 1: Create master product with black variant {black_variant['id']}")
    
    master_result = printify_service.create_product_design(
        blueprint_id=product.get('blueprint_id'),
        print_provider_id=product.get('print_provider_id') or product.get('primary_print_provider_id'),
        variant_id=black_variant['id'],
        image_id=test_image_id,
        product_title="Test Master Product - Jersey Tee"
    )
    
    if not master_result.get("success"):
        print(f"❌ Failed to create master product: {master_result.get('error')}")
        return False
    
    master_product_id = master_result.get("product_id")
    print(f"✅ Master product created: {master_product_id}")
    print(f"   Default mockup: {master_result.get('mockup_url')}")
    
    # Test getting variant-specific mockups from the same product
    test_colors = ['Navy', 'Light Blue', 'Royal']
    variant_mockups = []
    
    print(f"\n🎨 Step 2: Get variant-specific mockups from master product")
    
    for color in test_colors:
        color_variant = product_service._find_variant_by_color(product_id, color)
        if color_variant:
            print(f"   Testing {color} variant {color_variant['id']}...")
            
            mockup_result = printify_service.get_variant_mockup(master_product_id, color_variant['id'])
            mockup_url = mockup_result.get("mockup_url")
            
            if mockup_url:
                print(f"   ✅ {color}: {mockup_url}")
                variant_mockups.append((color, mockup_url))
            else:
                print(f"   ❌ {color}: No mockup found")
        else:
            print(f"   ⚠️ {color}: Variant not found")
    
    # Summary
    print(f"\n📊 RESULTS:")
    print(f"   Master product ID: {master_product_id}")
    print(f"   Variant mockups found: {len(variant_mockups)}")
    
    if len(variant_mockups) > 0:
        print(f"   ✅ SUCCESS: Got {len(variant_mockups)} different color mockups from same product!")
        return True
    else:
        print(f"   ❌ FAILED: Could not get variant-specific mockups")
        return False

if __name__ == "__main__":
    success = test_master_product_approach()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Master product approach")