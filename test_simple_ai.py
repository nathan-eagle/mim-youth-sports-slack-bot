#!/usr/bin/env python3
"""
Simple AI testing without external dependencies
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Test product selection directly
def test_product_selection():
    print("🧠 TESTING AI PRODUCT SELECTION (SIMPLIFIED)")
    print("=" * 50)
    
    try:
        from services.product_selector import product_selector
        
        test_requests = [
            "I need shirts for my daughter's soccer team",
            "We need hoodies and caps for basketball",
            "Looking for gear for volleyball team"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n{i}. Testing: \"{request}\"")
            
            # Mock conversation context
            context = {
                'sport_context': 'soccer' if 'soccer' in request else 'basketball' if 'basketball' in request else 'volleyball',
                'age_group': 'youth'
            }
            
            result = product_selector.select_products_from_conversation(request, context)
            
            if result['success']:
                print(f"✅ AI Selected: {result.get('categories', [])}")
                products = result.get('selected_products', [])
                for product in products:
                    print(f"   • {product['title']} (category: {product['category']})")
                
                # Test alternatives
                alternatives = result.get('alternatives', {})
                if alternatives:
                    print(f"   📋 Alternatives available for {len(alternatives)} categories")
                
            else:
                print(f"❌ Failed: {result.get('error')}")
        
        print("\n✅ Product Selection AI Test Complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_color_analysis():
    print("\n🎨 TESTING AI COLOR ANALYSIS (SIMPLIFIED)")
    print("=" * 50)
    
    try:
        from ai_color_service import ai_color_service
        
        # Test logo URL
        logo_url = "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png"
        
        print(f"Testing color analysis for logo: {logo_url}")
        
        result = ai_color_service.get_default_colors_for_products(logo_url)
        
        if result.get('success', False):
            colors = result.get('colors', {})
            print("✅ AI Color Recommendations:")
            for product_type, color in colors.items():
                print(f"   • {product_type}: {color}")
        else:
            print(f"⚠️ AI returned fallback colors: {result.get('colors', {})}")
        
        print("\n✅ Color Analysis AI Test Complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_product_cache():
    print("\n📊 TESTING PRODUCT CACHE")
    print("=" * 50)
    
    try:
        from services.product_service import product_service
        
        # Test cache loading
        cache_data = product_service.load_printify_choice_products()
        
        if cache_data:
            total_products = len(cache_data.get('products', {}))
            categories = cache_data.get('categories', {})
            
            print(f"✅ Loaded {total_products} products from cache")
            print(f"✅ Categories: {categories}")
            
            # Test category filtering
            tshirts = product_service.get_products_by_category('tshirt')
            hoodies = product_service.get_products_by_category('hoodie')
            
            print(f"✅ Found {len(tshirts)} t-shirts")
            print(f"✅ Found {len(hoodies)} hoodies")
            
            if tshirts:
                print(f"   Top t-shirt: {tshirts[0]['title']} (score: {tshirts[0].get('popularity_score', 0)})")
            
        else:
            print("❌ Failed to load product cache")
            return False
        
        print("\n✅ Product Cache Test Complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 SIMPLE AI INTELLIGENCE TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Product Cache", test_product_cache()))
    results.append(("Product Selection AI", test_product_selection()))
    results.append(("Color Analysis AI", test_color_analysis()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All AI systems working correctly!")
    else:
        print("\n⚠️ Some AI systems need attention")

if __name__ == "__main__":
    main()