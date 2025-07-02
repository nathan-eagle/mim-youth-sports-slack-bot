#!/usr/bin/env python3
"""
Test that the Fleece Hoodie color selection now works after fixing the swapped fields
"""

from product_service import ProductService
from openai_service import OpenAIService

def test_fleece_hoodie():
    """Test fleece hoodie product and color selection"""
    print("🧪 TESTING FLEECE HOODIE AFTER FIELD FIX")
    print("=" * 60)
    
    product_service = ProductService()
    openai_service = OpenAIService()
    
    # Test 1: Product selection
    print("1️⃣ Testing product selection...")
    product_match = product_service.find_product_by_intent_ai("Unisex Midweight Softstyle Fleece Hoodie")
    
    if product_match:
        print(f"✅ Product found: {product_match['product']['title']}")
        print(f"   Product ID: {product_match['id']}")
    else:
        print("❌ Product not found")
        return False
    
    # Test 2: Get available colors
    print("\n2️⃣ Testing color availability...")
    product_id = product_match['id']
    available_colors = product_service.get_colors_for_product(product_id)
    
    print(f"✅ Found {len(available_colors)} colors")
    print(f"   First 10 colors: {available_colors[:10]}")
    
    # Test 3: AI color selection
    print("\n3️⃣ Testing AI color selection for 'red' request...")
    default_logo_url = "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png/v1/fill/w_190,h_190,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/MiM%20Color%20Logo.png"
    
    ai_result = openai_service.analyze_color_request(
        user_request="red hoodie",
        logo_url=default_logo_url,
        available_colors=available_colors,
        product_name="Unisex Midweight Softstyle Fleece Hoodie"
    )
    
    print(f"   AI selected color: {ai_result.get('best_color_match')}")
    print(f"   Confidence: {ai_result.get('confidence')}")
    print(f"   Reasoning: {ai_result.get('reasoning')}")
    
    # Test 4: Find specific variant
    print("\n4️⃣ Testing variant lookup...")
    selected_color = ai_result.get('best_color_match')
    if selected_color:
        variant = product_service.find_variant_by_options(product_id, selected_color, "M")
        if variant:
            print(f"✅ Found variant: ID {variant['id']}, Color: {variant['color']}, Size: {variant['size']}")
            print(f"   Price: ${variant['price']}")
        else:
            print(f"❌ No variant found for {selected_color} in size M")
            return False
    
    # Test 5: Parse color preferences with AI
    print("\n5️⃣ Testing full color preference parsing...")
    variants = product_service.parse_color_preferences_ai("red fleece hoodie", default_logo_url)
    
    if variants:
        variant_info = variants[0]
        print(f"✅ Parsed successfully:")
        print(f"   Product: {variant_info['product_name']}")
        print(f"   Color: {variant_info['color']}")
        print(f"   Variant ID: {variant_info['variant']['id']}")
        print(f"   AI Confidence: {variant_info['ai_confidence']}")
    else:
        print("❌ Color preference parsing failed")
        return False
    
    print("\n🎉 ALL TESTS PASSED! Fleece Hoodie is working correctly!")
    return True

if __name__ == "__main__":
    success = test_fleece_hoodie()
    print(f"\n{'🎉 FLEECE HOODIE WORKING' if success else '❌ STILL BROKEN'}")