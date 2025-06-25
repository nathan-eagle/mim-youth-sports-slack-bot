#!/usr/bin/env python3
"""
Test script to verify MiM Youth Sports Swag Bot setup
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test that required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET', 
        'OPENAI_API_KEY',
        'PRINTIFY_API_TOKEN',
        'PRINTIFY_SHOP_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            print(f"❌ {var}: Not set")
        else:
            print(f"✅ {var}: Set")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with these variables.")
        return False
    
    print("✅ All environment variables are set!")
    return True

def test_product_cache():
    """Test product cache loading and 'best' product filtering"""
    print("\n🛍️  Testing Product Cache...")
    
    try:
        from product_service import product_service
        
        # Test cache loading
        if not product_service.products_cache:
            print("❌ Product cache is empty")
            return False
        
        print(f"✅ Loaded {len(product_service.products_cache)} total products")
        
        # Test 'best' products filtering
        best_products = product_service.get_best_products()
        if not best_products:
            print("❌ No 'best' products found")
            return False
        
        print(f"✅ Found {len(best_products)} products tagged as 'best':")
        
        for product_id, product in best_products.items():
            formatted = product_service.format_product_for_slack(product_id, product)
            print(f"   • {formatted['title']} ({formatted['category']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing product cache: {e}")
        return False

def test_openai_service():
    """Test OpenAI service"""
    print("\n🤖 Testing OpenAI Service...")
    
    try:
        from openai_service import openai_service
        
        # Test basic analysis
        test_message = "I need a shirt for my son's baseball team"
        result = openai_service.analyze_parent_request(test_message)
        
        if result and result.get('response_message'):
            print("✅ OpenAI service is working")
            print(f"   Sample analysis: {result}")
            return True
        else:
            print("❌ OpenAI service returned invalid response")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenAI service: {e}")
        return False

def test_printify_connection():
    """Test Printify API connection"""
    print("\n🖨️  Testing Printify Connection...")
    
    try:
        from printify_service import printify_service
        
        if not printify_service.api_token:
            print("❌ Printify API token not configured")
            return False
        
        if not printify_service.shop_id:
            print("❌ Printify shop ID not configured")
            return False
        
        print("✅ Printify service is configured")
        print(f"   Shop ID: {printify_service.shop_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Printify service: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 MiM Youth Sports Swag Bot - Setup Test\n")
    
    tests = [
        test_environment_variables,
        test_product_cache,
        test_openai_service,
        test_printify_connection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("\nNext steps:")
        print("1. Set up your Slack app and get tokens")
        print("2. Run: python app.py")
        print("3. Test with a parent message in Slack!")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 