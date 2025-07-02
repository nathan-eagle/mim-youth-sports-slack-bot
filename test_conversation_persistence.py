#!/usr/bin/env python3

import os
import time
import json
from conversation_manager import conversation_manager

def test_conversation_persistence():
    """Test if conversations are actually being saved and can be restored"""
    
    print("🧪 Testing Conversation Persistence")
    print("=" * 40)
    
    # Test channel and user (like from Slack)
    test_channel = "C123456789"
    test_user = "U987654321"
    
    print(f"1️⃣ Creating conversation for {test_channel}_{test_user}")
    
    # Reset conversation
    conversation_manager.reset_conversation(test_channel, test_user)
    
    # Update with logo info (like after restart)
    logo_info = {
        "printify_image_id": "test_logo_123",
        "url": "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png"
    }
    
    conversation_manager.update_conversation(test_channel, test_user, {
        "state": "completed",
        "logo_info": logo_info,
        "team_info": {"name": "Test Team"}
    })
    
    print("   ✅ Updated conversation with logo and team info")
    
    # Check current state
    current_conversation = conversation_manager.get_conversation(test_channel, test_user)
    print(f"   📊 Current state: {current_conversation['state']}")
    print(f"   🎨 Logo ID: {current_conversation['logo_info']['printify_image_id']}")
    
    # Check if state file was created/updated
    state_file = "conversation_state.json"
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            saved_data = json.load(f)
        
        conversation_key = f"{test_channel}_{test_user}"
        if conversation_key in saved_data.get('conversations', {}):
            saved_conversation = saved_data['conversations'][conversation_key]
            print(f"   💾 Saved to disk: {saved_conversation['state']}")
            print(f"   💾 Saved logo: {saved_conversation.get('logo_info', {}).get('printify_image_id', 'None')}")
            
            # Check timestamps
            created_time = saved_conversation.get('created_at', 0)
            last_activity = saved_conversation.get('last_activity', 0)
            current_time = time.time()
            
            print(f"   ⏰ Created: {time.strftime('%H:%M:%S', time.localtime(created_time))}")
            print(f"   ⏰ Last activity: {time.strftime('%H:%M:%S', time.localtime(last_activity))}")
            print(f"   ⏰ Age: {(current_time - last_activity):.1f} seconds")
            
        else:
            print(f"   ❌ NOT FOUND in saved state file!")
            print(f"   📋 Available keys: {list(saved_data.get('conversations', {}).keys())}")
    else:
        print(f"   ❌ State file {state_file} does not exist!")
    
    print(f"\n2️⃣ Simulating new conversation manager instance (like app restart)")
    
    # Create new conversation manager instance to simulate app restart
    from conversation_manager import ConversationManager
    new_manager = ConversationManager()
    
    # Check if it can retrieve the conversation
    restored_conversation = new_manager.get_conversation(test_channel, test_user)
    
    if restored_conversation.get('logo_info') and restored_conversation['logo_info'].get('printify_image_id'):
        print("   ✅ Conversation RESTORED successfully after restart!")
        print(f"   📊 Restored state: {restored_conversation['state']}")
        print(f"   🎨 Restored logo: {restored_conversation['logo_info']['printify_image_id']}")
    else:
        print("   ❌ Conversation LOST after restart!")
        print(f"   📊 State: {restored_conversation.get('state', 'None')}")
        print(f"   🎨 Logo: {restored_conversation.get('logo_info', 'None')}")
    
    print(f"\n3️⃣ Testing cleanup behavior")
    
    # Show cleanup threshold
    cleanup_threshold = 24 * 60 * 60  # 24 hours
    current_time = time.time()
    conversation_age = current_time - restored_conversation.get('last_activity', current_time)
    
    print(f"   ⏰ Cleanup threshold: {cleanup_threshold / 3600:.1f} hours")
    print(f"   ⏰ Conversation age: {conversation_age / 60:.1f} minutes")
    print(f"   🧹 Will be cleaned: {'YES' if conversation_age > cleanup_threshold else 'NO'}")

if __name__ == "__main__":
    test_conversation_persistence()