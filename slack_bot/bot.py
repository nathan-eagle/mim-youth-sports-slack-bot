"""
Main SlackBot class that handles incoming events and coordinates responses
"""
import os
import logging
from typing import Dict, Optional
from slack_sdk import WebClient
from dotenv import load_dotenv

from .handlers import MessageHandler, FileHandler
from .message_sender import MessageSender
from conversation_manager import conversation_manager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class SlackBot:
    """Main bot class that coordinates all Slack interactions"""
    
    def __init__(self):
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        self.message_handler = MessageHandler(self)
        self.file_handler = FileHandler(self)
        self.message_sender = MessageSender(self.client)
    
    def handle_message(self, event: Dict) -> Dict:
        """Handle incoming Slack message with improved error handling"""
        try:
            channel = event.get('channel')
            user = event.get('user')
            text = event.get('text', '').strip()
            
            # Skip bot messages and empty messages
            if event.get('bot_id') or not text:
                return {"status": "ignored"}
            
            # Check for duplicate events
            if conversation_manager.is_duplicate_event(event):
                return {"status": "duplicate"}
            
            logger.info(f"Processing message from {user} in {channel}: {text}")
            logger.info(f"Conversation state: {conversation_manager.get_conversation_summary(channel, user)}")
            
            # Handle restart command
            if text.lower().strip() in ['restart', 'reset', 'start over']:
                return self.message_handler.handle_restart(channel, user)
            
            # Get or create conversation
            conversation = conversation_manager.get_or_create_conversation(channel, user)
            current_state = conversation.get('state', 'initial')
            
            logger.info(f"Current state: {current_state}")
            
            # Route to appropriate handler based on state
            return self.message_handler.route_message(text, conversation, event, channel, user)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    def handle_file_share(self, event: Dict) -> Dict:
        """Handle file share events (logo uploads)"""
        try:
            channel = event.get('channel')
            user = event.get('user')
            
            # Skip bot uploads
            if event.get('bot_id'):
                return {"status": "ignored"}
            
            logger.info(f"Processing file share from {user} in {channel}")
            
            # Get or create conversation
            conversation = conversation_manager.get_or_create_conversation(channel, user)
            
            return self.file_handler.handle_file_upload(event, conversation, channel, user)
            
        except Exception as e:
            logger.error(f"Error handling file share: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    def send_error_message(self, channel: str, user: str, error: str):
        """Send error message to user"""
        self.message_sender.send_error_message(channel, user, error)
    
    def send_message(self, channel: str, message: str):
        """Send plain text message"""
        self.message_sender.send_message(channel, message)
    
    def send_image_message(self, channel: str, image_url: str, caption: str = ""):
        """Send image with optional caption"""
        self.message_sender.send_image_message(channel, image_url, caption)


# Create singleton instance
slack_bot = SlackBot()