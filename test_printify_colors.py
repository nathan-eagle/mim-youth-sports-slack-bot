#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_printify_color_data():
    """Test what color information Printify API actually provides"""
    
    api_token = os.getenv('PRINTIFY_API_TOKEN')
    if not api_token:
        print("❌ PRINTIFY_API_TOKEN not found")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test our main products
    test_products = [
        {"id": 12, "name": "Jersey Tee"},
        {"id": 92, "name": "College Hoodie"}
    ]
    
    for product in test_products:
        blueprint_id = product["id"]
        product_name = product["name"]
        
        print(f"\n🎯 Testing {product_name} (Blueprint {blueprint_id})")
        
        # Get blueprint details
        blueprint_url = f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}.json"
        try:
            response = requests.get(blueprint_url, headers=headers)
            if response.status_code == 200:
                blueprint_data = response.json()
                
                # Check if blueprint has color information
                if 'options' in blueprint_data:
                    for option in blueprint_data['options']:
                        if option.get('type') == 'color' or 'color' in option.get('name', '').lower():
                            print(f"   🎨 Found color option: {option.get('name')}")
                            
                            # Check for hex codes in values
                            if 'values' in option:
                                print(f"      📊 {len(option['values'])} color values available")
                                
                                # Show first few colors with hex codes
                                for i, color_value in enumerate(option['values'][:5]):
                                    title = color_value.get('title', 'Unknown')
                                    colors = color_value.get('colors', [])
                                    print(f"         {i+1}. {title}: {colors}")
                                
                                if len(option['values']) > 5:
                                    print(f"         ... and {len(option['values']) - 5} more colors")
                            break
                else:
                    print("   ❌ No color options found in blueprint")
            else:
                print(f"   ❌ Failed to get blueprint: {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Error getting blueprint: {e}")
        
        # Also test variants endpoint
        print(f"   🔍 Checking variants for provider 99...")
        variants_url = f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers/99/variants.json"
        try:
            response = requests.get(variants_url, headers=headers)
            if response.status_code == 200:
                variants_data = response.json()
                variants = variants_data.get('variants', variants_data if isinstance(variants_data, list) else [])
                
                print(f"      📦 Found {len(variants)} variants")
                
                # Check first few variants for color info
                for i, variant in enumerate(variants[:3]):
                    variant_id = variant.get('id')
                    title = variant.get('title', '')
                    
                    # Look for color-related fields
                    color_fields = {}
                    for key, value in variant.items():
                        if 'color' in key.lower() or (isinstance(value, str) and value.startswith('#')):
                            color_fields[key] = value
                    
                    print(f"         Variant {i+1} ({variant_id}): {title}")
                    if color_fields:
                        print(f"            Color fields: {color_fields}")
                    
                    # Check if variant has options
                    if 'options' in variant:
                        for option in variant['options']:
                            if 'color' in option.get('name', '').lower():
                                print(f"            Color option: {option}")
            else:
                print(f"      ❌ Failed to get variants: {response.status_code}")
        
        except Exception as e:
            print(f"      ❌ Error getting variants: {e}")

if __name__ == "__main__":
    print("🔍 TESTING PRINTIFY COLOR DATA AVAILABILITY")
    print("=" * 50)
    test_printify_color_data()
    print("\n✅ Color data test complete!")