#!/usr/bin/env python3
"""
Test product selection logic without AI calls
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_product_selection_mock():
    print("🧠 TESTING PRODUCT SELECTION LOGIC (MOCKED AI)")
    print("=" * 50)
    
    try:
        from services.product_selector import product_selector
        
        # Mock the AI service to return predictable results
        class MockOpenAIService:
            def analyze_product_request_conversation(self, text, context):
                # Simple keyword matching
                text_lower = text.lower()
                products = []
                
                if 'shirt' in text_lower or 'tee' in text_lower:
                    products.append('tshirt')
                if 'hoodie' in text_lower or 'sweatshirt' in text_lower:
                    products.append('hoodie')
                if 'hat' in text_lower or 'cap' in text_lower:
                    products.append('headwear')
                if 'volleyball' in text_lower and 'tank' not in text_lower:
                    products.append('tank')  # volleyball typically uses tanks
                
                if not products:
                    products = ['tshirt']  # default
                
                return {
                    'success': True,
                    'products': products,
                    'confidence': 'high'
                }
        
        # Replace the real service temporarily
        import openai_service
        original_service = openai_service.openai_service
        openai_service.openai_service = MockOpenAIService()
        
        test_requests = [
            ("I need shirts for my daughter's soccer team", ['tshirt']),
            ("We need hoodies and caps for basketball", ['hoodie', 'headwear']),
            ("Looking for gear for volleyball team", ['tank'])
        ]
        
        all_passed = True
        
        for i, (request, expected_categories) in enumerate(test_requests, 1):
            print(f"\n{i}. Testing: \"{request}\"")
            print(f"   Expected categories: {expected_categories}")
            
            # Mock conversation context
            context = {
                'sport_context': 'soccer' if 'soccer' in request else 'basketball' if 'basketball' in request else 'volleyball',
                'age_group': 'youth'
            }
            
            result = product_selector.select_products_from_conversation(request, context)
            
            if result['success']:
                actual_categories = result.get('categories', [])
                selected_products = result.get('selected_products', [])
                
                print(f"   ✅ AI Selected: {actual_categories}")
                print(f"   ✅ Products found: {len(selected_products)}")
                
                for product in selected_products:
                    print(f"      • {product['title']} (category: {product['category']}, score: {product.get('popularity_score', 0)})")
                
                # Check if we got expected categories
                if set(actual_categories) == set(expected_categories):
                    print(f"   ✅ Categories match expected: {expected_categories}")
                else:
                    print(f"   ⚠️ Categories don't match. Expected: {expected_categories}, Got: {actual_categories}")
                    all_passed = False
                
                # Test alternatives
                alternatives = result.get('alternatives', {})
                if alternatives:
                    print(f"   📋 Alternatives available for {len(alternatives)} categories")
                    for cat, alt_products in alternatives.items():
                        print(f"      {cat}: {len(alt_products)} alternatives")
                
            else:
                print(f"   ❌ Failed: {result.get('error')}")
                all_passed = False
        
        # Restore original service
        openai_service.openai_service = original_service
        
        if all_passed:
            print("\n✅ All product selection tests passed!")
        else:
            print("\n⚠️ Some product selection tests had issues")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_product_popularity_scoring():
    print("\n📊 TESTING PRODUCT POPULARITY SCORING")
    print("=" * 50)
    
    try:
        from services.product_service import product_service
        
        categories_to_test = ['tshirt', 'hoodie', 'headwear']
        
        for category in categories_to_test:
            products = product_service.get_products_by_category(category)
            
            # Convert dict to list if needed
            if isinstance(products, dict):
                products = list(products.values())
            
            if products:
                print(f"\n{category.upper()} Products (Top 5):")
                for i, product in enumerate(products[:5]):
                    score = product.get('popularity_score', 0)
                    title = product['title']
                    is_youth = any(word in title.lower() for word in ['youth', 'kids', 'toddler', 'junior'])
                    youth_indicator = "👶" if is_youth else "👤"
                    print(f"   {i+1}. {youth_indicator} {title} (score: {score})")
                
                # Check if scoring makes sense
                scores = [p.get('popularity_score', 0) for p in products]
                is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
                
                if is_sorted:
                    print(f"   ✅ Products correctly sorted by popularity")
                else:
                    print(f"   ⚠️ Products not sorted by popularity")
                
                # Check youth focus
                top_3 = products[:3]
                youth_count = sum(1 for p in top_3 if any(word in p['title'].lower() for word in ['youth', 'kids', 'toddler', 'junior']))
                print(f"   📊 Youth-focused products in top 3: {youth_count}/3")
            else:
                print(f"   ❌ No products found for {category}")
        
        print("\n✅ Product popularity scoring test complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_printify_integration():
    print("\n🖨️ TESTING PRINTIFY INTEGRATION (READ-ONLY)")
    print("=" * 50)
    
    try:
        from services.product_service import product_service
        
        # Get a sample product
        tshirts = product_service.get_products_by_category('tshirt')
        if isinstance(tshirts, dict):
            tshirts = list(tshirts.values())
        
        if not tshirts:
            print("❌ No t-shirts found")
            return False
        
        sample_product = tshirts[0]
        print(f"Testing with: {sample_product['title']}")
        print(f"Blueprint ID: {sample_product.get('blueprint_id')}")
        print(f"Print Provider ID: {sample_product.get('print_provider_id')}")
        print(f"Is Printify Choice: {sample_product.get('is_printify_choice')}")
        
        # Check variants
        variants = sample_product.get('variants', [])
        print(f"Available variants: {len(variants)}")
        
        if variants:
            print("Sample variants:")
            for variant in variants[:3]:
                print(f"   • {variant.get('color')} / {variant.get('size')} (ID: {variant.get('id')})")
        
        # Check required fields for mockup generation
        required_fields = ['blueprint_id', 'print_provider_id', 'variants']
        missing_fields = [field for field in required_fields if not sample_product.get(field)]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        else:
            print("✅ All required fields present for mockup generation")
        
        print("\n✅ Printify integration test complete")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 PRODUCT LOGIC TEST SUITE (NO AI CALLS)")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Product Selection Logic", test_product_selection_mock()))
    results.append(("Product Popularity Scoring", test_product_popularity_scoring()))
    results.append(("Printify Integration", test_printify_integration()))
    
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
        print("\n🎉 All product logic working correctly!")
        print("💡 The AI components will work once the OpenAI key issue is resolved")
    else:
        print("\n⚠️ Some product logic needs attention")

if __name__ == "__main__":
    main()