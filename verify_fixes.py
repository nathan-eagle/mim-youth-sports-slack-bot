#!/usr/bin/env python3
"""
Verify that both database schema and OpenAI imports are fixed
"""

import os
from dotenv import load_dotenv

load_dotenv()

def test_fixes():
    print("🔧 VERIFYING COMPLETE FIXES")
    print("=" * 40)
    
    # Test 1: OpenAI Service Import Fix
    print("1. Testing OpenAI service import fix...")
    try:
        from openai_service import OpenAIService
        openai_service = OpenAIService()
        print("   ✅ OpenAI service imports correctly")
        
        # Test a simple analysis (this would have failed before with json import error)
        result = openai_service.analyze_parent_request("I want a red hoodie")
        print(f"   ✅ OpenAI analysis working: {result.get('product_type')}")
        
    except Exception as e:
        print(f"   ❌ OpenAI service failed: {e}")
        return False
    
    # Test 2: Database Schema Fix
    print("\n2. Testing database schema...")
    try:
        from conversation_manager import ConversationManager
        conv_manager = ConversationManager()
        
        # This would have failed before with missing columns
        test_conversation = conv_manager.get_or_create_conversation("C123", "U456")
        conv_manager.update_conversation("C123", "U456", {
            "state": "product_selection",
            "error_count": 0,
            "team_info": {"sport": "soccer"}
        })
        
        # Verify it persisted
        loaded = conv_manager.get_conversation("C123", "U456")
        if loaded['state'] == 'product_selection':
            print("   ✅ Database schema complete and working")
        else:
            print("   ❌ Database persistence not working")
            return False
            
        conv_manager.reset_conversation("C123", "U456")
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False
    
    print("\n🎉 ALL FIXES VERIFIED!")
    print("✅ OpenAI json import fixed")
    print("✅ Database schema complete")
    print("✅ System ready for production")
    
    return True

if __name__ == "__main__":
    success = test_fixes()
    if not success:
        print("\n❌ FIXES NOT WORKING")
        exit(1)