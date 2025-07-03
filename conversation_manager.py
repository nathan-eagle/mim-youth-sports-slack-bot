#!/usr/bin/env python3
"""
Simple conversation manager that works with minimal database schema
"""

import os
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class SimpleConversationManager:
    """Minimal conversation manager with fallback to in-memory"""
    
    def __init__(self):
        # Always use in-memory for now since database is problematic
        self.conversations = {}
        self.supabase = None  # Disable database for now
        logger.info("Using in-memory conversation storage")
    
    def get_conversation(self, channel: str, user: str) -> Dict:
        """Get conversation - in-memory only"""
        conversation_key = f"{channel}_{user}"
        
        if conversation_key not in self.conversations:
            self.conversations[conversation_key] = {
                "state": "initial",
                "created_at": time.time(),
                "last_activity": time.time(),
            }
            logger.info(f"Created new conversation: {conversation_key}")
        
        return self.conversations[conversation_key]
    
    def update_conversation(self, channel: str, user: str, updates: Dict):
        """Update conversation - in-memory only"""
        conversation_key = f"{channel}_{user}"
        conversation = self.get_conversation(channel, user)
        
        for key, value in updates.items():
            conversation[key] = value
        
        conversation["last_activity"] = time.time()
        logger.info(f"Updated conversation: {conversation_key}")
    
    def reset_conversation(self, channel: str, user: str):
        """Reset conversation"""
        conversation_key = f"{channel}_{user}"
        self.conversations[conversation_key] = {
            "state": "initial",
            "created_at": time.time(),
            "last_activity": time.time(),
        }
        logger.info(f"Reset conversation: {conversation_key}")
    
    def get_or_create_conversation(self, channel: str, user: str) -> Dict:
        """Get or create conversation"""
        return self.get_conversation(channel, user)
    
    def get_conversation_summary(self, channel: str, user: str) -> str:
        """Get conversation summary"""
        conversation = self.get_conversation(channel, user)
        state = conversation.get('state', 'initial')
        last_activity = conversation.get('last_activity', 0)
        age = (time.time() - last_activity) / 60
        return f"state={state}, age={age:.1f}min"
    
    def is_duplicate_event(self, event: Dict) -> bool:
        """Check if event is duplicate - always return False for in-memory"""
        return False
    
    def cleanup_old_conversations(self):
        """Cleanup old conversations - no-op for in-memory"""
        pass

# Global instance
conversation_manager = SimpleConversationManager()