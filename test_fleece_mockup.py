#!/usr/bin/env python3
"""
Test Fleece Hoodie mockup generation to debug Slack image display issues
"""

import os
import requests
from dotenv import load_dotenv
from printify_service import printify_service
from product_service import product_service

load_dotenv()

def test_fleece_hoodie_mockup():
    """Test fleece hoodie mockup generation and URL validation"""
    print("🧪 TESTING FLEECE HOODIE MOCKUP GENERATION")
    print("=" * 60)
    
    # Get product info
    product = product_service.get_product_by_id("1525")
    if not product:
        print("❌ Product 1525 not found")
        return False
    
    print(f"✅ Product: {product['title']}")
    
    # Find Cocoa color variant
    cocoa_variant = None
    for variant in product.get('variants', []):
        if variant.get('color') == 'Cocoa' and variant.get('size') == 'S':
            cocoa_variant = variant
            break
    
    if not cocoa_variant:
        print("❌ Cocoa variant not found")
        return False
    
    print(f"✅ Found Cocoa variant: ID {cocoa_variant['id']}")
    
    # Test mockup creation
    print("\n🔄 Creating mockup...")
    
    result = printify_service.create_product_design(
        image_id="685d8aee5638948d7abca30a",  # Default MiM logo
        blueprint_id=1525,
        print_provider_id=99,
        title="Test Fleece Hoodie",
        variant_id=cocoa_variant['id']
    )
    
    if not result.get("success"):
        print(f"❌ Failed to create mockup: {result}")
        return False
    
    mockup_url = result.get("mockup_url")
    print(f"✅ Mockup created: {mockup_url}")
    
    # Test if URL is accessible
    print("\n🔍 Testing URL accessibility...")
    try:
        response = requests.get(mockup_url, timeout=10)
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Content-Length: {response.headers.get('Content-Length', 'Unknown')} bytes")
        
        if response.status_code == 200:
            print("✅ URL is accessible")
            
            # Check if it's actually an image
            content_type = response.headers.get('Content-Type', '').lower()
            if 'image' in content_type:
                print("✅ Content is an image")
            else:
                print(f"⚠️  Content type doesn't look like an image: {content_type}")
        else:
            print(f"❌ URL returned error status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to access URL: {e}")
        return False
    
    # Get the product to check mockup URLs
    print("\n🔍 Checking product mockup structure...")
    product_id = result.get("product_id")
    
    try:
        response = requests.get(
            f"https://api.printify.com/v1/shops/{printify_service.shop_id}/products/{product_id}.json",
            headers=printify_service.headers
        )
        
        if response.status_code == 200:
            product_data = response.json()
            images = product_data.get('images', [])
            print(f"✅ Product has {len(images)} images")
            
            # Check for variant-specific images
            variant_specific_count = 0
            for img in images[:5]:  # First 5 images
                variant_ids = img.get('variant_ids', [])
                if variant_ids:
                    variant_specific_count += 1
                    print(f"   Image for variants {variant_ids[:3]}...: {img.get('src')[:80]}...")
            
            print(f"✅ Found {variant_specific_count} variant-specific images")
            
    except Exception as e:
        print(f"⚠️  Failed to get product details: {e}")
    
    print("\n🎉 FLEECE HOODIE MOCKUP TEST COMPLETE")
    return True

if __name__ == "__main__":
    success = test_fleece_hoodie_mockup()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")