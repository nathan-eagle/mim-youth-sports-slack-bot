"""
Event handlers for MiM Slack Bot
Async handlers for different types of Slack events
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from .redis_state_manager import RedisStateManager

logger = structlog.get_logger(__name__)


class BaseEventHandler:
    """
    Base class for event handlers
    """
    
    def __init__(self, state_manager: RedisStateManager):
        """
        Initialize base event handler
        
        Args:
            state_manager: Redis state manager
        """
        self.state_manager = state_manager
    
    async def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle event (to be implemented by subclasses)
        
        Args:
            event_data: Slack event data
            
        Returns:
            Processing result
        """
        raise NotImplementedError("Subclasses must implement handle method")
    
    def _extract_event_info(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract common event information"""
        event = event_data.get('event', {})
        
        return {
            'event_id': event_data.get('event_id'),
            'event_type': event.get('type'),
            'user_id': event.get('user'),
            'channel_id': event.get('channel'),
            'timestamp': event.get('ts'),
            'text': event.get('text', ''),
            'subtype': event.get('subtype')
        }


class MessageHandler(BaseEventHandler):
    """
    Handler for message events
    """
    
    async def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle message event
        
        Args:
            event_data: Slack event data
            
        Returns:
            Processing result
        """
        try:
            event_info = self._extract_event_info(event_data)
            
            logger.info("Processing message event", 
                       user=event_info['user_id'],
                       channel=event_info['channel_id'])
            
            # Import the main bot logic (avoid circular imports)
            from slack_bot import slack_bot
            
            # Use existing bot logic for message handling
            result = slack_bot.handle_message(event_data.get('event', {}))
            
            # Update conversation state
            if event_info['user_id'] and event_info['channel_id']:
                await self.state_manager.update_conversation(
                    event_info['channel_id'],
                    event_info['user_id'],
                    {
                        'last_message': event_info['text'],
                        'last_message_time': datetime.utcnow().isoformat(),
                        'last_processing_result': result
                    }
                )
            
            return {
                'status': 'completed',
                'result': result,
                'event_info': event_info
            }
            
        except Exception as e:
            logger.error("Message handling failed", error=str(e))
            raise


class FileShareHandler(BaseEventHandler):
    """
    Handler for file share events
    """
    
    async def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle file share event
        
        Args:
            event_data: Slack event data
            
        Returns:
            Processing result
        """
        try:
            event_info = self._extract_event_info(event_data)
            
            logger.info("Processing file share event",
                       user=event_info['user_id'],
                       channel=event_info['channel_id'])
            
            # Import the main bot logic (avoid circular imports)
            from slack_bot import slack_bot
            
            # Use existing bot logic for file handling
            result = slack_bot.handle_file_share(event_data.get('event', {}))
            
            # Update conversation state
            if event_info['user_id'] and event_info['channel_id']:
                await self.state_manager.update_conversation(
                    event_info['channel_id'],
                    event_info['user_id'],
                    {
                        'last_file_upload': datetime.utcnow().isoformat(),
                        'last_processing_result': result
                    }
                )
            
            return {
                'status': 'completed',
                'result': result,
                'event_info': event_info
            }
            
        except Exception as e:
            logger.error("File share handling failed", error=str(e))
            raise


class AppMentionHandler(BaseEventHandler):
    """
    Handler for app mention events
    """
    
    async def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle app mention event
        
        Args:
            event_data: Slack event data
            
        Returns:
            Processing result
        """
        try:
            event_info = self._extract_event_info(event_data)
            
            logger.info("Processing app mention event",
                       user=event_info['user_id'],
                       channel=event_info['channel_id'])
            
            # Handle as a regular message for now
            # Could add special mention-specific logic here
            return await MessageHandler(self.state_manager).handle(event_data)
            
        except Exception as e:
            logger.error("App mention handling failed", error=str(e))
            raise


class ReactionHandler(BaseEventHandler):
    """
    Handler for reaction events (future enhancement)
    """
    
    async def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle reaction event
        
        Args:
            event_data: Slack event data
            
        Returns:
            Processing result
        """
        try:
            event_info = self._extract_event_info(event_data)
            
            logger.info("Processing reaction event",
                       user=event_info['user_id'],
                       channel=event_info['channel_id'])
            
            # For now, just log the reaction
            # Future: Could use reactions for feedback, approvals, etc.
            
            return {
                'status': 'completed',
                'result': 'reaction_logged',
                'event_info': event_info
            }
            
        except Exception as e:
            logger.error("Reaction handling failed", error=str(e))
            raise