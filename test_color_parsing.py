#!/usr/bin/env python3
"""
Test color parsing functionality
"""

import sys
from product_service import ProductService

def test_color_parsing():
    """Test the color parsing with the user's request"""
    print("🧪 Testing color parsing functionality")
    print("=" * 50)
    
    product_service = ProductService()
    
    # Test the user's actual request
    user_input = "I want the jersey tshirt to be the same light blue color as the logo!"
    
    print(f"User input: '{user_input}'")
    
    # Parse color preferences
    selected_variants = product_service.parse_color_preferences(user_input)
    
    print(f"Parsed variants: {len(selected_variants)}")
    
    if selected_variants:
        for variant_info in selected_variants:
            print(f"✅ Found match:")
            print(f"   Product ID: {variant_info['product_id']}")
            print(f"   Product: {variant_info['product_name']}")
            print(f"   Color: {variant_info['color']}")
            print(f"   Variant ID: {variant_info['variant']['id']}")
    else:
        print("❌ No color variants parsed")
        
        # Debug: Check available colors for jersey
        print("\n🔍 Available colors for Jersey T-shirt (ID: 12):")
        colors = product_service.get_colors_for_product('12')
        for i, color in enumerate(colors[:20]):  # Show first 20
            print(f"   {i+1}. {color}")
        if len(colors) > 20:
            print(f"   ... and {len(colors) - 20} more")
    
    # Test a few more variations
    test_inputs = [
        "light blue jersey",
        "blue jersey shirt", 
        "jersey t-shirt light blue",
        "light blue t-shirt"
    ]
    
    print("\n🧪 Testing variations:")
    for test_input in test_inputs:
        variants = product_service.parse_color_preferences(test_input)
        print(f"'{test_input}' -> {len(variants)} matches")
        for variant in variants:
            print(f"   {variant['product_name']} in {variant['color']}")

if __name__ == "__main__":
    test_color_parsing()