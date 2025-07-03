#!/usr/bin/env python3
"""
Test the simplified system without database dependencies
"""

def test_simple_system():
    print("🚀 TESTING SIMPLIFIED SYSTEM (NO DATABASE)")
    print("=" * 50)
    
    # Test 1: Simple Conversation Manager
    print("1. Testing simple conversation manager...")
    try:
        from simple_conversation_manager import conversation_manager
        
        conv = conversation_manager.get_conversation("C123", "U456")
        print(f"   ✅ Created conversation: {conv['state']}")
        
        conversation_manager.update_conversation("C123", "U456", {"state": "product_selection"})
        updated = conversation_manager.get_conversation("C123", "U456")
        
        if updated['state'] == 'product_selection':
            print("   ✅ Conversation updates working")
        else:
            print("   ❌ Conversation update failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Conversation manager failed: {e}")
        return False
    
    # Test 2: Simple Database Service
    print("\n2. Testing simple database service...")
    try:
        from simple_database_service import database_service
        
        design_data = {
            "product_name": "Test Hoodie",
            "color": "Red",
            "mockup_url": "https://example.com/mockup.jpg"
        }
        
        design_id = database_service.save_product_design(design_data)
        print(f"   ✅ Saved design: {design_id}")
        
        retrieved = database_service.get_product_design(design_id)
        if retrieved and retrieved['color'] == 'Red':
            print("   ✅ Design retrieval working")
        else:
            print("   ❌ Design retrieval failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Database service failed: {e}")
        return False
    
    # Test 3: OpenAI Service (should still work)
    print("\n3. Testing OpenAI service...")
    try:
        from openai_service import OpenAIService
        openai_service = OpenAIService()
        
        result = openai_service.analyze_parent_request("I want a red hoodie")
        print(f"   ✅ OpenAI analysis: {result.get('product_type')}")
        
    except Exception as e:
        print(f"   ❌ OpenAI service failed: {e}")
        return False
    
    # Test 4: Product Service (should work)
    print("\n4. Testing product service...")
    try:
        from services.product_service import product_service
        
        hoodies = product_service.get_products_by_category('hoodie')
        if isinstance(hoodies, dict):
            hoodies = list(hoodies.values())
        
        if hoodies and len(hoodies) > 0:
            print(f"   ✅ Found {len(hoodies)} hoodies")
        else:
            print("   ❌ No hoodies found")
            return False
            
    except Exception as e:
        print(f"   ❌ Product service failed: {e}")
        return False
    
    print(f"\n🎉 SIMPLIFIED SYSTEM WORKING!")
    print("✅ In-memory conversation management")
    print("✅ In-memory design storage")
    print("✅ OpenAI integration")
    print("✅ Product catalog")
    print("\n💡 System will work without database dependencies")
    
    return True

if __name__ == "__main__":
    success = test_simple_system()
    if success:
        print("\n🚀 READY TO TEST WITH SLACK BOT!")
    else:
        print("\n❌ SYSTEM NOT READY")
        exit(1)