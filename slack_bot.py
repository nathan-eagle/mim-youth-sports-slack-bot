import os
import logging
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, Optional
from dotenv import load_dotenv

from product_service import product_service
from openai_service import openai_service
from logo_processor import logo_processor
from printify_service import printify_service

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SlackBot:
    def __init__(self):
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        
        # Conversation state management (in production, use Redis or database)
        self.conversations = {}
    
    def handle_message(self, event: Dict) -> Dict:
        """Handle incoming Slack message"""
        try:
            channel = event.get('channel')
            user = event.get('user')
            text = event.get('text', '').strip()
            
            # Skip bot messages and empty messages
            if event.get('bot_id') or not text:
                return {"status": "ignored"}
            
            # Get or create conversation state
            conversation_key = f"{channel}_{user}"
            conversation = self.conversations.get(conversation_key, {
                "state": "initial",
                "product_selected": None,
                "logo_info": None,
                "team_info": {}
            })
            
            logger.info(f"Processing message from {user} in {channel}: {text}")
            
            # Process message based on conversation state
            if conversation["state"] == "initial":
                response = self._handle_initial_message(text, conversation)
            elif conversation["state"] == "awaiting_product_selection":
                response = self._handle_product_selection(text, conversation)
            elif conversation["state"] == "awaiting_logo":
                response = self._handle_logo_request(text, conversation, event)
            else:
                response = self._handle_initial_message(text, conversation)
            
            # Update conversation state
            self.conversations[conversation_key] = conversation
            
            # Send response to Slack
            if response.get("message"):
                self._send_message(channel, response["message"])
            
            if response.get("image_url"):
                self._send_image_message(channel, response["image_url"], response.get("image_caption", ""))
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"status": "error", "error": str(e)}
    
    def handle_file_share(self, event: Dict) -> Dict:
        """Handle file upload to Slack"""
        try:
            channel = event.get('channel')
            user = event.get('user')
            file_info = event.get('file', {})
            
            # Get conversation state
            conversation_key = f"{channel}_{user}"
            conversation = self.conversations.get(conversation_key, {})
            
            if conversation.get("state") != "awaiting_logo":
                self._send_message(channel, "Please start by telling me what product you'd like to customize!")
                return {"status": "ignored"}
            
            # Process the uploaded file
            logo_result = logo_processor.process_slack_file(file_info, self.client)
            
            if not logo_result["success"]:
                self._send_message(channel, f"Sorry, there was an issue with your logo: {logo_result['error']}")
                return {"status": "error"}
            
            # Process the logo and create product
            response = self._create_custom_product(conversation, logo_result)
            
            # Send response
            if response.get("message"):
                self._send_message(channel, response["message"])
            
            if response.get("image_url") and response.get("purchase_url"):
                self._send_product_result(channel, response)
            
            # Clean up conversation state
            conversation["state"] = "completed"
            self.conversations[conversation_key] = conversation
            
            # Clean up temporary logo file
            logo_processor.cleanup_logo(logo_result["file_path"])
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error handling file share: {e}")
            return {"status": "error", "error": str(e)}
    
    def _handle_initial_message(self, text: str, conversation: Dict) -> Dict:
        """Handle initial parent message"""
        # Use OpenAI to analyze the request
        analysis = openai_service.analyze_parent_request(text)
        
        # Store team information
        if analysis.get("sport_mentioned"):
            conversation["team_info"]["sport"] = analysis["sport_mentioned"]
        if analysis.get("team_mentioned"):
            conversation["team_info"]["name"] = analysis["team_mentioned"]
        
        # Check if product type was specified
        if analysis.get("product_specified") and analysis.get("product_type"):
            # Find matching product
            product_match = product_service.find_product_by_intent(text)
            if product_match:
                conversation["product_selected"] = product_match
                conversation["state"] = "awaiting_logo"
                
                # Generate logo request message
                team_context = ""
                if conversation["team_info"]:
                    team_parts = []
                    if conversation["team_info"].get("name"):
                        team_parts.append(conversation["team_info"]["name"])
                    if conversation["team_info"].get("sport"):
                        team_parts.append(conversation["team_info"]["sport"])
                    team_context = " ".join(team_parts)
                
                logo_message = openai_service.generate_logo_request_message(
                    product_match["formatted"]["title"], 
                    team_context
                )
                
                return {"message": logo_message}
        
        # Product not specified or not found - ask for clarification
        conversation["state"] = "awaiting_product_selection"
        suggestion_message = product_service.get_product_suggestions_text()
        
        return {"message": f"{analysis.get('response_message', 'Hi there!')}\n\n{suggestion_message}"}
    
    def _handle_product_selection(self, text: str, conversation: Dict) -> Dict:
        """Handle product selection from parent"""
        # Try to find product based on selection
        product_match = product_service.find_product_by_intent(text)
        
        if product_match:
            conversation["product_selected"] = product_match
            conversation["state"] = "awaiting_logo"
            
            # Generate logo request message
            team_context = ""
            if conversation["team_info"]:
                team_parts = []
                if conversation["team_info"].get("name"):
                    team_parts.append(conversation["team_info"]["name"])
                if conversation["team_info"].get("sport"):
                    team_parts.append(conversation["team_info"]["sport"])
                team_context = " ".join(team_parts)
            
            logo_message = openai_service.generate_logo_request_message(
                product_match["formatted"]["title"], 
                team_context
            )
            
            return {"message": logo_message}
        else:
            # Still unclear, show options again
            suggestion_message = product_service.get_product_suggestions_text()
            return {"message": f"I'm not sure which product you'd like. {suggestion_message}"}
    
    def _handle_logo_request(self, text: str, conversation: Dict, event: Dict) -> Dict:
        """Handle logo URL or other text when awaiting logo"""
        # Check if text contains a URL (handle Slack's <url> format)
        if "http" in text.lower():
            # Extract URL - handle both plain URLs and Slack's <url> format
            import re
            # Match URLs with or without angle brackets
            url_pattern = r'<?(https?://[^\s>]+)>?'
            urls = re.findall(url_pattern, text)
            
            if urls:
                url = urls[0]  # Take the first URL found
                
                # Process logo from URL
                logo_result = logo_processor.download_logo_from_url(url)
                
                if not logo_result["success"]:
                    return {"message": f"Sorry, there was an issue with your logo URL: {logo_result['error']}. Please try uploading the image file directly or check the URL."}
                
                # Create custom product
                response = self._create_custom_product(conversation, logo_result)
                
                # Clean up temporary file
                logo_processor.cleanup_logo(logo_result["file_path"])
                
                conversation["state"] = "completed"
                return response
        
        # Not a URL, remind about logo requirement
        return {"message": "Please upload your team logo as an image file or provide a direct URL to the logo image. I'll use it to customize your selected product!"}
    
    def _create_custom_product(self, conversation: Dict, logo_result: Dict) -> Dict:
        """Create custom product with logo"""
        try:
            product_info = conversation["product_selected"]
            product_id = product_info["id"]
            
            # Upload logo to Printify
            logo_filename = logo_result.get("original_name", "team_logo.png")
            upload_result = printify_service.upload_logo_image(logo_result["file_path"], logo_filename)
            
            if not upload_result["success"]:
                return {"message": f"Sorry, there was an issue uploading your logo: {upload_result['error']}"}
            
            # Create custom product
            product_result = printify_service.create_custom_product(
                product_id, 
                upload_result["image_id"]
            )
            
            if not product_result["success"]:
                return {"message": f"Sorry, there was an issue creating your custom product: {product_result['error']}"}
            
            # Format success response
            team_info = conversation.get("team_info", {})
            team_name = team_info.get("name", "your team")
            
            success_message = f"🎉 Awesome! I've created a custom {product_info['formatted']['title']} for {team_name}!\n\n"
            success_message += f"*Product Details:*\n"
            success_message += f"• {product_result['title']}\n"
            success_message += f"• Color: {product_result['variant_info']['color']}\n"
            success_message += f"• Size: {product_result['variant_info']['size']}\n\n"
            
            if product_result.get("mockup_url"):
                success_message += "Check out your customized product below! 👇"
                
                return {
                    "message": success_message,
                    "image_url": product_result["mockup_url"],
                    "purchase_url": product_result["purchase_url"],
                    "product_title": product_result["title"]
                }
            else:
                success_message += f"🛒 Ready to order? <{product_result['purchase_url']}|Click here to purchase>"
                return {"message": success_message}
            
        except Exception as e:
            logger.error(f"Error creating custom product: {e}")
            return {"message": "Sorry, there was an unexpected error creating your custom product. Please try again!"}
    
    def _send_message(self, channel: str, message: str):
        """Send text message to Slack"""
        try:
            self.client.chat_postMessage(
                channel=channel,
                text=message,
                unfurl_links=False
            )
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
    
    def _send_image_message(self, channel: str, image_url: str, caption: str = ""):
        """Send image message to Slack"""
        try:
            # Create rich message with image
            blocks = [
                {
                    "type": "image",
                    "image_url": image_url,
                    "alt_text": "Custom product mockup"
                }
            ]
            
            if caption:
                blocks.insert(0, {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": caption
                    }
                })
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                unfurl_links=False
            )
        except SlackApiError as e:
            logger.error(f"Error sending image message: {e}")
    
    def _send_product_result(self, channel: str, response: Dict):
        """Send product result with image and purchase link"""
        try:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": response["message"]
                    }
                },
                {
                    "type": "image",
                    "image_url": response["image_url"],
                    "alt_text": f"Custom {response['product_title']}"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🛒 *Ready to order?* <{response['purchase_url']}|Click here to purchase your custom {response['product_title']}>"
                    }
                }
            ]
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                unfurl_links=False
            )
        except SlackApiError as e:
            logger.error(f"Error sending product result: {e}")

# Global instance
slack_bot = SlackBot() 