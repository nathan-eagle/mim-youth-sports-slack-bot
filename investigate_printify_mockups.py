#!/usr/bin/env python3
"""
Investigate why Printify mockups aren't showing different colors
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def investigate_product_mockups():
    """Investigate the actual Printify product structure"""
    print("🔍 INVESTIGATING PRINTIFY PRODUCT MOCKUP GENERATION")
    print("=" * 70)
    
    api_token = os.getenv('PRINTIFY_API_TOKEN')
    shop_id = os.getenv('PRINTIFY_SHOP_ID', '9564969')
    
    if not api_token:
        print("❌ PRINTIFY_API_TOKEN not found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test with the actual products from drop_data.json
    test_products = [
        "6864162ddc1c5f6b050eb4c1",  # From drop_data.json
        "68641c1278d26655fa0c7383",  # From drop_data.json
        "68641c1fd9fa9f6f180d7b7b"   # From drop_data.json
    ]
    
    for i, product_id in enumerate(test_products, 1):
        print(f"\n📦 Product {i}: {product_id}")
        print("-" * 50)
        
        try:
            response = requests.get(
                f"https://api.printify.com/v1/shops/{shop_id}/products/{product_id}.json",
                headers=headers
            )
            
            if response.status_code == 200:
                product_data = response.json()
                
                print(f"   Title: {product_data.get('title')}")
                print(f"   Status: {product_data.get('status')}")
                print(f"   Total variants: {len(product_data.get('variants', []))}")
                
                # Check images
                images = product_data.get('images', [])
                print(f"   Total images: {len(images)}")
                
                if images:
                    print(f"   📸 Image breakdown:")
                    for j, image in enumerate(images[:10]):  # Show first 10
                        variant_ids = image.get('variant_ids', [])
                        position = image.get('position', 'unknown')
                        is_default = image.get('is_default', False)
                        src = image.get('src', '')
                        
                        print(f"      {j+1}. Position: {position}, Default: {is_default}")
                        print(f"         Variants: {len(variant_ids)} ({variant_ids[:3]}{'...' if len(variant_ids) > 3 else ''})")
                        print(f"         URL: {src[-50:]}...")  # Last 50 chars
                
                # Check specific variants we're interested in
                test_variants = [18486, 18395, 12100]  # From the URLs
                print(f"\n   🎯 Testing specific variants:")
                
                for variant_id in test_variants:
                    # Look for images with this specific variant
                    variant_images = [img for img in images if variant_id in img.get('variant_ids', [])]
                    if variant_images:
                        print(f"      Variant {variant_id}: {len(variant_images)} image(s)")
                        for img in variant_images:
                            print(f"         → {img.get('position')} ({img.get('src', '')[-40:]}...)")
                    else:
                        print(f"      Variant {variant_id}: ❌ No specific image found")
                
                # Check if all images are the same
                unique_image_urls = set(img.get('src') for img in images)
                print(f"\n   🔍 Image URL analysis:")
                print(f"      Total images: {len(images)}")
                print(f"      Unique URLs: {len(unique_image_urls)}")
                
                if len(unique_image_urls) == 1:
                    print(f"      ⚠️ ALL IMAGES USE THE SAME URL!")
                    print(f"      This explains why colors look identical")
                elif len(unique_image_urls) < len(images):
                    print(f"      ⚠️ Some images share URLs ({len(images) - len(unique_image_urls)} duplicates)")
                else:
                    print(f"      ✅ All images have unique URLs")
                    
            else:
                print(f"   ❌ Failed to get product: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎯 CONCLUSION:")
    print("If all products show 'ALL IMAGES USE THE SAME URL', then Printify")
    print("is not generating variant-specific mockups, which explains why")
    print("all colors look the same despite different variant IDs in URLs.")

if __name__ == "__main__":
    investigate_product_mockups()