#!/usr/bin/env python3
"""
Vercel-compatible conversation manager using Supabase for persistence
"""

import os
import time
import logging
from typing import Dict, Optional
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class ConversationManager:
    """Serverless conversation manager using Supabase"""
    
    def __init__(self):
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not found - using in-memory fallback")
            self.supabase = None
            self.conversations = {}
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.conversations = {}  # In-memory cache for this request
    
    def get_conversation(self, channel: str, user: str) -> Dict:
        """Get conversation from Supabase or create new one"""
        conversation_key = f"{channel}_{user}"
        
        # Check in-memory cache first (for this request)
        if conversation_key in self.conversations:
            return self.conversations[conversation_key]
        
        # Try to load from Supabase
        if self.supabase:
            try:
                result = self.supabase.table('conversations').select('*').eq('conversation_key', conversation_key).execute()
                
                if result.data:
                    # Found existing conversation
                    conversation_data = result.data[0]
                    conversation = {
                        "state": conversation_data.get('state', 'initial'),
                        "product_selected": conversation_data.get('product_selected'),
                        "logo_info": conversation_data.get('logo_info'),
                        "team_info": conversation_data.get('team_info', {}),
                        "selected_variants": conversation_data.get('selected_variants', {}),
                        "created_at": conversation_data.get('created_at', time.time()),
                        "last_activity": conversation_data.get('last_activity', time.time()),
                        "error_count": conversation_data.get('error_count', 0),
                        "last_error": conversation_data.get('last_error'),
                        "pending_request": conversation_data.get('pending_request'),
                        "recent_creation": conversation_data.get('recent_creation')
                    }
                    
                    # Cache in memory for this request
                    self.conversations[conversation_key] = conversation
                    
                    age_minutes = (time.time() - conversation.get('last_activity', 0)) / 60
                    logger.info(f"Restored conversation from Supabase: {conversation_key}, age: {age_minutes:.1f} minutes")
                    
                    return conversation
                    
            except Exception as e:
                logger.error(f"Error loading conversation from Supabase: {e}")
        
        # Create new conversation if not found or Supabase unavailable
        new_conversation = {
            "state": "initial",
            "product_selected": None,
            "logo_info": None,
            "team_info": {},
            "selected_variants": {},
            "created_at": time.time(),
            "last_activity": time.time(),
            "error_count": 0,
            "last_error": None,
            "pending_request": None,
            "recent_creation": None
        }
        
        # Cache in memory
        self.conversations[conversation_key] = new_conversation
        
        logger.info(f"Created new conversation: {conversation_key}")
        return new_conversation
    
    def update_conversation(self, channel: str, user: str, updates: Dict):
        """Update conversation in both cache and Supabase"""
        conversation_key = f"{channel}_{user}"
        conversation = self.get_conversation(channel, user)
        
        # Apply updates to in-memory copy
        for key, value in updates.items():
            conversation[key] = value
        
        conversation["last_activity"] = time.time()
        
        # Save to Supabase
        if self.supabase:
            try:
                # Prepare data for Supabase
                supabase_data = {
                    "conversation_key": conversation_key,
                    "channel": channel,
                    "user": user,
                    "state": conversation.get("state"),
                    "product_selected": conversation.get("product_selected"),
                    "logo_info": conversation.get("logo_info"),
                    "team_info": conversation.get("team_info"),
                    "selected_variants": conversation.get("selected_variants"),
                    "created_at": conversation.get("created_at"),
                    "last_activity": conversation.get("last_activity"),
                    "error_count": conversation.get("error_count"),
                    "last_error": conversation.get("last_error"),
                    "pending_request": conversation.get("pending_request"),
                    "recent_creation": conversation.get("recent_creation")
                }
                
                # Upsert (insert or update)
                self.supabase.table('conversations').upsert(supabase_data).execute()
                logger.info(f"Saved conversation to Supabase: {conversation_key}")
                
            except Exception as e:
                logger.error(f"Error saving conversation to Supabase: {e}")
    
    def reset_conversation(self, channel: str, user: str):
        """Reset conversation state"""
        conversation_key = f"{channel}_{user}"
        
        new_conversation = {
            "state": "initial",
            "product_selected": None,
            "logo_info": None,
            "team_info": {},
            "selected_variants": {},
            "created_at": time.time(),
            "last_activity": time.time(),
            "error_count": 0,
            "last_error": None,
            "pending_request": None,
            "recent_creation": None
        }
        
        # Update in-memory cache
        self.conversations[conversation_key] = new_conversation
        
        # Save to Supabase
        self.update_conversation(channel, user, {})
        
        logger.info(f"Reset conversation: {conversation_key}")
    
    def get_or_create_conversation(self, channel: str, user: str) -> Dict:
        """Get or create conversation - alias for get_conversation"""
        return self.get_conversation(channel, user)
    
    def is_duplicate_event(self, event: Dict) -> bool:
        """Check if event is duplicate (simplified for stateless)"""
        # In a stateless environment, we can't easily track duplicates across requests
        # This would need to be handled at a higher level or with a separate cache
        return False
    
    def get_conversation_summary(self, channel: str, user: str) -> str:
        """Get conversation summary for logging"""
        conversation = self.get_conversation(channel, user)
        state = conversation.get('state', 'initial')
        last_activity = conversation.get('last_activity', 0)
        age = (time.time() - last_activity) / 60  # minutes
        
        return f"state={state}, age={age:.1f}min"
    
    def cleanup_old_conversations(self):
        """Cleanup old conversations from Supabase"""
        if self.supabase:
            try:
                # Delete conversations older than 24 hours
                cutoff_time = time.time() - (24 * 60 * 60)
                
                self.supabase.table('conversations').delete().lt('last_activity', cutoff_time).execute()
                logger.info("Cleaned up old conversations from Supabase")
                
            except Exception as e:
                logger.error(f"Error cleaning up conversations: {e}")


# Global instance for this request
conversation_manager = ConversationManager()