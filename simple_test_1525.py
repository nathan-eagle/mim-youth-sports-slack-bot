#!/usr/bin/env python3
"""
Simple test to verify product 1525 variant data is now correct
"""

import json

def test_product_1525_fix():
    """Test that product 1525 variants now have correct color/size fields"""
    print("🧪 TESTING PRODUCT 1525 VARIANT FIELDS")
    print("=" * 60)
    
    try:
        with open("top3_product_cache_optimized.json", 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load cache: {e}")
        return False
    
    # Get product 1525
    product = data.get("products", {}).get("1525", {})
    if not product:
        print("❌ Product 1525 not found")
        return False
    
    print(f"✅ Product found: {product['title']}")
    
    variants = product.get("variants", [])
    if not variants:
        print("❌ No variants found")
        return False
    
    print(f"✅ Found {len(variants)} variants")
    
    # Check first 10 variants for correct structure
    expected_colors = {"Cocoa", "Paragon", "Pink Lemonade", "Charcoal", "Dark Heather", "Maroon", "Navy", "Pistachio", "Purple", "Red", "Royal", "Sand", "White", "Sport Grey", "Tangerine", "Yellow Haze", "Black", "Forest Green", "Light Pink", "Military Green", "Stone Blue", "Sky", "Daisy", "Cement", "Mustard"}
    expected_sizes = {"S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"}
    
    correct_variants = 0
    sample_variants = variants[:10]
    
    print("\n📋 SAMPLE VARIANTS:")
    for i, variant in enumerate(sample_variants):
        color = variant.get("color", "")
        size = variant.get("size", "")
        variant_id = variant.get("id", "")
        
        color_correct = color in expected_colors
        size_correct = size in expected_sizes
        
        status = "✅" if (color_correct and size_correct) else "❌"
        print(f"   {status} Variant {variant_id}: color='{color}', size='{size}'")
        
        if color_correct and size_correct:
            correct_variants += 1
    
    print(f"\n📊 RESULTS:")
    print(f"   Correct variants: {correct_variants}/{len(sample_variants)}")
    success = correct_variants >= 8  # Allow some margin
    
    if success:
        print("✅ Product 1525 variant data is now CORRECT!")
        print("   - Colors are in the 'color' field")
        print("   - Sizes are in the 'size' field")
        
        # Test color extraction
        all_colors = set()
        all_sizes = set()
        for variant in variants:
            if variant.get("available", True):
                all_colors.add(variant.get("color", ""))
                all_sizes.add(variant.get("size", ""))
        
        print(f"\n🎨 AVAILABLE COLORS ({len(all_colors)}):")
        print(f"   {sorted(list(all_colors))[:10]}...")  # First 10
        
        print(f"\n📏 AVAILABLE SIZES ({len(all_sizes)}):")
        print(f"   {sorted(list(all_sizes))}")
        
        return True
    else:
        print("❌ Product 1525 variant data is still BROKEN!")
        return False

if __name__ == "__main__":
    success = test_product_1525_fix()
    print(f"\n{'🎉 FIX SUCCESSFUL' if success else '❌ STILL BROKEN'}")