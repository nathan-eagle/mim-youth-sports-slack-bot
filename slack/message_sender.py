"""
Slack message sending utilities
"""
import logging
from typing import List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class MessageSender:
    """Handles sending messages to Slack"""
    
    def __init__(self, client: WebClient):
        self.client = client
    
    def send_error_message(self, channel: str, user: str, error: str):
        """Send error message to user"""
        try:
            message = f"<@{user}> I encountered an error: {error}\n\nPlease try again or contact support if the issue persists."
            self.send_message(channel, message)
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    def send_message(self, channel: str, message: str):
        """Send plain text message"""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=message
            )
            logger.info(f"Message sent successfully to {channel}")
        except SlackApiError as e:
            logger.error(f"Error sending message: {e.response['error']}")
            raise
    
    def send_image_message(self, channel: str, image_url: str, caption: str = ""):
        """Send image with optional caption"""
        try:
            blocks = []
            
            # Add caption if provided
            if caption:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": caption
                    }
                })
            
            # Add image
            blocks.append({
                "type": "image",
                "image_url": image_url,
                "alt_text": caption or "Product mockup"
            })
            
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=caption or "Here's your product mockup!"
            )
            
            logger.info(f"Image message sent successfully to {channel}")
            
        except SlackApiError as e:
            logger.error(f"Error sending image message: {e.response['error']}")
            raise
    
    def send_product_result(self, channel: str, image_url: str, purchase_url: str, 
                          product_name: str, publish_method: str = None):
        """Send product result with image and purchase link"""
        try:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{product_name}*"
                    }
                },
                {
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": product_name
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{purchase_url}|View and Purchase>"
                    }
                }
            ]
            
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"{product_name} - View at: {purchase_url}"
            )
            
            logger.info(f"Product result sent successfully to {channel}")
            
        except SlackApiError as e:
            logger.error(f"Error sending product result: {e.response['error']}")
            raise
    
    def send_product_result_with_alternatives(self, channel: str, image_url: str, 
                                            purchase_url: str, product_name: str, 
                                            available_colors: List[str], 
                                            publish_method: str = None, 
                                            logo_url: str = None):
        """Send product result with alternative color suggestions"""
        try:
            # Build color alternatives text
            if available_colors:
                colors_text = "*Also available in:* " + ", ".join(available_colors[:8])
            else:
                colors_text = ""
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{product_name}*"
                    }
                },
                {
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": product_name
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{purchase_url}|🛒 View and Customize>"
                    }
                }
            ]
            
            # Add color alternatives if available
            if colors_text:
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": colors_text
                    }]
                })
            
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"{product_name} - View at: {purchase_url}"
            )
            
            logger.info(f"Product result with alternatives sent to {channel}")
            
        except SlackApiError as e:
            logger.error(f"Error sending product result: {e.response['error']}")
            raise