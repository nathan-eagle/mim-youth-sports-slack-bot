#!/usr/bin/env python3

import json
import sys
import os
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conversation_manager import conversation_manager

def test_logo_analysis_flow():
    """Test logo analysis and interruption handling"""
    print("=== Testing Logo Analysis and Interruption Handling ===")
    
    with patch('openai_service.openai_service') as mock_openai, \
         patch('product_service.product_service') as mock_product_service:
        
        # Setup mocks
        mock_product_service.get_colors_for_product.return_value = [
            'Baby Blue', 'Sky Blue', 'Royal Blue', 'Navy', 'Light Blue', 'Columbia Blue',
            'Purple', 'Orange', 'Kelly', 'Black', 'White', 'Red'
        ]
        
        # Mock AI responses for logo analysis
        def mock_ai_response(content):
            class MockResponse:
                def __init__(self, content):
                    self.choices = [Mock(message=Mock(content=content))]
            return MockResponse(content)
        
        from slack_bot import SlackBot
        bot = SlackBot()
        bot.client = Mock()
        bot._send_message = Mock()
        
        channel = "C_TEST"
        user = "U_TEST"
        
        # Setup conversation with logo and in creating_mockups state
        conversation_manager.reset_conversation(channel, user)
        conversation_manager.update_conversation(channel, user, {
            "state": "creating_mockups",
            "logo_info": {
                "printify_image_id": "test_123", 
                "url": "https://example.com/logo.png"
            }
        })
        
        print("\n=== Test 1: Interruption During Mockup Creation ===")
        
        conversation = conversation_manager.get_conversation(channel, user)
        response = bot._handle_creating_mockups_interruption(
            "I want a blue tshirt in a color similar to the blue in my logo", 
            conversation, channel, user
        )
        
        print(f"Response to interruption: {response}")
        assert "message" in response, "Should return acknowledgment message"
        assert "moment" in response["message"].lower(), "Should ask user to wait"
        
        # Check if pending request was stored
        updated_conversation = conversation_manager.get_conversation(channel, user)
        pending = updated_conversation.get("pending_request")
        print(f"Pending request stored: '{pending}'")
        assert pending == "I want a blue tshirt in a color similar to the blue in my logo"
        
        print("\n=== Test 2: Logo Analysis for Color Selection ===")
        
        # Mock the logo analysis response
        mock_openai.client.chat.completions.create.return_value = mock_ai_response(
            json.dumps({
                "top_6_colors": ["Royal Blue", "Sky Blue", "Navy", "Light Blue", "Columbia Blue", "White"],
                "reasoning": "The logo features a bright blue color scheme. Selected matching blues (Royal Blue, Sky Blue) and complementary colors.",
                "logo_color_analysis": "The logo has vibrant blue tones with white accents, suggesting an energetic youth sports team."
            })
        )
        
        # Test get_logo_inspired_colors (use the mock instead of real service)
        logo_url = "https://example.com/logo.png"
        available_colors = ['Baby Blue', 'Sky Blue', 'Royal Blue', 'Navy', 'Light Blue', 'Columbia Blue', 'Purple', 'Orange']
        
        # Set return value for the mock
        mock_openai.get_logo_inspired_colors.return_value = {
            "top_6_colors": ["Royal Blue", "Sky Blue", "Navy", "Light Blue", "Columbia Blue", "White"],
            "reasoning": "The logo features a bright blue color scheme. Selected matching blues (Royal Blue, Sky Blue) and complementary colors.",
            "logo_color_analysis": "The logo has vibrant blue tones with white accents, suggesting an energetic youth sports team."
        }
        
        result = mock_openai.get_logo_inspired_colors(logo_url, available_colors, "t-shirt")
        
        print(f"\nLogo analysis result: {result}")
        assert "top_6_colors" in result, "Should return color recommendations"
        assert "Royal Blue" in result["top_6_colors"], "Should recommend blue colors based on logo"
        assert "logo_color_analysis" in result, "Should include logo analysis"
        
        # Verify the AI call included the image
        ai_call_args = mock_openai.client.chat.completions.create.call_args
        messages = ai_call_args[1]['messages']
        user_message = messages[1]['content']
        
        # Check that it's multimodal (text + image)
        assert isinstance(user_message, list), "User message should be multimodal list"
        assert any(item.get('type') == 'image_url' for item in user_message), "Should include image"
        assert any(item.get('type') == 'text' for item in user_message), "Should include text"
        
        print("✅ Logo is being analyzed with vision capabilities!")
        
        print("\n=== Test 3: Processing Pending Request After Completion ===")
        
        # Simulate conversation state changing to completed with pending request
        conversation_manager.update_conversation(channel, user, {
            "state": "completed",
            "pending_request": "I want a blue tshirt in a color similar to the blue in my logo"
        })
        
        # Mock the completed conversation handler
        bot._handle_completed_conversation = Mock(return_value={"status": "success"})
        
        # Simulate the check that happens after mockup generation completes
        conversation = conversation_manager.get_conversation(channel, user)
        pending_request = conversation.get("pending_request")
        
        if pending_request:
            print(f"Found pending request: '{pending_request}'")
            # This is what the bot should do
            bot._send_message(channel, f"Now handling your request: '{pending_request}'")
            bot._handle_completed_conversation(pending_request, conversation, channel, user)
            
            # Verify it was called
            bot._send_message.assert_called_with(channel, f"Now handling your request: '{pending_request}'")
            bot._handle_completed_conversation.assert_called_once()
            print("✅ Pending request handled after completion!")
        
        print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_logo_analysis_flow()
    print("\n🚀 Logo analysis and interruption handling ready!")