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
from conversation_manager import conversation_manager

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class SlackBot:
    def __init__(self):
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.signing_secret = os.getenv('SLACK_SIGNING_SECRET')
    
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
                conversation_manager.reset_conversation(channel, user)
                self._send_message(channel, "Great! Let's start fresh. What type of merchandise would you like to create for your team? 🏆")
                return {"status": "success"}
            
            # Get conversation state
            conversation = conversation_manager.get_conversation(channel, user)
            
            # Check if user needs help due to errors
            recovery_message = conversation_manager.get_recovery_message(channel, user)
            if recovery_message and text.lower() not in ['help', 'restart', 'reset']:
                self._send_message(channel, recovery_message)
                return {"status": "recovery_suggested"}
            
            # Process message based on conversation state
            try:
                if conversation["state"] == "initial":
                    response = self._handle_initial_message(text, conversation, channel, user)
                elif conversation["state"] == "awaiting_product_selection":
                    response = self._handle_product_selection(text, conversation, channel, user)
                elif conversation["state"] == "awaiting_product_selection_with_logo":
                    response = self._handle_product_selection_with_logo(text, conversation, channel, user)
                elif conversation["state"] == "awaiting_logo":
                    response = self._handle_logo_request(text, conversation, event, channel, user)
                elif conversation["state"] == "completed":
                    response = self._handle_completed_conversation(text, conversation, channel, user)
                else:
                    response = self._handle_initial_message(text, conversation, channel, user)
                
                # Send response to Slack
                if response.get("message"):
                    self._send_message(channel, response["message"])
                
                if response.get("image_url"):
                    self._send_image_message(channel, response["image_url"], response.get("image_caption", ""))
                
                return {"status": "success"}
                
            except Exception as e:
                # Record error in conversation state
                error_msg = f"Processing error: {str(e)}"
                conversation_manager.record_error(channel, user, error_msg)
                
                # Send user-friendly error message
                self._send_error_message(channel, user, str(e))
                
                return {"status": "error", "error": str(e)}
            
        except Exception as e:
            logger.error(f"Critical error handling message: {e}")
            
            # Try to send generic error message
            try:
                if channel:
                    self._send_message(channel, "Sorry, I'm having technical difficulties. Please try again in a moment! 🔧")
            except:
                pass
            
            return {"status": "critical_error", "error": str(e)}
    
    def handle_file_share(self, event: Dict) -> Dict:
        """Handle file upload to Slack with improved error handling"""
        try:
            channel = event.get('channel')
            user = event.get('user')
            file_info = event.get('file', {})
            
            # Check for duplicate events
            if conversation_manager.is_duplicate_event(event):
                return {"status": "duplicate"}
            
            logger.info(f"Processing file share from {user} in {channel}")
            
            # Get conversation state
            conversation = conversation_manager.get_conversation(channel, user)
            
            # If no product selected yet, ask for product type first
            if not conversation.get("product_selected"):
                self._send_message(channel, "I see you've uploaded a logo! What type of product would you like to customize? Please tell me if you want a shirt, hoodie, or hat for your team.")
                # Update state to awaiting product selection with logo ready
                conversation_manager.update_conversation(channel, user, {
                    "state": "awaiting_product_selection_with_logo",
                    "pending_file": file_info
                })
                return {"status": "awaiting_product"}
            
            try:
                # Process the uploaded file
                logo_result = logo_processor.process_slack_file(file_info, self.client)
                
                if not logo_result["success"]:
                    error_msg = f"File processing failed: {logo_result['error']}"
                    conversation_manager.record_error(channel, user, error_msg)
                    self._send_message(channel, f"Sorry, there was an issue with your logo: {logo_result['error']}")
                    return {"status": "error"}
                
                # Process the logo and create product
                response = self._create_custom_product(conversation, logo_result, channel, user)
                
                # Send response with purchase link
                if response.get("image_url") and response.get("purchase_url"):
                    self._send_product_result(channel, response)
                elif response.get("message"):
                    self._send_message(channel, response["message"])
                
                # Update conversation state to completed
                conversation_manager.update_conversation(channel, user, {"state": "completed"})
                
                # Clean up temporary logo file
                logo_processor.cleanup_logo(logo_result["file_path"])
                
                return {"status": "success"}
                
            except Exception as e:
                # Record error and send user-friendly message
                conversation_manager.record_error(channel, user, f"File share processing error: {str(e)}")
                self._send_error_message(channel, user, str(e))
                return {"status": "error", "error": str(e)}
            
        except Exception as e:
            logger.error(f"Critical error handling file share: {e}")
            
            # Try to send generic error message
            try:
                if channel:
                    self._send_message(channel, "Sorry, I'm having technical difficulties processing your file. Please try again! 🔧")
            except:
                pass
            
            return {"status": "critical_error", "error": str(e)}
    
    def _handle_initial_message(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle initial parent message"""
        try:
            # Use OpenAI to analyze the request
            analysis = openai_service.analyze_parent_request(text)
            
            # Prepare updates for conversation state
            updates = {}
            
            # Store team information
            if analysis.get("sport_mentioned"):
                if "team_info" not in conversation:
                    conversation["team_info"] = {}
                conversation["team_info"]["sport"] = analysis["sport_mentioned"]
                updates["team_info"] = conversation["team_info"]
            
            if analysis.get("team_mentioned"):
                if "team_info" not in conversation:
                    conversation["team_info"] = {}
                conversation["team_info"]["name"] = analysis["team_mentioned"]
                updates["team_info"] = conversation["team_info"]
            
            # Check if product type was specified
            if analysis.get("product_specified") and analysis.get("product_type"):
                # Find matching product
                product_match = product_service.find_product_by_intent(text)
                if product_match:
                    updates["product_selected"] = product_match
                    updates["state"] = "awaiting_logo"
                    
                    # Update conversation state
                    conversation_manager.update_conversation(channel, user, updates)
                    
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
            updates["state"] = "awaiting_product_selection"
            conversation_manager.update_conversation(channel, user, updates)
            
            suggestion_message = product_service.get_product_suggestions_text()
            
            return {"message": f"{analysis.get('response_message', 'Hi there!')}\n\n{suggestion_message}"}
            
        except Exception as e:
            logger.error(f"Error in _handle_initial_message: {e}")
            raise e
    
    def _handle_product_selection(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle product selection from parent"""
        try:
            # Try to find product based on selection
            product_match = product_service.find_product_by_intent(text)
            
            if product_match:
                # Update conversation state
                updates = {
                    "product_selected": product_match,
                    "state": "awaiting_logo"
                }
                conversation_manager.update_conversation(channel, user, updates)
                
                # Generate logo request message
                team_context = ""
                if conversation.get("team_info"):
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
                
        except Exception as e:
            logger.error(f"Error in _handle_product_selection: {e}")
            raise e
    
    def _handle_product_selection_with_logo(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle product selection when logo is already uploaded"""
        try:
            # Use OpenAI to understand the product selection
            analysis = openai_service.analyze_parent_request(text)
            
            # Find matching product
            product_match = product_service.find_product_by_intent(text)
            
            if product_match:
                # Update conversation with selected product
                conversation_manager.update_conversation(channel, user, {
                    "product_selected": product_match,
                    "state": "processing_with_logo"
                })
                
                # Get the pending file info
                pending_file = conversation.get("pending_file")
                if pending_file:
                    # Process the uploaded file
                    logo_result = logo_processor.process_slack_file(pending_file, self.client)
                    
                    if not logo_result["success"]:
                        error_msg = f"File processing failed: {logo_result['error']}"
                        conversation_manager.record_error(channel, user, error_msg)
                        return {"message": f"Sorry, there was an issue with your logo: {logo_result['error']}"}
                    
                    # Create custom product
                    response = self._create_custom_product(conversation, logo_result, channel, user)
                    
                    # Clean up temporary logo file
                    logo_processor.cleanup_logo(logo_result["file_path"])
                    
                    # Update conversation state to completed
                    conversation_manager.update_conversation(channel, user, {"state": "completed"})
                    
                    return response
                else:
                    # No pending file, ask for logo
                    conversation_manager.update_conversation(channel, user, {"state": "awaiting_logo"})
                    return {"message": "Great! Now please upload your team logo as an image file or provide a direct URL to the logo image."}
            else:
                # Product not clear, ask for clarification
                suggestion_message = product_service.get_product_suggestions_text()
                return {"message": f"I'm not sure which product you'd like. {suggestion_message}"}
                
        except Exception as e:
            logger.error(f"Error in _handle_product_selection_with_logo: {e}")
            raise e
    
    def _handle_logo_request(self, text: str, conversation: Dict, event: Dict, channel: str, user: str) -> Dict:
        """Handle logo URL or other text when awaiting logo"""
        try:
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
                        error_msg = f"Logo URL processing failed: {logo_result['error']}"
                        conversation_manager.record_error(channel, user, error_msg)
                        return {"message": f"Sorry, there was an issue with your logo URL: {logo_result['error']}. Please try uploading the image file directly or check the URL."}
                    
                    # Create custom product
                    response = self._create_custom_product(conversation, logo_result, channel, user)
                    
                    # Clean up temporary file
                    logo_processor.cleanup_logo(logo_result["file_path"])
                    
                    # Update conversation state to completed
                    conversation_manager.update_conversation(channel, user, {"state": "completed"})
                    
                    return response
            
            # Not a URL, remind about logo requirement
            return {"message": "Please upload your team logo as an image file or provide a direct URL to the logo image. I'll use it to customize your selected product!"}
            
        except Exception as e:
            logger.error(f"Error in _handle_logo_request: {e}")
            raise e
    
    def _handle_completed_conversation(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle messages after product has been completed"""
        try:
            # Check if user wants to create another product
            analysis = openai_service.analyze_parent_request(text)
            
            # Look for indicators of wanting to create something new
            new_product_indicators = [
                "another", "different", "new", "also want", "now i want", "next", 
                "can i get", "i'd like", "shirt", "hoodie", "hat", "cap", "sweatshirt"
            ]
            
            text_lower = text.lower()
            wants_new_product = any(indicator in text_lower for indicator in new_product_indicators)
            
            if wants_new_product:
                # Check if they specified a product type
                product_match = product_service.find_product_by_intent(text)
                if product_match:
                    # Start new product flow
                    updates = {
                        "product_selected": product_match,
                        "state": "awaiting_logo"
                    }
                    conversation_manager.update_conversation(channel, user, updates)
                    
                    # Generate logo request message
                    team_context = ""
                    if conversation.get("team_info"):
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
                    # They want something new but didn't specify what
                    conversation_manager.update_conversation(channel, user, {"state": "awaiting_product_selection"})
                    suggestion_message = product_service.get_product_suggestions_text()
                    return {"message": f"Great! What else would you like to create for your team?\n\n{suggestion_message}"}
            
            # Check for purchase-related questions
            purchase_indicators = ["buy", "purchase", "order", "get", "link", "where", "how"]
            wants_purchase_info = any(indicator in text_lower for indicator in purchase_indicators)
            
            if wants_purchase_info:
                return {"message": "I'd be happy to help you get that product! Please use the purchase link I provided above, or if you need a new link, just let me know which product you're referring to."}
            
            # Generic positive response - don't restart the flow
            positive_responses = ["love", "great", "awesome", "perfect", "thanks", "thank you", "looks good", "nice"]
            is_positive = any(response in text_lower for response in positive_responses)
            
            if is_positive:
                return {"message": "I'm so glad you like it! 🎉 Is there anything else you'd like to create for your team? Just let me know what product you're interested in!"}
            
            # Default response for completed conversations
            return {"message": "Thanks! Is there anything else I can help you create for your team? Just tell me what product you're interested in (shirt, hoodie, hat) and I'll get started!"}
            
        except Exception as e:
            logger.error(f"Error in _handle_completed_conversation: {e}")
            raise e
    
    def _create_custom_product(self, conversation: Dict, logo_result: Dict, channel: str, user: str) -> Dict:
        """Create custom product with logo"""
        try:
            product_info = conversation["product_selected"]
            product_id = product_info["id"]
            
            # Upload logo to Printify
            logger.info(f"Uploading logo for {channel}_{user}")
            logo_filename = logo_result.get("original_name", "team_logo.png")
            upload_result = printify_service.upload_logo_image(logo_result["file_path"], logo_filename)
            
            if not upload_result["success"]:
                error_msg = f"Logo upload failed: {upload_result['error']}"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": f"Sorry, there was an issue uploading your logo: {upload_result['error']}"}
            
            # Create custom product
            logger.info(f"Creating custom product for {channel}_{user} with logo {upload_result['image_id']}")
            product_result = printify_service.create_custom_product(
                product_id, 
                upload_result["image_id"]
            )
            
            if not product_result["success"]:
                error_msg = f"Product creation failed: {product_result['error']}"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": f"Sorry, there was an issue creating your custom product: {product_result['error']}"}
            
            # Success! Format response
            logger.info(f"Successfully created product {product_result['product_id']} for {channel}_{user}")
            
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
            conversation_manager.record_error(channel, user, f"Product creation exception: {str(e)}")
            return {"message": "Sorry, there was an unexpected error creating your custom product. Please try again or type 'restart' to begin fresh!"}
    
    def _send_error_message(self, channel: str, user: str, error: str):
        """Send user-friendly error message"""
        try:
            # Check if user has had multiple errors
            if conversation_manager.should_show_help(channel, user):
                message = ("I'm having trouble helping you right now. Let me suggest a fresh start! "
                          "Type 'restart' to begin again, or let me know specifically what you need help with. "
                          "I'm here to create awesome team merchandise! 🏆")
            else:
                message = ("Oops! Something went wrong on my end. Please try again, "
                          "or type 'restart' if you'd like to start fresh. 🔧")
            
            self._send_message(channel, message)
            
        except Exception as e:
            logger.error(f"Error sending error message: {e}")
    
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