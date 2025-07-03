#!/usr/bin/env python3
"""
Test just the core functionality
"""

def test_core():
    print("🔧 TESTING CORE FUNCTIONALITY")
    print("=" * 40)
    
    try:
        # Test 1: Conversation management
        from conversation_manager import conversation_manager
        conv = conversation_manager.get_conversation("C123", "U456")
        conversation_manager.update_conversation("C123", "U456", {"state": "product_selection"})
        print("✅ Conversation management working")
        
        # Test 2: Database service
        from database_service import database_service
        design_id = database_service.save_product_design({"color": "red"})
        print("✅ Database service working")
        
        # Test 3: OpenAI service
        from openai_service import OpenAIService
        openai_service = OpenAIService()
        result = openai_service.analyze_parent_request("red hoodie")
        print(f"✅ OpenAI working: {result.get('product_type')}")
        
        # Test 4: Product service
        from services.product_service import product_service
        products = product_service.get_products_by_category('hoodie')
        print(f"✅ Product service working: {len(list(products.values()) if isinstance(products, dict) else products)} hoodies")
        
        print("\n🎉 CORE FUNCTIONALITY WORKING!")
        return True
        
    except Exception as e:
        print(f"❌ Core test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_core()