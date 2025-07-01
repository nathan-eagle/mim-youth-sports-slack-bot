#!/usr/bin/env python3
"""
Test the actual bot flow and VERIFY the mockup images show different colors
"""

import os
from dotenv import load_dotenv
from slack_bot import SlackBot
from product_service import ProductService
import requests

# Load environment variables
load_dotenv()

def analyze_mockup_url(url, expected_color):
    """Analyze mockup URL and try to download image to verify color"""
    print(f"   🔍 Analyzing mockup URL: {url}")
    
    # Extract variant info from URL
    url_parts = url.split('/')
    for i, part in enumerate(url_parts):
        if part.isdigit() and len(part) > 4:  # Likely variant ID
            print(f"      Variant ID in URL: {part}")
    
    # Try to download image and check if accessible
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Image accessible (HTTP {response.status_code})")
            print(f"      Expected color: {expected_color}")
            return True
        else:
            print(f"   ❌ Image not accessible (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"   ⚠️ Could not check image accessibility: {e}")
        return False

def test_bot_color_verification():
    """Test the actual bot flow and verify different colors produce different images"""
    print("🧪 TESTING ACTUAL COLOR VERIFICATION")
    print("=" * 70)
    
    slack_bot = SlackBot()
    product_service = ProductService()
    
    # Simulate conversation state
    conversation = {
        "state": "completed",
        "team_info": {"name": "Test Team"},
        "logo_info": {"printify_image_id": "685d8aee5638948d7abca30a"}
    }
    
    # Test different color requests and collect actual mockup URLs
    color_tests = [
        ("black jersey", "Black"),
        ("blue jersey", "Navy/Blue"),
        ("red jersey", "Red")
    ]
    
    results = []
    
    for request_text, expected_color in color_tests:
        print(f"\n🎨 Testing: '{request_text}' (expecting {expected_color})")
        print("-" * 50)
        
        # Parse color preference
        selected_variants = product_service.parse_color_preferences(request_text)
        
        if not selected_variants:
            print(f"   ❌ No color variants parsed for '{request_text}'")
            continue
        
        variant_info = selected_variants[0]
        print(f"   ✅ Parsed: {variant_info['product_name']} in {variant_info['color']}")
        
        # Create product info structure
        product_info = {
            "id": variant_info['product_id'],
            "formatted": {"title": variant_info['product_name']}
        }
        
        selected_variant = variant_info['variant']
        
        # Test the actual bot method
        print(f"   🔄 Creating mockup via bot...")
        result = slack_bot._create_single_mockup_with_variant(
            conversation=conversation,
            logo_info=conversation['logo_info'],
            product_info=product_info,
            selected_variant=selected_variant,
            channel="test_channel",
            user="test_user"
        )
        
        if result.get("image_url"):
            mockup_url = result["image_url"]
            print(f"   ✅ Mockup created: {result.get('product_title', 'Unknown')}")
            
            # Analyze the mockup URL
            is_accessible = analyze_mockup_url(mockup_url, expected_color)
            
            results.append({
                "request": request_text,
                "expected_color": expected_color,
                "actual_color": variant_info['color'],
                "mockup_url": mockup_url,
                "accessible": is_accessible,
                "product_id": result.get("product_id")
            })
        else:
            print(f"   ❌ FAILED to create mockup: {result}")
    
    # Analyze results
    print(f"\n📊 FINAL ANALYSIS")
    print("=" * 70)
    
    unique_urls = set(r["mockup_url"] for r in results)
    unique_product_ids = set(r["product_id"] for r in results)
    
    print(f"Total tests: {len(results)}")
    print(f"Unique mockup URLs: {len(unique_urls)}")
    print(f"Unique product IDs: {len(unique_product_ids)}")
    
    print(f"\nDetailed Results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['request']} → {result['actual_color']}")
        print(f"   Product ID: {result['product_id']}")
        print(f"   Mockup URL: {result['mockup_url']}")
        print(f"   Accessible: {'✅' if result['accessible'] else '❌'}")
    
    # Check if we got different images for different colors
    if len(unique_urls) == len(results):
        print(f"\n🎉 SUCCESS: All {len(results)} color requests produced DIFFERENT mockup URLs!")
        print("✅ Colors are working correctly!")
        return True
    elif len(unique_urls) == 1:
        print(f"\n❌ FAILURE: All color requests produced the SAME mockup URL")
        print("❌ Colors are NOT working - still showing same image")
        return False
    else:
        print(f"\n⚠️ PARTIAL: Got {len(unique_urls)} unique URLs from {len(results)} requests")
        print("⚠️ Some colors working, some not")
        return False

if __name__ == "__main__":
    success = test_bot_color_verification()
    print(f"\n{'🎉 COLORS WORKING' if success else '❌ COLORS STILL BROKEN'}")