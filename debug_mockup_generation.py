#!/usr/bin/env python3
"""
Debug script to test mockup generation for all 3 products
This will help us see exactly why the hoodie and hat aren't generating
"""

import json
import logging
from product_service import ProductService
from printify_service import PrintifyService

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_product_cache():
    """Test that our product cache has the expected products"""
    print("🧪 TESTING PRODUCT CACHE")
    print("=" * 50)
    
    service = ProductService()
    
    # Test the 3 products we expect
    test_products = [
        ("12", "Unisex Jersey Short Sleeve Tee"),
        ("92", "Unisex College Hoodie"), 
        ("1447", "Classic Dad Cap")
    ]
    
    for product_id, expected_name in test_products:
        product = service.get_product_by_id(product_id)
        if product:
            print(f"✅ {product_id}: {product['title']}")
            print(f"   Blueprint ID: {product.get('blueprint_id')}")
            print(f"   Print Provider ID: {product.get('print_provider_id')} / {product.get('primary_print_provider_id')}")
            print(f"   Variants: {len(product.get('variants', []))}")
            
            # Test variant selection
            if product_id == "92":  # College Hoodie - use first variant
                first_variant = product.get('variants', [{}])[0] if product.get('variants') else None
                print(f"   First variant: {first_variant.get('id') if first_variant else 'NONE'} - {first_variant.get('color') if first_variant else 'N/A'}")
            else:
                black_variant = service._find_variant_by_color(product_id, 'Black')
                print(f"   Black variant: {black_variant.get('id') if black_variant else 'NOT FOUND'}")
        else:
            print(f"❌ {product_id}: NOT FOUND IN CACHE")
        print()

def test_printify_service():
    """Test Printify service with each product"""
    print("🔧 TESTING PRINTIFY SERVICE")
    print("=" * 50)
    
    service = ProductService()
    printify = PrintifyService()
    
    # Use a test image ID (you can replace with actual one)
    test_image_id = "685d8aee5638948d7abca30a"  # From your logs
    
    test_products = [
        ("12", "Unisex Jersey Short Sleeve Tee"),
        ("92", "Unisex College Hoodie"), 
        ("1447", "Classic Dad Cap")
    ]
    
    for product_id, product_name in test_products:
        print(f"Testing {product_name} (ID: {product_id})")
        
        product = service.get_product_by_id(product_id)
        if not product:
            print(f"❌ Product {product_id} not found in cache")
            continue
            
        # Get variant
        if product_id == "92":  # College Hoodie
            variant = product.get('variants', [{}])[0] if product.get('variants') else None
        else:
            variant = service._find_variant_by_color(product_id, 'Black')
            
        if not variant:
            print(f"❌ No variant found for {product_id}")
            continue
            
        # Get provider info
        blueprint_id = product.get('blueprint_id')
        print_provider_id = product.get('print_provider_id') or product.get('primary_print_provider_id')
        variant_id = variant.get('id')
        
        print(f"   Blueprint: {blueprint_id}")
        print(f"   Provider: {print_provider_id}")
        print(f"   Variant: {variant_id} ({variant.get('color')}/{variant.get('size')})")
        
        # Test if all required fields are present
        if not blueprint_id:
            print(f"❌ Missing blueprint_id for {product_id}")
        elif not print_provider_id:
            print(f"❌ Missing print_provider_id for {product_id}")
        elif not variant_id:
            print(f"❌ Missing variant_id for {product_id}")
        else:
            print(f"✅ All required fields present for {product_id}")
            
            # Try to create design (this is where it might fail)
            try:
                print(f"   🔄 Attempting to create design...")
                result = printify.create_product_design(
                    blueprint_id=blueprint_id,
                    print_provider_id=print_provider_id,
                    variant_id=variant_id,
                    image_id=test_image_id,
                    product_title=f"Test {product_name}"
                )
                
                if result.get("success"):
                    print(f"   ✅ Design creation SUCCEEDED for {product_id}")
                    print(f"      Mockup URL: {result.get('mockup_url', 'N/A')}")
                else:
                    print(f"   ❌ Design creation FAILED for {product_id}")
                    print(f"      Error: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"   ❌ Exception during design creation for {product_id}: {e}")
        
        print()

def check_cache_files():
    """Check that cache files are properly updated"""
    print("📁 CHECKING CACHE FILES")
    print("=" * 50)
    
    files_to_check = [
        "top3_product_cache_optimized.json",
        "drop/top3_product_cache_optimized.json"
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r') as f:
                cache = json.load(f)
            
            print(f"✅ {file_path}")
            print(f"   Products: {len(cache.get('products', {}))}")
            print(f"   Categories: {list(cache.get('category_info', {}).keys())}")
            
            # Check for our specific products
            products = cache.get('products', {})
            for product_id in ['12', '92', '1447']:
                if product_id in products:
                    product = products[product_id]
                    print(f"   {product_id}: {product.get('title')} ✅")
                else:
                    print(f"   {product_id}: NOT FOUND ❌")
            
        except Exception as e:
            print(f"❌ {file_path}: Error - {e}")
        
        print()

if __name__ == "__main__":
    print("🚀 DEBUGGING MOCKUP GENERATION ISSUES")
    print("=" * 60)
    print()
    
    try:
        check_cache_files()
        test_product_cache()
        test_printify_service()
        
        print("🏁 DEBUG COMPLETE")
        print("=" * 60)
        print("Check the output above to see where the issues are occurring.")
        
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        import traceback
        traceback.print_exc()