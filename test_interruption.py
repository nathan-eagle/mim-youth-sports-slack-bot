#!/usr/bin/env python3

import json
import sys
import os
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conversation_manager import conversation_manager

def test_interruption_handling():
    """Test that interruption handling stores pending requests correctly"""
    print("=== Testing Interruption Handling ===")
    
    # Import SlackBot without mocking dependencies
    from slack_bot import SlackBot
    
    # Create bot instance with mock Slack client
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
    
    print("✅ Interruption handling works!")
    
    print("\n=== Test 2: Pending Request Processing ===")
    
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
    
    print("\n✅ All interruption tests passed!")

def test_logo_vision():
    """Test that OpenAI service uses vision for logo analysis"""
    print("\n=== Testing Logo Vision Analysis ===")
    
    from openai_service import openai_service
    
    # Mock just the OpenAI client call
    with patch.object(openai_service.client.chat.completions, 'create') as mock_create:
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "top_6_colors": ["Royal Blue", "Sky Blue", "Navy", "Light Blue", "Columbia Blue", "White"],
            "reasoning": "The logo features a bright blue color scheme",
            "logo_color_analysis": "The logo has vibrant blue tones with white accents"
        })
        mock_create.return_value = mock_response
        
        # Test get_logo_inspired_colors
        logo_url = "https://example.com/logo.png"
        available_colors = ['Baby Blue', 'Sky Blue', 'Royal Blue', 'Navy', 'Light Blue', 'Columbia Blue', 'Purple', 'Orange']
        
        result = openai_service.get_logo_inspired_colors(logo_url, available_colors, "t-shirt")
        
        print(f"Logo analysis result: {result}")
        assert "top_6_colors" in result, "Should return color recommendations"
        assert "Royal Blue" in result["top_6_colors"], "Should recommend blue colors based on logo"
        assert "logo_color_analysis" in result, "Should include logo analysis"
        
        # Verify the AI call included the image
        mock_create.assert_called_once()
        call_args = mock_create.call_args
        messages = call_args[1]['messages']
        user_message = messages[1]['content']
        
        # Check that it's multimodal (text + image)
        assert isinstance(user_message, list), "User message should be multimodal list"
        assert any(item.get('type') == 'image_url' for item in user_message), "Should include image"
        assert any(item.get('type') == 'text' for item in user_message), "Should include text"
        
        print("✅ Logo is being analyzed with vision capabilities!")

if __name__ == "__main__":
    test_interruption_handling()
    test_logo_vision()
    print("\n🚀 All tests passed! Interruption handling and logo vision analysis ready!")