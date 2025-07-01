#!/usr/bin/env python3
"""
Test the full bot color flow through _create_single_mockup_with_variant
"""

import os
from dotenv import load_dotenv
from slack_bot import SlackBot
from product_service import ProductService

# Load environment variables
load_dotenv()

def test_bot_color_flow():
    """Test the actual bot flow for color requests"""
    print("🧪 Testing full bot color flow")
    print("=" * 50)
    
    slack_bot = SlackBot()
    product_service = ProductService()
    
    # Simulate conversation state
    conversation = {
        "state": "completed",
        "team_info": {"name": "Test Team"},
        "logo_info": {"printify_image_id": "685d8aee5638948d7abca30a"}
    }
    
    # Parse user request for blue jersey
    user_request = "i want a blue jersey tshirt"
    selected_variants = product_service.parse_color_preferences(user_request)
    
    if not selected_variants:
        print("❌ No variants parsed")
        return False
    
    variant_info = selected_variants[0]
    print(f"✅ Parsed: {variant_info['product_name']} in {variant_info['color']}")
    
    # Create product info structure
    product_info = {
        "id": variant_info['product_id'],
        "formatted": {"title": variant_info['product_name']}
    }
    
    selected_variant = variant_info['variant']
    
    print(f"🔄 Testing _create_single_mockup_with_variant...")
    print(f"   Product: {product_info}")
    print(f"   Variant: {selected_variant['id']} ({variant_info['color']})")
    
    # Test the actual method the bot uses
    result = slack_bot._create_single_mockup_with_variant(
        conversation=conversation,
        logo_info=conversation['logo_info'],
        product_info=product_info,
        selected_variant=selected_variant,
        channel="test_channel",
        user="test_user"
    )
    
    if result.get("image_url") and result.get("purchase_url"):
        print(f"✅ SUCCESS!")
        print(f"   Image URL: {result['image_url']}")
        print(f"   Purchase URL: {result['purchase_url']}")
        print(f"   Product Title: {result.get('product_title', 'N/A')}")
        return True
    else:
        print(f"❌ FAILED: {result}")
        return False

if __name__ == "__main__":
    success = test_bot_color_flow()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Bot color flow test")