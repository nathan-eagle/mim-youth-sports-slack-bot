"""
Conversation Manager with persistent state and improved error handling
"""

import json
import logging
import time
import hashlib
from typing import Dict, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class ConversationManager:
    _instance = None
    _initialized = False
    
    def __new__(cls, state_file: str = "conversation_state.json"):
        if cls._instance is None:
            cls._instance = super(ConversationManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, state_file: str = "conversation_state.json"):
        if self._initialized:
            return
        
        self.state_file = Path(state_file)
        self.conversations = {}
        self.processed_events = set()  # For event deduplication
        self.max_processed_events = 1000  # Limit memory usage
        
        # Load existing state
        self._load_state()
        
        # Clean up old conversations (older than 24 hours)
        self._cleanup_old_conversations()
        
        self._initialized = True
        logger.info("ConversationManager singleton initialized")
    
    def _load_state(self):
        """Load conversation state from disk"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.conversations = data.get('conversations', {})
                    self.processed_events = set(data.get('processed_events', []))
                    logger.info(f"Loaded {len(self.conversations)} conversations from disk")
        except Exception as e:
            logger.warning(f"Could not load conversation state: {e}")
            self.conversations = {}
            self.processed_events = set()
    
    def _save_state(self):
        """Save conversation state to disk"""
        try:
            # Limit processed_events size to prevent memory bloat
            if len(self.processed_events) > self.max_processed_events:
                # Keep only the most recent events (approximate)
                events_list = list(self.processed_events)
                self.processed_events = set(events_list[-self.max_processed_events//2:])
            
            data = {
                'conversations': self.conversations,
                'processed_events': list(self.processed_events),
                'last_updated': time.time()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except (OSError, PermissionError) as e:
            # Handle read-only file system (common in serverless environments)
            if "Read-only file system" in str(e) or "Permission denied" in str(e):
                logger.warning(f"Cannot save conversation state - read-only file system. Continuing with in-memory state.")
                # Continue with in-memory state only
                pass
            else:
                logger.error(f"Could not save conversation state: {e}")
        except Exception as e:
            logger.error(f"Could not save conversation state: {e}")
    
    def _cleanup_old_conversations(self):
        """Remove conversations older than 24 hours"""
        current_time = time.time()
        cutoff_time = current_time - (24 * 60 * 60)  # 24 hours ago
        
        old_conversations = []
        for conv_key, conversation in self.conversations.items():
            last_activity = conversation.get('last_activity', 0)
            if last_activity < cutoff_time:
                old_conversations.append(conv_key)
        
        for conv_key in old_conversations:
            del self.conversations[conv_key]
            logger.info(f"Cleaned up old conversation: {conv_key}")
        
        if old_conversations:
            self._save_state()
    
    def generate_event_id(self, event: Dict) -> str:
        """Generate unique event ID for deduplication"""
        # Create a hash from event content to detect duplicates
        event_data = {
            'channel': event.get('channel'),
            'user': event.get('user'),
            'text': event.get('text'),
            'ts': event.get('ts'),
            'event_ts': event.get('event_ts')
        }
        
        event_str = json.dumps(event_data, sort_keys=True)
        return hashlib.md5(event_str.encode()).hexdigest()
    
    def is_duplicate_event(self, event: Dict) -> bool:
        """Check if event has already been processed"""
        event_id = self.generate_event_id(event)
        
        if event_id in self.processed_events:
            logger.info(f"Duplicate event detected: {event_id}")
            return True
        
        # Mark as processed
        self.processed_events.add(event_id)
        return False
    
    def get_conversation(self, channel: str, user: str) -> Dict:
        """Get or create conversation state"""
        conversation_key = f"{channel}_{user}"
        
        if conversation_key not in self.conversations:
            self.conversations[conversation_key] = {
                "state": "initial",
                "product_selected": None,
                "logo_info": None,
                "team_info": {},
                "selected_variants": {},  # Store color selections for each product
                "created_at": time.time(),
                "last_activity": time.time(),
                "error_count": 0,
                "last_error": None
            }
            logger.info(f"Created new conversation: {conversation_key}")
        
        # Update last activity
        self.conversations[conversation_key]["last_activity"] = time.time()
        
        return self.conversations[conversation_key]
    
    def update_conversation(self, channel: str, user: str, updates: Dict):
        """Update conversation state"""
        conversation_key = f"{channel}_{user}"
        conversation = self.get_conversation(channel, user)
        
        # Apply updates
        for key, value in updates.items():
            conversation[key] = value
        
        conversation["last_activity"] = time.time()
        
        # Save to disk
        self._save_state()
        
        logger.info(f"Updated conversation {conversation_key}: {list(updates.keys())}")
    
    def record_error(self, channel: str, user: str, error: str):
        """Record error in conversation state"""
        conversation = self.get_conversation(channel, user)
        conversation["error_count"] = conversation.get("error_count", 0) + 1
        conversation["last_error"] = {
            "message": error,
            "timestamp": time.time()
        }
        
        logger.warning(f"Error recorded for {channel}_{user}: {error}")
        self._save_state()
    
    def reset_conversation(self, channel: str, user: str):
        """Reset conversation to initial state"""
        conversation_key = f"{channel}_{user}"
        if conversation_key in self.conversations:
            self.conversations[conversation_key] = {
                "state": "initial",
                "product_selected": None,
                "logo_info": None,
                "team_info": {},
                "selected_variants": {},  # Store color selections for each product
                "created_at": time.time(),
                "last_activity": time.time(),
                "error_count": 0,
                "last_error": None
            }
            self._save_state()
            logger.info(f"Reset conversation: {conversation_key}")
    
    def get_conversation_summary(self, channel: str, user: str) -> str:
        """Get human-readable conversation summary"""
        conversation = self.get_conversation(channel, user)
        
        summary_parts = []
        summary_parts.append(f"State: {conversation['state']}")
        
        if conversation.get('product_selected'):
            product_title = conversation['product_selected'].get('formatted', {}).get('title', 'Unknown')
            summary_parts.append(f"Product: {product_title}")
        
        if conversation.get('team_info'):
            team_info = conversation['team_info']
            if team_info.get('name'):
                summary_parts.append(f"Team: {team_info['name']}")
            if team_info.get('sport'):
                summary_parts.append(f"Sport: {team_info['sport']}")
        
        if conversation.get('error_count', 0) > 0:
            summary_parts.append(f"Errors: {conversation['error_count']}")
        
        return " | ".join(summary_parts)
    
    def should_show_help(self, channel: str, user: str) -> bool:
        """Determine if user needs help based on error count"""
        conversation = self.get_conversation(channel, user)
        return conversation.get("error_count", 0) >= 2
    
    def get_recovery_message(self, channel: str, user: str) -> Optional[str]:
        """Get recovery message for users with errors"""
        conversation = self.get_conversation(channel, user)
        
        if conversation.get("error_count", 0) >= 2:
            return ("I notice you've run into a few issues. Let me help! "
                   "You can type 'restart' to begin fresh, or let me know what you're trying to do. "
                   "I'm here to help you create custom team merchandise! 🏆")
        
        return None

    def _get_timestamp(self) -> float:
        """Get current timestamp for tracking"""
        return time.time()

# Global instance
conversation_manager = ConversationManager() 