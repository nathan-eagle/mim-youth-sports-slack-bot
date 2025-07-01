#!/usr/bin/env python3
"""
Test color-specific mockup generation
"""

import os
from dotenv import load_dotenv
from product_service import ProductService
from printify_service import PrintifyService

# Load environment variables
load_dotenv()

def test_color_generation():
    """Test generating a light blue jersey mockup"""
    print("🧪 Testing color-specific mockup generation")
    print("=" * 50)
    
    product_service = ProductService()
    printify_service = PrintifyService()
    
    # Parse user request
    user_request = "I want the jersey tshirt to be the same light blue color as the logo!"
    selected_variants = product_service.parse_color_preferences(user_request)
    
    if not selected_variants:
        print("❌ No variants parsed from user request")
        return False
    
    # Use the first (priority) match - should be Jersey in Light Blue
    variant_info = selected_variants[0]
    print(f"✅ Using: {variant_info['product_name']} in {variant_info['color']}")
    
    # Test image ID from previous successful tests
    test_image_id = "685d8aee5638948d7abca30a"
    
    # Get product details
    product_id = variant_info['product_id']
    product = product_service.get_product_by_id(product_id)
    
    if not product:
        print(f"❌ Product {product_id} not found")
        return False
    
    # Create mockup
    blueprint_id = product.get('blueprint_id')
    print_provider_id = product.get('print_provider_id') or product.get('primary_print_provider_id')
    variant_id = variant_info['variant']['id']
    
    print(f"📋 Mockup parameters:")
    print(f"   Blueprint: {blueprint_id}")
    print(f"   Provider: {print_provider_id}")
    print(f"   Variant: {variant_id} ({variant_info['color']})")
    print(f"   Image: {test_image_id}")
    
    try:
        result = printify_service.create_product_design(
            blueprint_id=blueprint_id,
            print_provider_id=print_provider_id,
            variant_id=variant_id,
            image_id=test_image_id,
            product_title=f"Custom {variant_info['product_name']} - {variant_info['color']}"
        )
        
        if result.get("success"):
            print(f"✅ SUCCESS! Light blue jersey mockup created")
            print(f"   Product ID: {result.get('product_id')}")
            print(f"   Mockup URL: {result.get('mockup_url')}")
            return True
        else:
            print(f"❌ FAILED: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_color_generation()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Color-specific mockup generation")