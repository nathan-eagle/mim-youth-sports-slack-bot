#!/usr/bin/env python3
"""
Test the full mockup generation flow to ensure all 3 products are created
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services
from product_service import ProductService
from printify_service import PrintifyService
from logo_processor import LogoProcessor

def test_full_mockup_generation():
    """Test creating mockups for all 3 target products"""
    print("🧪 TESTING FULL MOCKUP GENERATION FOR ALL 3 PRODUCTS")
    print("=" * 65)
    
    # Initialize services
    product_service = ProductService()
    printify_service = PrintifyService()
    logo_processor = LogoProcessor()
    
    # Use a test image ID that we know works from previous tests
    test_image_id = "685d8aee5638948d7abca30a"  # From previous successful uploads
    
    # Test with all 3 products from our cache
    target_products = [
        {"id": "12", "name": "Unisex Jersey Short Sleeve Tee"},
        {"id": "92", "name": "Unisex College Hoodie"}, 
        {"id": "6", "name": "Unisex Heavy Cotton Tee"}
    ]
    
    print(f"🎯 Target products: {len(target_products)}")
    for product in target_products:
        print(f"   - {product['name']} (ID: {product['id']})")
    
    print(f"\n🖼️  Using test image ID: {test_image_id}")
    image_id = test_image_id
    
    # Test mockup generation for each product
    success_count = 0
    results = []
    
    for product_info in target_products:
        product_id = product_info["id"]
        product_name = product_info["name"]
        
        print(f"\n🔄 Testing {product_name}...")
        
        # Get product from cache
        product = product_service.get_product_by_id(product_id)
        if not product:
            print(f"❌ Product {product_id} not found in cache")
            continue
        
        # Get a black variant
        black_variant = product_service._find_variant_by_color(product_id, 'Black')
        if not black_variant:
            # Try to get any variant
            variants = product_service.get_product_variants(product_id)
            black_variant = variants[0] if variants else None
        
        if not black_variant:
            print(f"❌ No variants found for {product_name}")
            continue
        
        # Get required parameters
        blueprint_id = product.get('blueprint_id')
        print_provider_id = product.get('print_provider_id') or product.get('primary_print_provider_id')
        variant_id = black_variant.get('id')
        
        print(f"   Blueprint: {blueprint_id}, Provider: {print_provider_id}, Variant: {variant_id}")
        
        # Create mockup
        try:
            result = printify_service.create_product_design(
                blueprint_id=blueprint_id,
                print_provider_id=print_provider_id,
                variant_id=variant_id,
                image_id=image_id,
                product_title=f"Test {product_name}"
            )
            
            if result.get("success"):
                print(f"✅ SUCCESS: {product_name}")
                print(f"   Product ID: {result.get('product_id')}")
                print(f"   Mockup URL: {result.get('mockup_url')}")
                success_count += 1
                results.append({
                    "product_name": product_name,
                    "product_id": result.get('product_id'),
                    "mockup_url": result.get('mockup_url')
                })
            else:
                print(f"❌ FAILED: {product_name} - {result.get('error')}")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {product_name} - {e}")
    
    print(f"\n" + "=" * 65)
    print(f"🎯 RESULTS: {success_count}/{len(target_products)} products created successfully")
    
    if success_count == len(target_products):
        print("🎉 ALL PRODUCTS CREATED SUCCESSFULLY!")
        print("✅ The Slack bot should now be able to generate all 3 mockups")
        
        print(f"\n📋 Summary of created products:")
        for result in results:
            print(f"   - {result['product_name']}: {result['mockup_url']}")
        
        return True
    else:
        print(f"❌ Only {success_count} out of {len(target_products)} products worked")
        print("   Investigation needed for failed products")
        return False

if __name__ == "__main__":
    success = test_full_mockup_generation()
    sys.exit(0 if success else 1)