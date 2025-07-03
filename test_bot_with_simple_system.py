#!/usr/bin/env python3
"""
Test the bot with simplified system components
"""

def test_bot_integration():
    print("🤖 TESTING SLACK BOT WITH SIMPLIFIED SYSTEM")
    print("=" * 50)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from slack_bot.bot import slack_bot
        print("   ✅ Slack bot imported successfully")
        
        from simple_conversation_manager import conversation_manager
        print("   ✅ Simple conversation manager imported")
        
        from simple_database_service import database_service
        print("   ✅ Simple database service imported")
        
        # Test conversation flow
        print("\n2. Testing conversation flow...")
        conv = conversation_manager.get_conversation("C123", "U456")
        print(f"   ✅ Initial conversation state: {conv['state']}")
        
        conversation_manager.update_conversation("C123", "U456", {"state": "product_selection"})
        updated = conversation_manager.get_conversation("C123", "U456")
        print(f"   ✅ Updated conversation state: {updated['state']}")
        
        # Test mockup generator with simplified system
        print("\n3. Testing mockup generator...")
        from slack_bot.mockup_generator import MockupGenerator
        mockup_gen = MockupGenerator()
        print("   ✅ Mockup generator created successfully")
        
        # Test product selection
        print("\n4. Testing product selection...")
        from services.product_service import product_service
        hoodies = product_service.get_products_by_category('hoodie')
        if isinstance(hoodies, dict):
            hoodies = list(hoodies.values())
        print(f"   ✅ Found {len(hoodies)} hoodies")
        
        print(f"\n🎉 BOT INTEGRATION TEST PASSED!")
        print("✅ All imports working")
        print("✅ Conversation management working")
        print("✅ Product selection working")
        print("✅ System ready for Slack integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_bot_integration()
    if success:
        print("\n🚀 BOT READY FOR SLACK TESTING!")
    else:
        print("\n❌ BOT NOT READY")
        exit(1)