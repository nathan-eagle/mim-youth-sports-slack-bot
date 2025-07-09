import os
import json
import logging
import re
from typing import Dict, Any, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from mcp_client import mcp_client
from conversation_manager import conversation_manager

logger = logging.getLogger(__name__)

class SlackBotMCP:
    def __init__(self):
        self.client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        self.conversation_manager = conversation_manager
        self.default_logo_url = "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png/v1/fill/w_190,h_190,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/MiM%20Color%20Logo.png"

    def handle_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Slack messages"""
        try:
            channel = event.get("channel", "")
            user = event.get("user", "")
            text = event.get("text", "")
            
            if not channel or not user:
                return {"status": "error", "error": "Missing channel or user"}
            
            # Check for duplicate events to prevent spam
            if conversation_manager.is_duplicate_event(event):
                return {"status": "duplicate", "message": "Event already processed"}
            
            # Handle file uploads
            if event.get("files"):
                return self._handle_file_upload(channel, user, event["files"])
            
            # Process message with MCP
            return self._process_message_with_mcp(channel, user, text, event)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"status": "error", "error": str(e)}
    
    def _handle_file_upload(self, channel: str, user: str, files: list) -> Dict[str, Any]:
        """Handle file uploads (logos)"""
        try:
            for file_info in files:
                if file_info.get("mimetype", "").startswith("image/"):
                    file_url = file_info.get("url_private", "")
                    
                    if file_url:
                        # Store logo URL in conversation
                        conversation_manager.update_conversation(channel, user, {
                            'logo_url': file_url
                        })
                        
                        # Analyze logo with MCP
                        analysis = mcp_client.analyze_logo(file_url)
                        
                        if analysis.get("error"):
                            self._send_message(channel, f"Error analyzing logo: {analysis['error']}")
                        else:
                            colors = analysis.get("colors", [])
                            suggestions = analysis.get("suggestions", "")
                            
                            msg = f"🎨 **Custom Logo Uploaded!**\n\n"
                            if colors:
                                msg += f"**Colors detected:** {', '.join(colors)}\n"
                            if suggestions:
                                msg += f"**Suggestions:** {suggestions}\n"
                            msg += f"\n✅ I'll now use your custom logo for mockups!\nWhat's your team name and sport?"
                            
                            self._send_message(channel, msg)
                        
                        return {"status": "success", "message": "Logo processed"}
            
            return {"status": "success", "message": "No image files found"}
            
        except Exception as e:
            logger.error(f"Error handling file: {e}")
            self._send_message(channel, f"Error processing your logo: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _process_message_with_mcp(self, channel: str, user: str, text: str, event: Dict) -> Dict:
        """Process message using MCP server tools"""
        
        conversation = conversation_manager.get_conversation(channel, user)
        logo_url = conversation.get("logo_url") or self.default_logo_url
        
        # Handle different requests
        if any(word in text.lower() for word in ["suggest", "recommend", "products"]):
            suggestions = mcp_client.suggest_products("Custom", "general")
            msg = f"🏀 **Product Options**\n\n"
            
            # Check if we got recommendations in the expected format
            if suggestions.get("error"):
                msg += f"Sorry, I couldn't get suggestions: {suggestions['error']}"
            else:
                # Try different response formats
                items = (suggestions.get("suggestions", []) or 
                        suggestions.get("primary_recommendations", []) or
                        suggestions.get("recommendations", []))
                
                if items:
                    for item in items:
                        name = item.get("name", item.get("title", "Unknown Product"))
                        price = item.get("price", item.get("estimated_price", "N/A"))
                        msg += f"• **{name}** - ${price}\n"
                else:
                    msg += "• **Jersey Tee** - $25.99\n• **Hoodie** - $45.99\n• **Tank Top** - $22.99\n"
            
            msg += "\nWhich product would you like to create?"
            self._send_message(channel, msg)
            return {"message": msg}
        
        elif any(word in text.lower() for word in ["mockup", "create", "jersey", "hoodie", "shirt", "tshirt", "t-shirt"]) and not any(word in text.lower() for word in ["restart", "reset", "start"]):
            product_id = "92" if "hoodie" in text.lower() else "12"
            
            # Extract color if specified
            color = self._extract_color(text)
            
            # Use default logo if no custom logo uploaded
            using_default_logo = logo_url == self.default_logo_url
            mockup_result = mcp_client.create_team_mockup(
                logo_url=logo_url,
                product_id=product_id,
                team_name="Custom",  # Simple default
                sport="",
                color=color
            )
            
            # Handle None response from MCP client
            if mockup_result is None:
                error_msg = "Sorry, couldn't create mockup: No response from server"
                self._send_message(channel, error_msg)
                conversation_manager.record_error(channel, user, error_msg)
                return {"status": "error", "message": error_msg}
            
            if mockup_result.get("error"):
                error_msg = f"Sorry, couldn't create mockup: {mockup_result['error']}"
                
                # Check if we recently had this error to prevent spam
                conversation = conversation_manager.get_conversation(channel, user)
                last_error = conversation.get('last_error', {})
                
                # Only send error message if it's different from the last one
                if last_error.get('message', '') != error_msg:
                    self._send_message(channel, error_msg)
                
                # Record error to prevent immediate retries
                conversation_manager.record_error(channel, user, error_msg)
                return {"status": "error", "message": error_msg}
            
            # Send product result with image and purchase link
            self._send_product_result(
                channel,
                mockup_result.get("mockup_url", ""),
                mockup_result.get("drop_link", ""),
                mockup_result.get("product_title", "Custom Product")
            )
            
            return {
                "image_url": mockup_result.get("mockup_url", ""),
                "purchase_url": mockup_result.get("drop_link", ""),
                "product_title": mockup_result.get("product_title", "Custom Product")
            }
        
        elif any(word in text.lower() for word in ["analytics", "stats", "report"]):
            analytics = mcp_client.get_analytics("")
            msg = f"📊 **Analytics**\n\n"
            if analytics.get("error"):
                msg += f"Error getting analytics: {analytics['error']}"
            else:
                msg += f"Coming soon! Analytics will show order history and popular products."
            
            self._send_message(channel, msg)
            return {"message": msg}
        
        else:
            # Simple guide - just about products
            custom_logo_status = "your custom logo" if logo_url != self.default_logo_url else "the MiM logo"
            msg = f"Hi! 🎨 I'll put {custom_logo_status} on any product you want.\n\nTry saying:\n• 'create shirt' or 'show me a tshirt'\n• 'create hoodie'\n• 'suggest products'\n\n💡 Upload your own logo anytime to replace the default!"
            
            self._send_message(channel, msg)
            return {"message": msg}
    
    def _extract_color(self, text: str) -> str:
        """Extract color from message"""
        colors = ["red", "blue", "green", "black", "white", "yellow", "orange", "purple", "pink", "gray", "grey", "navy", "maroon"]
        for color in colors:
            if color in text.lower():
                return color
        return ""
    
    def _send_message(self, channel: str, message: str):
        """Send message to Slack"""
        try:
            self.client.chat_postMessage(channel=channel, text=message)
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
    
    def _send_product_result(self, channel: str, image_url: str, purchase_url: str, product_title: str):
        """Send product result with purchase link"""
        try:
            blocks = [
                {
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": product_title
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"🎽 **{product_title}**\n\nReady to purchase!"}
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "🛒 Purchase Now"},
                            "url": purchase_url,
                            "style": "primary"
                        }
                    ]
                }
            ]
            
            self.client.chat_postMessage(channel=channel, blocks=blocks)
        except SlackApiError as e:
            logger.error(f"Error sending product result: {e}")
            # Fall back to simple message
            self._send_message(channel, f"🎽 {product_title}\n\nPurchase: {purchase_url}")

# Create bot instance
slack_bot_mcp = SlackBotMCP() 