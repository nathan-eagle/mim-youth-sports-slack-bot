#!/usr/bin/env python3
"""
Debug: Examine the actual product structure to see mockup images
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_product_images():
    """Debug what images Printify actually generates for products with multiple variants"""
    print("🔍 Debugging Product Images Structure")
    print("=" * 60)
    
    api_token = os.getenv('PRINTIFY_API_TOKEN')
    shop_id = os.getenv('PRINTIFY_SHOP_ID', '9564969')
    
    if not api_token:
        print("❌ PRINTIFY_API_TOKEN not found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Use the master product we just created
    product_id = "68641785864ba497d50b113f"
    
    print(f"📦 Examining product: {product_id}")
    
    try:
        response = requests.get(
            f"https://api.printify.com/v1/shops/{shop_id}/products/{product_id}.json",
            headers=headers
        )
        
        if response.status_code == 200:
            product_data = response.json()
            
            print(f"✅ Product found: {product_data.get('title')}")
            print(f"   Total variants: {len(product_data.get('variants', []))}")
            
            images = product_data.get('images', [])
            print(f"   Total images: {len(images)}")
            
            # Analyze each image
            for i, image in enumerate(images):
                print(f"\n📸 Image {i+1}:")
                print(f"   URL: {image.get('src')}")
                print(f"   Position: {image.get('position')}")
                print(f"   Is Default: {image.get('is_default')}")
                print(f"   Variant IDs: {image.get('variant_ids', [])[:10]}..." if len(image.get('variant_ids', [])) > 10 else f"   Variant IDs: {image.get('variant_ids', [])}")
                
                # Check if this image is for specific variants
                variant_ids = image.get('variant_ids', [])
                if len(variant_ids) == 1:
                    print(f"   🎯 This is a variant-specific image!")
                elif len(variant_ids) > 100:
                    print(f"   📋 This covers many/all variants")
                else:
                    print(f"   📝 This covers {len(variant_ids)} variants")
            
            # Look for patterns in image URLs
            print(f"\n🔍 URL Analysis:")
            unique_urls = set(img.get('src') for img in images)
            print(f"   Unique image URLs: {len(unique_urls)}")
            
            if len(unique_urls) == 1:
                print(f"   ⚠️ All images have the same URL - Printify may not generate separate mockups")
            else:
                print(f"   ✅ Found {len(unique_urls)} different image URLs")
                
        else:
            print(f"❌ Failed to get product: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_product_images()