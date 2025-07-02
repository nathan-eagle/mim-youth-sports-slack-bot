#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from product_service import product_service

def test_hex_integration():
    """Test hex color integration with product service"""
    
    print("🎨 Testing Hex Color Integration")
    print("=" * 40)
    
    # Test both Jersey Tee and College Hoodie
    products = [
        {"id": "12", "name": "Jersey Tee"},
        {"id": "92", "name": "College Hoodie"}
    ]
    
    for product in products:
        product_id = product["id"]
        product_name = product["name"]
        
        print(f"\n🎯 {product_name} (ID: {product_id})")
        
        # Get regular colors (current method)
        regular_colors = product_service.get_colors_for_product(product_id)
        print(f"   📋 Available colors: {len(regular_colors)}")
        print(f"   First 5: {regular_colors[:5]}")
        
        # Get colors with hex codes (new method)
        colors_with_hex = product_service.get_colors_with_hex_for_product(product_id)
        print(f"\n   🎨 Colors with hex codes:")
        for i, color_data in enumerate(colors_with_hex[:5]):
            name = color_data['name']
            hex_code = color_data['hex']
            print(f"      {i+1}. {name}: {hex_code}")
        
        if len(colors_with_hex) > 5:
            print(f"      ... and {len(colors_with_hex) - 5} more colors")

if __name__ == "__main__":
    test_hex_integration()