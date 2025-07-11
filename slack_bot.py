import os
import logging
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, Optional, List
from dotenv import load_dotenv

from product_service import product_service
from openai_service import openai_service
from logo_processor import logo_processor
from printify_service import printify_service
from conversation_manager import conversation_manager
from database_service import database_service

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
                
                # Automatically use default logo and create initial drops
                default_logo_url = "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png/v1/fill/w_190,h_190,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/MiM%20Color%20Logo.png"
                
                # Send welcome message
                product_suggestions = product_service.get_product_suggestions_text()
                service_msg = f"""Welcome to the team merchandise service! 🏆

I'll create custom mockups of our top youth sports products:

{product_suggestions}

📸 *Just upload your team logo* and I'll show you these products with your design!"""
                self._send_message(channel, service_msg)
                
                # Automatically process the default logo
                logger.info("Auto-processing default logo for restart")
                return self._handle_logo_request(default_logo_url, conversation_manager.get_conversation(channel, user), event, channel, user)
                
            
            # Get conversation state
            conversation = conversation_manager.get_conversation(channel, user)
            
            # Check if user needs help due to errors
            recovery_message = conversation_manager.get_recovery_message(channel, user)
            if recovery_message and text.lower() not in ['help', 'restart', 'reset']:
                self._send_message(channel, recovery_message)
                return {"status": "recovery_suggested"}
            
            # Process message based on conversation state
            try:
                # Check for URL first - handle logo URLs from any state
                if "http" in text.lower():
                    # Process logo URL regardless of current state
                    response = self._handle_logo_request(text, conversation, event, channel, user)
                else:
                    # Process message based on conversation state
                    if conversation["state"] == "initial":
                        response = self._handle_initial_message(text, conversation, channel, user)
                    elif conversation["state"] == "awaiting_product_selection":
                        response = self._handle_product_selection(text, conversation, channel, user)
                    elif conversation["state"] == "awaiting_logo":
                        response = self._handle_logo_request(text, conversation, event, channel, user)
                    elif conversation["state"] == "awaiting_color_selection":
                        response = self._handle_color_selection(text, conversation, channel, user)
                    elif conversation["state"] == "completed":
                        response = self._handle_completed_conversation(text, conversation, channel, user)
                    else:
                        response = self._handle_initial_message(text, conversation, channel, user)
                
                # Send response to Slack
                if response.get("image_url") and response.get("purchase_url"):
                    # Send product result with image and purchase link
                    self._send_product_result(channel, response["image_url"], response["purchase_url"], response["product_title"], response.get("publish_method"))
                elif response.get("message"):
                    self._send_message(channel, response["message"])
                elif response.get("image_url"):
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
        """Handle file upload to Slack with logo persistence"""
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
            
            # Process the uploaded file and upload to Printify for persistence
            try:
                # Process the uploaded file
                logo_result = logo_processor.process_slack_file(file_info, self.client)
                
                if not logo_result["success"]:
                    error_msg = f"File processing failed: {logo_result['error']}"
                    conversation_manager.record_error(channel, user, error_msg)
                    self._send_message(channel, f"Sorry, there was an issue with your logo: {logo_result['error']}")
                    return {"status": "error"}
                
                # Upload logo to Printify for persistence
                logger.info(f"Uploading logo to Printify for persistence: {channel}_{user}")
                logo_filename = logo_result.get("original_name", "team_logo.png")
                upload_result = printify_service.upload_image_from_file(logo_result["file_path"], logo_filename)
                
                if not upload_result["success"]:
                    error_msg = f"Logo upload failed: {upload_result['error']}"
                    conversation_manager.record_error(channel, user, error_msg)
                    self._send_message(channel, f"Sorry, there was an issue uploading your logo: {upload_result['error']}")
                    return {"status": "error"}
                
                # Store logo info in conversation for reuse
                logo_info = {
                    "printify_image_id": upload_result["image_id"],
                    "preview_url": upload_result.get("preview_url"),
                    "filename": logo_filename,
                    "uploaded_at": conversation_manager._get_timestamp()
                }
                
                # Update conversation with persistent logo and start creating default drops
                conversation_manager.update_conversation(channel, user, {
                    "logo_info": logo_info,
                    "state": "creating_mockups"
                })
                
                # Clean up temporary logo file
                logo_processor.cleanup_logo(logo_result["file_path"])
                
                # Get updated conversation state
                updated_conversation = conversation_manager.get_conversation(channel, user)
                
                # Create all 3 drops with default colors immediately
                self._generate_all_mockups_with_default_colors(updated_conversation, logo_info, channel, user)
                
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
                product_match = product_service.find_product_by_intent_ai(text)
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
            
            # Always set to awaiting_logo state for new optimized flow
            updates["state"] = "awaiting_logo"
            conversation_manager.update_conversation(channel, user, updates)
            
            # Get actual product suggestions from our cache
            product_suggestions = product_service.get_product_suggestions_text()
            
            # Service description with immediate logo request
            service_description = f"""Welcome to the team merchandise service! 🏆

I'll create custom mockups of our top youth sports products:

{product_suggestions}

📸 *Just upload your team logo* and I'll show you these products with your design!"""
            
            return {"message": service_description}
            
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
                
                # Check if we already have a logo stored
                stored_logo = conversation.get("logo_info")
                if stored_logo and stored_logo.get("printify_image_id"):
                    # Use stored logo to create product immediately
                    logger.info(f"Using stored logo for product creation: {stored_logo['printify_image_id']}")
                    
                    # Get updated conversation with product selection
                    updated_conversation = conversation_manager.get_conversation(channel, user)
                    response = self._create_custom_product_with_stored_logo(updated_conversation, stored_logo, channel, user)
                    
                    # Update state to completed
                    conversation_manager.update_conversation(channel, user, {"state": "completed"})
                    
                    return response
                else:
                    # No stored logo, ask for logo upload
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
                    
                    # Upload to Printify for persistence
                    logger.info(f"Uploading URL logo to Printify for persistence: {channel}_{user}")
                    logo_filename = logo_result.get("original_name", "team_logo.png")
                    upload_result = printify_service.upload_image_from_file(logo_result["file_path"], logo_filename)
                    
                    if not upload_result["success"]:
                        error_msg = f"Logo upload failed: {upload_result['error']}"
                        conversation_manager.record_error(channel, user, error_msg)
                        return {"message": f"Sorry, there was an issue uploading your logo: {upload_result['error']}"}
                    
                    # Store logo info for reuse
                    logo_info = {
                        "printify_image_id": upload_result["image_id"],
                        "preview_url": upload_result.get("preview_url"),
                        "filename": logo_filename,
                        "uploaded_at": conversation_manager._get_timestamp(),
                        "source": "url"
                    }
                    
                    # Update conversation with logo and start creating default drops
                    conversation_manager.update_conversation(channel, user, {
                        "logo_info": logo_info,
                        "state": "creating_mockups"
                    })
                    
                    # Clean up temporary file
                    logo_processor.cleanup_logo(logo_result["file_path"])
                    
                    # Get updated conversation state
                    updated_conversation = conversation_manager.get_conversation(channel, user)
                    
                    # Create all 3 drops with default colors immediately
                    self._generate_all_mockups_with_default_colors(updated_conversation, logo_info, channel, user)
                    
                    return {"status": "success"}
            
            # Not a URL, remind about logo requirement (prefer URLs)
            return {"message": "Please provide your team logo! For best results, share a direct URL link to your logo image (like from Google Drive, Dropbox, or any image hosting site). You can also upload an image file if needed."}
            
        except Exception as e:
            logger.error(f"Error in _handle_logo_request: {e}")
            raise e
    
    def _handle_completed_conversation(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle messages after product has been completed using LLM intelligence"""
        try:
            text_lower = text.lower()
            
            # Check for immediate action requests like "yes create the drop!" or "create it!"
            action_phrases = ['yes create', 'create the drop', 'create it', 'make it', 'yes make', 'go ahead', 'let\'s do it']
            if any(phrase in text_lower for phrase in action_phrases):
                # Check if we have recent context about what they want to create
                recent_context = conversation.get("recent_discussion", "")
                logo_info = conversation.get("logo_info")
                
                if logo_info and logo_info.get("printify_image_id"):
                    # Try to extract product and color from recent context or use defaults
                    if "baby blue" in recent_context.lower() or "sky" in recent_context.lower():
                        # They want a Baby Blue t-shirt based on recent discussion
                        self._send_message(channel, "🎨 Creating your Baby Blue t-shirt with your logo...")
                        selected_variant = product_service._find_variant_by_color('12', 'Baby Blue')
                        if selected_variant:
                            product_info = {"id": "12", "formatted": {"title": "Unisex Jersey Short Sleeve Tee"}}
                            response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                            if response.get("image_url") and response.get("purchase_url"):
                                self._send_product_result(channel, response["image_url"], response["purchase_url"], 
                                                         f"Team {response['product_title']} (Baby Blue)", response.get("publish_method"))
                                return {"status": "success"}
                
                # Fallback for unclear context
                return {"message": "I'd love to help create that! Could you let me know which product (t-shirt or hoodie) and what color you'd like? 🎨"}
            
            logo_info = conversation.get("logo_info")
            
            # Check for specific color/product requests FIRST - immediate action phrases
            color_action_phrases = ['show me', 'make', 'create', 'i want', 'give me']
            has_action_phrase = any(phrase in text_lower for phrase in color_action_phrases)
            has_product_context = any(word in text_lower for word in ['shirt', 'tshirt', 't-shirt', 'hoodie', 'blue', 'red', 'purple', 'sky', 'baby blue', 'color'])
            
            if has_action_phrase and has_product_context and logo_info and logo_info.get("printify_image_id"):
                # Immediate acknowledgment for product creation requests
                self._send_message(channel, "🎨 Got it! Creating that for you right now...")
                
                # Get logo URL for AI analysis
                logo_url = logo_info.get("url", "No logo URL available")
                
                # Use AI-powered color analysis with logo context
                selected_variants = product_service.parse_color_preferences_ai(text, logo_url)
                
                if selected_variants:
                    # Create mockups with the selected color variants
                    self._generate_specific_color_mockups(conversation, logo_info, selected_variants, channel, user)
                    return {"status": "success"}
                else:
                    # If AI couldn't parse it, try basic color matching for common requests
                    if "sky" in text_lower or "baby blue" in text_lower:
                        # They want a baby blue t-shirt
                        selected_variant = product_service._find_variant_by_color('12', 'Baby Blue')
                        if selected_variant:
                            product_info = {"id": "12", "formatted": {"title": "Unisex Jersey Short Sleeve Tee"}}
                            response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                            if response.get("image_url") and response.get("purchase_url"):
                                self._send_product_result(channel, response["image_url"], response["purchase_url"], 
                                                         f"Team {response['product_title']} (Baby Blue)", response.get("publish_method"))
                                return {"status": "success"}
            
            # Check if user is asking a question about colors/options (only if not a product creation request)
            elif self._is_asking_for_options(text):
                # Add channel and user to conversation for the options query
                conversation['channel'] = channel
                conversation['user'] = user
                response_data = self._handle_options_query(text, conversation)
                # Store the question context for follow-up actions
                conversation_manager.update_conversation(channel, user, {"recent_discussion": text})
                
                # Handle different response types
                if isinstance(response_data, dict) and response_data.get("status") == "created_example":
                    return {"status": "success"}  # Example product was created
                else:
                    return {"message": response_data if isinstance(response_data, str) else "I can help you explore our color options!"}
            
            # Check for specific color requests (only if not asking for options and not handled above)
            elif logo_info and logo_info.get("printify_image_id"):
                # Get logo URL for AI analysis
                logo_url = logo_info.get("url", "No logo URL available")
                
                # Use AI-powered color analysis with logo context
                selected_variants = product_service.parse_color_preferences_ai(text, logo_url)
                
                if selected_variants:
                    # User wants specific color changes - create new drops!
                    self._send_message(channel, f"🎨 Creating new drops with your color preferences...")
                    
                    # Create mockups with the selected color variants
                    self._generate_specific_color_mockups(conversation, logo_info, selected_variants, channel, user)
                    
                    return {"status": "success"}
            
            # Use OpenAI to understand user intent in context
            analysis = openai_service.analyze_parent_request(text)
            
            # Get conversation context for LLM
            context_info = {
                "previous_product": conversation.get("product_selected", {}).get("formatted", {}).get("title", "unknown"),
                "team_info": conversation.get("team_info", {}),
                "conversation_state": "completed_product"
            }
            
            # Let LLM determine the best response based on user message and context
            try:
                # Create a context-aware prompt for the LLM
                context_prompt = f"""
                The user just completed creating a custom {context_info['previous_product']} and now said: "{text}"
                
                Team context: {context_info.get('team_info', {})}
                
                Determine the user's intent and respond appropriately:
                - If they want a different product type, identify what product they want
                - If they're asking about purchasing, provide helpful purchase guidance  
                - If they're just being positive/thankful, respond enthusiastically
                - If they want to modify the same product, guide them appropriately
                
                Available products: shirt (Unisex Jersey Short Sleeve Tee), hoodie (Unisex College Hoodie). Default products shown are Jersey Tee and College Hoodie.
                
                Respond as an enthusiastic youth sports merchandise assistant.
                """
                
                # Get LLM response for context-aware handling
                llm_response = openai_service.get_contextual_response(context_prompt, text)
                
                # Check if user wants a different product (but no logo uploaded for new flow)
                product_match = product_service.find_product_by_intent_ai(text)
                if product_match and isinstance(product_match, dict) and product_match.get('id'):
                    # Check if they have existing logo to use
                    if logo_info and logo_info.get("printify_image_id"):
                        # Get product title safely
                        product_title = "product"
                        if product_match.get('formatted') and product_match['formatted'].get('title'):
                            product_title = product_match['formatted']['title']
                        elif product_match.get('product') and product_match['product'].get('title'):
                            product_title = product_match['product']['title']
                        
                        # Use existing logo for new product
                        self._send_message(channel, f"🎨 Creating {product_title} with your existing logo...")
                        
                        # Find default color for this product
                        default_variants = {
                            '12': 'Black',    # Unisex Jersey Short Sleeve Tee
                            '92': 'Navy'      # Unisex College Hoodie
                        }
                        product_id = product_match.get('id')
                        default_color = default_variants.get(product_id, 'Black')
                        selected_variant = product_service._find_variant_by_color(product_id, default_color)
                        
                        if selected_variant and product_match and product_match.get('formatted'):
                            product_info = {"id": product_id, "formatted": {"title": product_match['formatted']['title']}}
                            response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                            
                            if response.get("image_url") and response.get("purchase_url"):
                                color = selected_variant.get('options', {}).get('color', 'Default')
                                product_title_with_color = f"{response['product_title']} ({color})"
                                colors_by_product = product_service.get_available_colors_for_best_products()
                                available_colors = colors_by_product.get(product_id, [])
                                self._send_product_result_with_alternatives(channel, response["image_url"], response["purchase_url"], product_title_with_color, available_colors, response.get("publish_method"), logo_info.get("url"))
                                return {"status": "success"}
                    else:
                        # Start new product flow - need logo
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
                
                # Use LLM response for other cases
                return {"message": llm_response}
                
            except Exception as llm_error:
                logger.warning(f"LLM contextual response failed: {llm_error}, falling back to simple logic")
                
                # Fallback to simple keyword-based logic if LLM fails
                text_lower = text.lower()
                
                # Check for purchase-related questions
                purchase_indicators = ["buy", "purchase", "order", "get", "link", "where", "how"]
                if any(indicator in text_lower for indicator in purchase_indicators):
                    return {"message": "I'd be happy to help you get that product! Please use the purchase link I provided above, or if you need a new link, just let me know which product you're referring to."}
                
                # Check if they want another product
                if any(word in text_lower for word in ["shirt", "hoodie", "hat", "different", "another", "instead"]):
                    product_match = product_service.find_product_by_intent_ai(text)
                    if product_match and product_match.get('id') and product_match.get('formatted'):
                        # Use existing logo if available
                        if logo_info and logo_info.get("printify_image_id"):
                            return {"message": f"Great! I'll create a {product_match['formatted']['title']} with your existing logo. Any specific color you'd like?"}
                        else:
                            conversation_manager.update_conversation(channel, user, {
                                "product_selected": product_match,
                                "state": "awaiting_logo"
                            })
                            return {"message": f"Great! Let's create a {product_match['formatted']['title']} for your team. Please upload your logo or provide a URL."}
                    else:
                        suggestion_message = product_service.get_product_suggestions_text()
                        return {"message": f"What would you like to create next?\n\n{suggestion_message}"}
                
                # Default positive response
                return {"message": "I'm so glad you like it! 🎉 Want different colors? Just say something like 'red t-shirt' or 'black hat'! Or let me know if you want a different product type."}
            
        except Exception as e:
            logger.error(f"Error in _handle_completed_conversation: {e}")
            raise e
    
    def _handle_color_selection(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle color selection input from user"""
        try:
            # Get logo URL for AI analysis
            logo_info = conversation.get("logo_info", {})
            logo_url = logo_info.get("url", "No logo URL available")
            
            # Use AI-powered color analysis with logo context
            selected_variants = product_service.parse_color_preferences_ai(text, logo_url)
            
            if not selected_variants:
                # No valid color selections found, show color options again
                color_message = product_service.format_color_selection_message()
                return {"message": f"I didn't quite understand your color preferences. Let me show you the options again:\n\n{color_message}"}
            
            # Store selected variants in conversation
            conversation_manager.update_conversation(channel, user, {
                "selected_variants": selected_variants,
                "state": "creating_mockups"
            })
            
            # Show confirmation of color selections
            color_summary = []
            product_names = {'157': 'T-shirt', '314': 'Hoodie', '1221': 'Hat'}
            
            for product_id, variant in selected_variants.items():
                product_name = product_names.get(product_id, f"Product {product_id}")
                color = variant.get('options', {}).get('color', 'Unknown')
                color_summary.append(f"• *{product_name}:* {color}")
            
            confirmation_msg = f"🎨 Perfect! Creating your products in these colors:\n" + "\n".join(color_summary)
            self._send_message(channel, confirmation_msg)
            
            # Get logo info and generate mockups with selected colors
            logo_info = conversation.get("logo_info")
            if logo_info:
                self._generate_all_mockups_with_colors(conversation, logo_info, selected_variants, channel, user)
            else:
                return {"message": "Sorry, I can't find your logo information. Please upload your logo again."}
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error in _handle_color_selection: {e}")
            return {"message": "Sorry, there was an issue processing your color selection. Please try again or type 'default colors' to use standard colors."}
    
    def _create_custom_product(self, conversation: Dict, logo_result: Dict, channel: str, user: str) -> Dict:
        """Create custom product design with uploaded logo"""
        try:
            product_info = conversation["product_selected"]
            team_info = conversation.get("team_info", {})
            
            # Upload logo to Printify
            logger.info(f"Uploading logo for {channel}_{user}")
            logo_filename = logo_result.get("original_name", "team_logo.png")
            upload_result = printify_service.upload_image_from_file(logo_result["file_path"], logo_filename)
            
            if not upload_result["success"]:
                error_msg = f"Logo upload failed: {upload_result['error']}"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": f"Sorry, there was an issue uploading your logo: {upload_result['error']}"}
            
            # Get product blueprint details from product service
            product_details = product_service.get_product_by_id(str(product_info['id']))
            
            if not product_details:
                error_msg = "Selected product not found in catalog"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": "Sorry, there was an issue finding the selected product. Please try again!"}
            
            # Convert to the format expected by create_product_design
            selected_product = {
                'id': product_info['id'],
                'title': product_details.get('title', 'Custom Product'),
                'blueprint_id': product_details.get('blueprint_id'),
                'print_provider_id': product_details.get('print_provider_id') or product_details.get('primary_print_provider_id'),
                'variants': product_details.get('variants', []),
                'type': product_details.get('category', 'apparel'),
                'base_price': product_details.get('base_price', 20.00)
            }
            
            # Get first available variant for mockup
            variants = selected_product.get('variants', [])
            if not variants:
                error_msg = "No variants available for selected product"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": "Sorry, this product doesn't have any available options. Please choose a different product!"}
            
            first_variant = variants[0]
            
            # Create product design for mockup
            logger.info(f"Creating product design for {channel}_{user} with logo {upload_result['image_id']}")
            design_result = printify_service.create_product_design(
                blueprint_id=selected_product['blueprint_id'],
                print_provider_id=selected_product['print_provider_id'],
                variant_id=first_variant['id'],
                image_id=upload_result["image_id"],
                product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}",
                database_service=database_service
            )
            
            if not design_result["success"]:
                error_msg = f"Design creation failed: {design_result['error']}"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": f"Sorry, there was an issue creating your design: {design_result['error']}"}
            
            # Save design to database
            design_data = {
                "name": f"{team_info.get('name', 'Team')} {selected_product['title']}",
                "description": f"Custom {selected_product['title']} with team logo",
                "blueprint_id": selected_product['blueprint_id'],
                "print_provider_id": selected_product['print_provider_id'],
                "printify_product_id": design_result.get("product_id"),
                "team_logo_image_id": upload_result["image_id"],
                "mockup_image_url": design_result.get("mockup_url"),
                "base_price": selected_product.get('base_price', 20.00),
                "markup_percentage": 50.0,
                "created_by": f"{channel}_{user}",
                "team_info": team_info,
                "product_type": selected_product.get('type', 'apparel')
            }
            
            design_id = database_service.save_product_design(design_data)
            
            # Generate storefront URL
            drop_url = database_service.generate_drop_url(design_id)
            
            # Success! Format response
            logger.info(f"Successfully created design {design_id} for {channel}_{user}")
            
            team_name = team_info.get("name", "your team")
            success_message = f"🎉 Awesome! I've created a custom {selected_product['title']} design for {team_name}!\n\n"
            success_message += "Your design drop is ready for purchase! 👇"
            
            return {
                "message": success_message,
                "image_url": design_result.get("mockup_url"),
                "purchase_url": drop_url,
                "product_title": design_data["name"]
            }
            
        except Exception as e:
            logger.error(f"Error creating custom product design: {e}")
            conversation_manager.record_error(channel, user, f"Design creation exception: {str(e)}")
            return {"message": "Sorry, there was an unexpected error creating your design. Please try again or type 'restart' to begin fresh!"}
    
    def _generate_all_mockups_in_series(self, conversation: Dict, logo_info: Dict, channel: str, user: str):
        """Generate mockups for all 3 products in series, showing each as it completes"""
        try:
            team_info = conversation.get("team_info", {})
            team_name = team_info.get("name", "your team")
            
            # Send initial message
            self._send_message(channel, f"🎨 Perfect! Creating mockups for {team_name}...")
            
            # Get the best products from our cache - use only Jersey Tee and College Hoodie
            best_products = product_service.get_best_products()
            products_order = [
                ("12", "Unisex Jersey Short Sleeve Tee"),  # Jersey Short Sleeve Tee
                ("92", "Unisex College Hoodie")   # College Hoodie
            ]
            
            for i, (product_id, product_name) in enumerate(products_order):
                if product_id not in best_products:
                    continue
                    
                # Add delay between products to avoid rate limiting (except for first product)
                if i > 0:
                    import time
                    # Standard delay between products
                    delay = 2
                    time.sleep(delay)
                    logger.info(f"Added {delay}-second delay before creating {product_name}")
                    
                try:
                    # Create mockup for this product
                    product_info = {"id": product_id, "formatted": {"title": product_name}}
                    response = self._create_single_mockup(conversation, logo_info, product_info, channel, user)
                    
                    if response.get("image_url") and response.get("purchase_url"):
                        # Send this mockup immediately
                        self._send_product_result(channel, response["image_url"], response["purchase_url"], response["product_title"], response.get("publish_method"))
                        
                        # Simple progress message (only for jersey tee -> hoodie)
                        if product_id == "12":  # Jersey Tee, next is hoodie
                            self._send_message(channel, f"⚡ Creating hoodie...")
                    
                except Exception as e:
                    logger.error(f"Error creating mockup for {product_name}: {e}")
                    # Check if it's a rate limit issue
                    if "rate" in str(e).lower() or "429" in str(e) or "too many" in str(e).lower():
                        self._send_message(channel, f"⏱️ API rate limit hit - retrying {product_name} in a moment...")
                        import time
                        time.sleep(5)  # Longer delay for rate limit recovery
                        # Retry once
                        try:
                            response = self._create_single_mockup(conversation, logo_info, product_info, channel, user)
                            if response.get("image_url") and response.get("purchase_url"):
                                self._send_product_result(channel, response["image_url"], response["purchase_url"], response["product_title"], response.get("publish_method"))
                            else:
                                self._send_message(channel, f"⚠️ {product_name} creation failed after retry - you can try uploading a new logo later")
                        except Exception as retry_e:
                            logger.error(f"Retry failed for {product_name}: {retry_e}")
                            self._send_message(channel, f"⚠️ {product_name} temporarily unavailable - try uploading a new logo later")
                    else:
                        self._send_message(channel, f"Had trouble with the {product_name}, but continuing with other products...")
            
            # Final message with more guidance
            self._send_message(channel, "🎉 *All done!* Click any link above to pick sizes and colors. Want different colors? Just say 'red t-shirt' or 'black hoodie'!")
            
            # Update conversation state
            conversation_manager.update_conversation(channel, user, {"state": "completed"})
            
        except Exception as e:
            logger.error(f"Error in _generate_all_mockups_in_series: {e}")
            self._send_message(channel, "Sorry, had some issues creating the mockups. Please try uploading your logo again!")
    
    def _generate_all_mockups_with_colors(self, conversation: Dict, logo_info: Dict, selected_variants: Dict, channel: str, user: str):
        """Generate mockups for the 2 main products using selected color variants"""
        try:
            team_info = conversation.get("team_info", {})
            team_name = team_info.get("name", "your team")
            
            # Products in order: Jersey Tee, College Hoodie only
            products_order = [
                ("12", "Unisex Jersey Short Sleeve Tee"),  # Jersey Short Sleeve Tee
                ("92", "Unisex College Hoodie")   # College Hoodie
            ]
            
            for i, (product_id, product_name) in enumerate(products_order):
                if product_id not in selected_variants:
                    logger.warning(f"No selected variant for product {product_id}, skipping")
                    continue
                    
                # Add delay between products to avoid rate limiting (except for first product)
                if i > 0:
                    import time
                    # Standard delay between products
                    delay = 2
                    time.sleep(delay)
                    logger.info(f"Added {delay}-second delay before creating {product_name}")
                    
                try:
                    # Create mockup for this product with selected variant
                    product_info = {"id": product_id, "formatted": {"title": product_name}}
                    selected_variant = selected_variants[product_id]
                    
                    response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                    
                    if response.get("image_url") and response.get("purchase_url"):
                        # Send this mockup immediately
                        color = selected_variant.get('options', {}).get('color', 'Unknown')
                        product_title_with_color = f"{response['product_title']} ({color})"
                        self._send_product_result(channel, response["image_url"], response["purchase_url"], product_title_with_color, response.get("publish_method"))
                        
                        # Simple progress message (only for jersey tee -> hoodie)
                        if product_id == "12":  # Jersey Tee, next is hoodie
                            self._send_message(channel, f"⚡ Creating hoodie...")
                    
                except Exception as e:
                    logger.error(f"Error creating mockup for {product_name}: {e}")
                    # Check if it's a rate limit issue
                    if "rate" in str(e).lower() or "429" in str(e) or "too many" in str(e).lower():
                        self._send_message(channel, f"⏱️ API rate limit hit - retrying {product_name} in a moment...")
                        import time
                        time.sleep(5)  # Longer delay for rate limit recovery
                        # Retry once
                        try:
                            response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                            if response.get("image_url") and response.get("purchase_url"):
                                color = selected_variant.get('options', {}).get('color', 'Unknown')
                                product_title_with_color = f"{response['product_title']} ({color})"
                                self._send_product_result(channel, response["image_url"], response["purchase_url"], product_title_with_color, response.get("publish_method"))
                            else:
                                self._send_message(channel, f"⚠️ {product_name} creation failed after retry - you can try uploading a new logo later")
                        except Exception as retry_e:
                            logger.error(f"Retry failed for {product_name}: {retry_e}")
                            self._send_message(channel, f"⚠️ {product_name} temporarily unavailable - try uploading a new logo later")
                    else:
                        self._send_message(channel, f"Had trouble with the {product_name}, but continuing with other products...")
            
            # Final message with more guidance
            self._send_message(channel, "🎉 *All done!* Click any link above to order your team merchandise. Want a different design? Just upload a new logo!")
            
            # Update conversation state
            conversation_manager.update_conversation(channel, user, {"state": "completed"})
            
        except Exception as e:
            logger.error(f"Error in _generate_all_mockups_with_colors: {e}")
            self._send_message(channel, "Sorry, had some issues creating the mockups. Please try uploading your logo again!")
    
    def _generate_all_mockups_with_default_colors(self, conversation: Dict, logo_info: Dict, channel: str, user: str):
        """Generate mockups for 2 products using default colors - Jersey Tee and College Hoodie only"""
        try:
            team_info = conversation.get("team_info", {})
            team_name = team_info.get("name", "your team")
            
            # Send initial message
            self._send_message(channel, f"🎨 Perfect! Creating your team merchandise for {team_name}...")
            
            # Get AI-recommended default colors for each product based on the logo
            logo_url = logo_info.get("url", "No logo URL available")
            ai_default_colors = self._get_ai_default_colors_for_products(logo_url)
            
            # Fallback colors if AI fails
            fallback_variants = {
                '12': 'Black',   # Unisex Jersey Short Sleeve Tee - Black is most popular
                '92': 'Navy'     # Unisex College Hoodie - Navy is classic
            }
            
            # Use AI colors or fallback
            default_variants = ai_default_colors if ai_default_colors else fallback_variants
            
            # Products in order: Jersey Tee, College Hoodie only
            products_order = [
                ("12", "Unisex Jersey Short Sleeve Tee"),  # Jersey Short Sleeve Tee
                ("92", "Unisex College Hoodie")   # College Hoodie
            ]
            
            for i, (product_id, product_name) in enumerate(products_order):
                if product_id not in default_variants:
                    logger.warning(f"No default variant for product {product_id}, skipping")
                    continue
                    
                # Add delay between products to avoid rate limiting (except for first product)
                if i > 0:
                    import time
                    # Standard delay between products
                    delay = 2
                    time.sleep(delay)
                    logger.info(f"Added {delay}-second delay before creating {product_name}")
                    
                try:
                    # For College Hoodie, use first variant to avoid validation issues
                    if product_id == "92":  # College Hoodie
                        logger.info(f"Using first available variant for {product_name} to avoid validation issues")
                        product_details = product_service.get_product_by_id(product_id)
                        if product_details and product_details.get('variants'):
                            selected_variant = product_details['variants'][0]
                        else:
                            selected_variant = None
                    else:
                        # For other products, try to find the default color first
                        default_color = default_variants[product_id]
                        selected_variant = product_service._find_variant_by_color(product_id, default_color)
                        
                        if not selected_variant:
                            logger.warning(f"Could not find variant for {product_name} in {default_color}, using first available")
                            # Fallback to first variant
                            product_details = product_service.get_product_by_id(product_id)
                            if product_details and product_details.get('variants'):
                                selected_variant = product_details['variants'][0]
                    
                    if selected_variant:
                        # Create mockup for this product with default variant
                        product_info = {"id": product_id, "formatted": {"title": product_name}}
                        
                        response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                        
                        if response.get("image_url") and response.get("purchase_url"):
                            # Send this mockup immediately with color info and alternatives
                            color = selected_variant.get('options', {}).get('color', 'Default')
                            product_title_with_color = f"{response['product_title']} ({color})"
                            
                            # Get available color alternatives for description
                            colors_by_product = product_service.get_available_colors_for_best_products()
                            available_colors = colors_by_product.get(product_id, [])
                            
                            # Send product with color alternatives info
                            self._send_product_result_with_alternatives(channel, response["image_url"], response["purchase_url"], product_title_with_color, available_colors, response.get("publish_method"), logo_info.get("url"))
                            
                            # Simple progress message (only for jersey tee -> hoodie)
                            if product_id == "12":  # Jersey Tee, next is hoodie
                                self._send_message(channel, f"⚡ Creating hoodie...")
                    
                except Exception as e:
                    logger.error(f"Error creating default mockup for {product_name}: {e}")
                    # Check if it's a rate limit issue
                    if "rate" in str(e).lower() or "429" in str(e) or "too many" in str(e).lower():
                        self._send_message(channel, f"⏱️ API rate limit hit - retrying {product_name} in a moment...")
                        import time
                        time.sleep(5)  # Longer delay for rate limit recovery
                        # Retry once
                        try:
                            default_color = default_variants[product_id]
                            selected_variant = product_service._find_variant_by_color(product_id, default_color)
                            if selected_variant:
                                response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                                if response.get("image_url") and response.get("purchase_url"):
                                    color = selected_variant.get('options', {}).get('color', 'Default')
                                    product_title_with_color = f"{response['product_title']} ({color})"
                                    colors_by_product = product_service.get_available_colors_for_best_products()
                                    available_colors = colors_by_product.get(product_id, [])
                                    self._send_product_result_with_alternatives(channel, response["image_url"], response["purchase_url"], product_title_with_color, available_colors, response.get("publish_method"), logo_info.get("url"))
                                else:
                                    self._send_message(channel, f"⚠️ {product_name} creation failed after retry - try a different logo later")
                        except Exception as retry_e:
                            logger.error(f"Retry failed for {product_name}: {retry_e}")
                            self._send_message(channel, f"⚠️ {product_name} temporarily unavailable - try a different logo later")
                    else:
                        self._send_message(channel, f"Had trouble with the {product_name}, but continuing with other products...")
            
            # Final message with color change guidance
            self._send_message(channel, "🎉 *All done!* Click any link above to order. Want different colors? Just say something like 'red t-shirt' or 'black hoodie' to create new drops!")
            
            # Update conversation state
            conversation_manager.update_conversation(channel, user, {"state": "completed"})
            
        except Exception as e:
            logger.error(f"Error in _generate_all_mockups_with_default_colors: {e}")
            self._send_message(channel, "Sorry, had some issues creating the mockups. Please try uploading your logo again!")
    
    def _generate_specific_color_mockups(self, conversation: Dict, logo_info: Dict, selected_variants: Dict, channel: str, user: str):
        """Generate mockups for specific color requests - used when user wants color changes"""
        try:
            team_info = conversation.get("team_info", {})
            
            # Product name mapping for display
            product_names = {
                '12': 'Unisex Jersey Short Sleeve Tee',
                '6': 'Unisex Heavy Cotton Tee',
                '145': 'Unisex Softstyle T-Shirt',
                '92': 'Unisex College Hoodie',
                '1525': 'Unisex Midweight Softstyle Fleece Hoodie',
                '499': 'Unisex Supply Hoodie',
                '1447': 'Classic Dad Cap',
                '1583': 'Surf Cap'
            }
            
            # Create mockups for each requested color variant
            for variant_info in selected_variants:
                product_id = variant_info.get('product_id')
                selected_variant = variant_info.get('variant')
                if product_id not in product_names:
                    continue
                    
                try:
                    product_name = product_names[product_id]
                    product_info = {"id": product_id, "formatted": {"title": product_name}}
                    
                    response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                    
                    if response.get("image_url") and response.get("purchase_url"):
                        # Send this mockup immediately with color info
                        color = variant_info.get('color', 'Unknown')
                        product_title_with_color = f"{response['product_title']} ({color})"
                        
                        # Get available color alternatives for description
                        colors_by_product = product_service.get_available_colors_for_best_products()
                        available_colors = colors_by_product.get(product_id, [])
                        
                        # Send product with color alternatives info
                        self._send_product_result_with_alternatives(channel, response["image_url"], response["purchase_url"], product_title_with_color, available_colors, response.get("publish_method"), logo_info.get("url"))
                    else:
                        color = variant_info.get('color', 'Unknown')
                        self._send_message(channel, f"Sorry, had trouble creating the {product_name} in {color}. Please try again!")
                        
                except Exception as e:
                    logger.error(f"Error creating specific color mockup for {product_id}: {e}")
                    # Check if it's a rate limit issue
                    if "rate" in str(e).lower() or "429" in str(e) or "too many" in str(e).lower():
                        self._send_message(channel, f"⏱️ API rate limit hit - please try again in a moment")
                    else:
                        self._send_message(channel, f"Had trouble creating that color variant, but continuing...")
            
            # Final message
            num_created = len(selected_variants)
            if num_created > 0:
                self._send_message(channel, f"🎉 *Done!* Created {num_created} new {'drop' if num_created == 1 else 'drops'} with your color preferences! Want more colors? Just ask!")
            else:
                self._send_message(channel, "Sorry, I couldn't create any drops with those color preferences. Try something like 'red t-shirt' or 'black hoodie'!")
            
        except Exception as e:
            logger.error(f"Error in _generate_specific_color_mockups: {e}")
            self._send_message(channel, "Sorry, had some issues creating the color variants. Please try again!")
    
    def _create_single_mockup(self, conversation: Dict, logo_info: Dict, product_info: Dict, channel: str, user: str) -> Dict:
        """Create a single product mockup (extracted from _create_custom_product_with_stored_logo)"""
        try:
            team_info = conversation.get("team_info", {})
            
            # Get product blueprint details
            product_details = product_service.get_product_by_id(str(product_info['id']))
            
            if not product_details:
                return {"message": "Product not found"}
            
            # Convert to expected format
            selected_product = {
                'id': product_info['id'],
                'title': product_details.get('title', 'Custom Product'),
                'blueprint_id': product_details.get('blueprint_id'),
                'print_provider_id': product_details.get('print_provider_id') or product_details.get('primary_print_provider_id'),
                'variants': product_details.get('variants', []),
                'type': product_details.get('category', 'apparel'),
                'base_price': product_details.get('base_price', 20.00)
            }
            
            # Get first available variant for mockup
            variants = selected_product.get('variants', [])
            if not variants:
                return {"message": "No variants available"}
            
            first_variant = variants[0]
            
            # Create product design for mockup
            design_result = printify_service.create_product_design(
                blueprint_id=selected_product['blueprint_id'],
                print_provider_id=selected_product['print_provider_id'],
                variant_id=first_variant['id'],
                image_id=logo_info["printify_image_id"],
                product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}",
                database_service=database_service
            )
            
            if not design_result["success"]:
                return {"message": f"Design creation failed: {design_result['error']}"}
            
            
            # Save design to database
            design_data = {
                "name": f"{team_info.get('name', 'Team')} {selected_product['title']}",
                "description": f"Custom {selected_product['title']} with team logo",
                "blueprint_id": selected_product['blueprint_id'],
                "print_provider_id": selected_product['print_provider_id'],
                "printify_product_id": design_result.get("product_id"),
                "team_logo_image_id": logo_info["printify_image_id"],
                "mockup_image_url": design_result.get("mockup_url"),
                "base_price": selected_product.get('base_price', 20.00),
                "markup_percentage": 50.0,
                "created_by": f"{channel}_{user}",
                "team_info": team_info,
                "product_type": selected_product.get('type', 'apparel')
            }
            
            design_id = database_service.save_product_design(design_data)
            drop_url = database_service.generate_drop_url(design_id)
            
            return {
                "image_url": design_result.get("mockup_url"),
                "purchase_url": drop_url,
                "product_title": design_data["name"]
            }
            
        except Exception as e:
            logger.error(f"Error creating single mockup: {e}")
            return {"message": "Mockup creation failed"}
    
    def _create_single_mockup_with_variant(self, conversation: Dict, logo_info: Dict, product_info: Dict, selected_variant: Dict, channel: str, user: str) -> Dict:
        """Create a single product mockup using the selected variant"""
        try:
            team_info = conversation.get("team_info", {})
            
            # Get product blueprint details
            product_details = product_service.get_product_by_id(str(product_info['id']))
            
            if not product_details:
                return {"message": "Product not found"}
            
            # Convert to expected format
            selected_product = {
                'id': product_info['id'],
                'title': product_details.get('title', 'Custom Product'),
                'blueprint_id': product_details.get('blueprint_id'),
                'print_provider_id': product_details.get('print_provider_id') or product_details.get('primary_print_provider_id'),
                'variants': product_details.get('variants', []),
                'type': product_details.get('category', 'apparel'),
                'base_price': product_details.get('base_price', 20.00)
            }
            
            # Use the selected variant instead of first available
            if not selected_variant:
                return {"message": "No variant selected"}
            
            # Check if we already have a master product for this logo/blueprint combination
            existing_design = database_service.find_existing_product_design(
                selected_product['blueprint_id'], 
                selected_product['print_provider_id'], 
                logo_info["printify_image_id"]
            )
            
            if existing_design and existing_design.get("printify_product_id"):
                # Check if this is an old single-variant product by testing variant availability
                product_id = existing_design["printify_product_id"]
                logger.info(f"Found existing product {product_id}, checking if it supports variant {selected_variant['id']}")
                
                # Test if this product can provide the requested variant mockup
                mockup_result = printify_service.get_variant_mockup(product_id, selected_variant['id'])
                
                if mockup_result.get("mockup_url"):
                    # Product supports this variant - use it
                    logger.info(f"Using existing master product {product_id} for variant {selected_variant['id']}")
                    design_result = {
                        "success": True,
                        "mockup_url": mockup_result.get("mockup_url"),
                        "product_id": product_id,
                        "product_title": f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}",
                        "blueprint_id": selected_product['blueprint_id'],
                        "print_provider_id": selected_product['print_provider_id'],
                        "variant_id": selected_variant['id'],
                        "image_id": logo_info["printify_image_id"],
                        "reused_existing": True
                    }
                else:
                    # Old single-variant product - create new master product
                    logger.info(f"Existing product {product_id} doesn't support variant {selected_variant['id']}, forcing creation of new master product")
                    design_result = printify_service.create_product_design(
                        blueprint_id=selected_product['blueprint_id'],
                        print_provider_id=selected_product['print_provider_id'],
                        variant_id=selected_variant['id'],
                        image_id=logo_info["printify_image_id"],
                        product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}",
                        database_service=database_service,
                        force_new_product=True  # FORCE new product - don't reuse old one
                    )
            else:
                # Create new master product with all variants
                design_result = printify_service.create_product_design(
                    blueprint_id=selected_product['blueprint_id'],
                    print_provider_id=selected_product['print_provider_id'],
                    variant_id=selected_variant['id'],
                    image_id=logo_info["printify_image_id"],
                    product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}",
                    database_service=database_service,
                    force_new_product=False
                )
            
            if not design_result["success"]:
                return {"message": f"Design creation failed: {design_result['error']}"}
            
            # Save design to database with variant information
            variant_color = selected_variant.get('options', {}).get('color', 'Unknown')
            design_data = {
                "name": f"{team_info.get('name', 'Team')} {selected_product['title']}",
                "description": f"Custom {selected_product['title']} with team logo in {variant_color}",
                "blueprint_id": selected_product['blueprint_id'],
                "print_provider_id": selected_product['print_provider_id'],
                "printify_product_id": design_result.get("product_id"),
                "team_logo_image_id": logo_info["printify_image_id"],
                "mockup_image_url": design_result.get("mockup_url"),
                "base_price": selected_product.get('base_price', 20.00),
                "markup_percentage": 50.0,
                "created_by": f"{channel}_{user}",
                "team_info": team_info,
                "product_type": selected_product.get('type', 'apparel'),
                "default_variant_id": selected_variant['id'],  # Store the selected variant
                "default_color": variant_color
            }
            
            design_id = database_service.save_product_design(design_data)
            drop_url = database_service.generate_drop_url(design_id)
            
            return {
                "image_url": design_result.get("mockup_url"),
                "purchase_url": drop_url,
                "product_title": design_data["name"]
            }
            
        except Exception as e:
            logger.error(f"Error creating single mockup with variant: {e}")
            return {"message": "Mockup creation failed"}

    def _create_custom_product_with_stored_logo(self, conversation: Dict, logo_info: Dict, channel: str, user: str) -> Dict:
        """Create custom product design and save to database for drop"""
        try:
            product_info = conversation["product_selected"]
            team_info = conversation.get("team_info", {})
            
            # Get product blueprint details from product service
            product_details = product_service.get_product_by_id(str(product_info['id']))
            
            if not product_details:
                error_msg = "Selected product not found in catalog"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": "Sorry, there was an issue finding the selected product. Please try again!"}
            
            # Convert to the format expected by create_product_design
            selected_product = {
                'id': product_info['id'],
                'title': product_details.get('title', 'Custom Product'),
                'blueprint_id': product_details.get('blueprint_id'),
                'print_provider_id': product_details.get('print_provider_id') or product_details.get('primary_print_provider_id'),
                'variants': product_details.get('variants', []),
                'type': product_details.get('category', 'apparel'),
                'base_price': product_details.get('base_price', 20.00)
            }
            
            # Get first available variant for mockup
            variants = selected_product.get('variants', [])
            if not variants:
                error_msg = "No variants available for selected product"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": "Sorry, this product doesn't have any available options. Please choose a different product!"}
            
            first_variant = variants[0]
            
            # Create product design for mockup
            logger.info(f"Creating product design for {channel}_{user} with stored logo")
            design_result = printify_service.create_product_design(
                blueprint_id=selected_product['blueprint_id'],
                print_provider_id=selected_product['print_provider_id'],
                variant_id=first_variant['id'],
                image_id=logo_info["printify_image_id"],
                product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}",
                database_service=database_service
            )
            
            if not design_result["success"]:
                error_msg = f"Design creation failed: {design_result['error']}"
                conversation_manager.record_error(channel, user, error_msg)
                return {"message": f"Sorry, there was an issue creating your design: {design_result['error']}"}
            
            # Save design to database
            design_data = {
                "name": f"{team_info.get('name', 'Team')} {selected_product['title']}",
                "description": f"Custom {selected_product['title']} with team logo",
                "blueprint_id": selected_product['blueprint_id'],
                "print_provider_id": selected_product['print_provider_id'],
                "printify_product_id": design_result.get("product_id"),
                "team_logo_image_id": logo_info["printify_image_id"],
                "mockup_image_url": design_result.get("mockup_url"),
                "base_price": selected_product.get('base_price', 20.00),
                "markup_percentage": 50.0,
                "created_by": f"{channel}_{user}",
                "team_info": team_info,
                "product_type": selected_product.get('type', 'apparel')
            }
            
            design_id = database_service.save_product_design(design_data)
            
            # Generate storefront URL
            drop_url = database_service.generate_drop_url(design_id)
            
            # Success! Format response
            logger.info(f"Successfully created design {design_id} for {channel}_{user}")
            
            team_name = team_info.get("name", "your team")
            success_message = f"🎉 Awesome! I've created a custom {selected_product['title']} design for {team_name}!\n\n"
            success_message += "Your design drop is ready for purchase! 👇"
            
            return {
                "message": success_message,
                "image_url": design_result.get("mockup_url"),
                "purchase_url": drop_url,
                "product_title": design_data["name"]
            }
            
        except Exception as e:
            logger.error(f"Error creating custom product design: {e}")
            conversation_manager.record_error(channel, user, f"Design creation exception: {str(e)}")
            return {"message": "Sorry, there was an unexpected error creating your design. Please try again or type 'restart' to begin fresh!"}
    
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
    
    def _send_product_result(self, channel: str, image_url: str, purchase_url: str, product_name: str, publish_method: str = None):
        """Send product creation result with drop link for purchase"""
        try:
            # Log the image URL for debugging
            logger.info(f"Sending product result with image URL: {image_url}")
            
            # Simple, clean messaging for the new flow (using proper Slack formatting)
            if "Tee" in product_name:
                # Add color info for the first product to guide users
                success_message = f"""🎉 *{product_name}*

🛒 <{purchase_url}|*Shop this design*>

_Available in 30+ colors including Black, White, Navy, Red, Royal Blue, and more!_"""
            else:
                # Simpler for subsequent products
                success_message = f"""🎉 *{product_name}*

🛒 <{purchase_url}|*Shop this design*>"""

            # Send the image with the message
            self.client.chat_postMessage(
                channel=channel,
                text=success_message,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": success_message
                        }
                    },
                    {
                        "type": "image",
                        "image_url": image_url,
                        "alt_text": f"Preview of {product_name}"
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error sending product result with image: {e}")
            # Fallback message without image (common for hat mockups that aren't ready yet)
            if "Cap" in product_name or "Hat" in product_name:
                fallback_msg = f"🎉 *{product_name}*\n\n🛒 <{purchase_url}|*Shop this design*>\n\n_Mockup image is generating and will appear on the product page shortly!_"
            else:
                fallback_msg = f"🎉 *{product_name}*\n\n🛒 <{purchase_url}|*Shop this design*>"
                
            self.client.chat_postMessage(
                channel=channel,
                text=fallback_msg
            )
    
    def _send_product_result_with_alternatives(self, channel: str, image_url: str, purchase_url: str, product_name: str, available_colors: List, publish_method: str = None, logo_url: str = None):
        """Send product result with color alternatives information"""
        try:
            # Format available colors for display (limit to avoid message being too long)
            if available_colors:
                # Get AI-recommended colors based on logo or fallback to standard recommendation
                if logo_url:
                    recommended_colors = self._get_logo_inspired_colors(available_colors, product_name, logo_url)
                else:
                    recommended_colors = self._get_recommended_colors(available_colors)
                display_colors = recommended_colors[:6]  # Limit to 6 for readability
                color_text = ", ".join(display_colors)
                if len(available_colors) > 6:
                    color_text += f" (+{len(available_colors) - 6} more)"
                
                # Extract the actual product type from the product name
                product_type = "item"  # default fallback
                if "Tee" in product_name or "Heavy Cotton" in product_name:
                    product_type = "t-shirt"
                elif "Sweatshirt" in product_name or "Hoodie" in product_name:
                    product_type = "hoodie"
                elif "Hat" in product_name or "Cap" in product_name:
                    product_type = "hat"
                
                alternatives_text = f"\n\n_💡 Also available in: {color_text}_\n_Want a different color? Just say '{available_colors[1].lower()} {product_type}' to create a new drop!_"
            else:
                alternatives_text = ""
            
            # Create message with color alternatives info
            success_message = f"""🎉 *{product_name}*

🛒 <{purchase_url}|*Shop this design*>{alternatives_text}"""

            # Send the image with the message
            try:
                # Log the image URL for debugging
                logger.info(f"Attempting to send product with image URL: {image_url}")
                
                self.client.chat_postMessage(
                    channel=channel,
                    text=success_message,
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": success_message
                            }
                        },
                        {
                            "type": "image",
                            "image_url": image_url,
                            "alt_text": f"Preview of {product_name}"
                        }
                    ]
                )
            except SlackApiError as slack_error:
                # Check if it's specifically an image download error
                error_data = slack_error.response.get('error', '')
                if 'downloading image failed' in str(slack_error) or 'invalid_blocks' in error_data:
                    logger.warning(f"Slack couldn't download image from {image_url}, sending without image")
                    # Send without the image block
                    self.client.chat_postMessage(
                        channel=channel,
                        text=success_message,
                        blocks=[
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn",
                                    "text": success_message + "\n\n_🖼️ Product mockup is being generated and will appear on the product page!_"
                                }
                            }
                        ]
                    )
                else:
                    # Re-raise if it's a different error
                    raise
            except Exception as img_error:
                # If image fails, send without the image block
                logger.warning(f"Failed to send with image, sending text only: {img_error}")
                self.client.chat_postMessage(
                    channel=channel,
                    text=success_message,
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": success_message + "\n\n_🖼️ Product mockup is being generated and will appear on the product page!_"
                            }
                        }
                    ]
                )
            
        except Exception as e:
            logger.error(f"Error sending product result with alternatives: {e}")
            # Final fallback - simple message
            try:
                self.client.chat_postMessage(
                    channel=channel,
                    text=f"🎉 *{product_name}*\n\n🛒 <{purchase_url}|*Shop this design*>"
                )
            except Exception as final_error:
                logger.error(f"Final fallback message failed: {final_error}")
    
    def _get_ai_default_colors_for_products(self, logo_url: str) -> Dict[str, str]:
        """Get AI-recommended default colors for each of the main products based on logo"""
        try:
            products_to_analyze = {
                '12': 'Unisex Jersey Short Sleeve Tee',
                '92': 'Unisex College Hoodie'
            }
            
            ai_defaults = {}
            colors_by_product = product_service.get_available_colors_for_best_products()
            
            for product_id, product_name in products_to_analyze.items():
                available_colors = colors_by_product.get(product_id, [])
                if not available_colors:
                    continue
                    
                # Get AI recommendation for best default color for this product
                ai_result = openai_service.get_logo_inspired_colors(logo_url, available_colors, product_name)
                top_colors = ai_result.get('top_6_colors', [])
                
                # Use the first AI-recommended color as the default
                if top_colors and top_colors[0] in available_colors:
                    ai_defaults[product_id] = top_colors[0]
                    logger.info(f"AI selected '{top_colors[0]}' as default for {product_name}")
            
            return ai_defaults if ai_defaults else None
            
        except Exception as e:
            logger.error(f"AI default color selection failed: {e}")
            return None

    def _get_logo_inspired_colors(self, available_colors: List[str], product_name: str, logo_url: str) -> List[str]:
        """Get AI-recommended colors based on logo analysis"""
        try:
            ai_result = openai_service.get_logo_inspired_colors(logo_url, available_colors, product_name)
            recommended_colors = ai_result.get('top_6_colors', [])
            
            # Validate that recommended colors are actually available
            valid_colors = []
            for color in recommended_colors:
                if color in available_colors:
                    valid_colors.append(color)
            
            # If we don't have enough valid colors, fill with fallback
            if len(valid_colors) < 6:
                fallback_colors = self._get_recommended_colors(available_colors)
                for color in fallback_colors:
                    if color not in valid_colors and len(valid_colors) < 6:
                        valid_colors.append(color)
            
            logger.info(f"AI-selected colors for {product_name}: {valid_colors[:6]}")
            return valid_colors[:6]
            
        except Exception as e:
            logger.error(f"AI color recommendation failed: {e}")
            return self._get_recommended_colors(available_colors)

    def _get_recommended_colors(self, available_colors: List[str]) -> List[str]:
        """Get recommended colors prioritizing team essentials and primary colors"""
        # Priority order for team colors
        priority_colors = [
            'Black', 'White', 'Navy', 'Royal Blue', 'Red', 'Cardinal', 
            'Athletic Heather', 'Sport Grey', 'Forest Green', 'Purple',
            'Maroon', 'Orange', 'Yellow', 'Pink', 'Brown'
        ]
        
        recommended = []
        available_lower = [color.lower() for color in available_colors]
        
        # First, add priority colors that are available
        for priority in priority_colors:
            for i, color_lower in enumerate(available_lower):
                if priority.lower() in color_lower:
                    recommended.append(available_colors[i])
                    break
            if len(recommended) >= 6:
                break
        
        # If we don't have 6 yet, add other available colors
        if len(recommended) < 6:
            for color in available_colors:
                if color not in recommended:
                    recommended.append(color)
                    if len(recommended) >= 6:
                        break
        
        return recommended
    
    def _is_asking_for_options(self, text: str) -> bool:
        """Check if user is asking for information rather than making a product"""
        text_lower = text.lower()
        
        # Question patterns that indicate the user wants information
        question_patterns = [
            'what', 'which', 'how many', 'list', 'show me', 'tell me',
            'are there', 'do you have', 'options', 'available',
            'other', 'different', 'more', 'all of the', 'any other'
        ]
        
        # Check for question words
        return any(pattern in text_lower for pattern in question_patterns)
    
    def _handle_options_query(self, text: str, conversation: Dict) -> Dict:
        """Handle user questions about available options - but proactively create examples using AI"""
        # Use AI to understand what the user is asking for
        try:
            logo_info = conversation.get("logo_info")
            
            # Use AI to analyze what color family/type the user is asking about
            if logo_info and logo_info.get("printify_image_id"):
                # Get all available colors for context
                jersey_colors = product_service.get_colors_for_product('12')
                hoodie_colors = product_service.get_colors_for_product('92')
                
                # Get recent conversation context for better understanding
                recent_creation = conversation.get("recent_creation", {})
                recent_discussion = conversation.get("recent_discussion", "")
                context_info = ""
                
                if recent_creation:
                    context_info = f"""
                RECENT CONTEXT: Just created a {recent_creation.get('product', '')} in {recent_creation.get('color', '')} color.
                Color family discussed: {recent_creation.get('color_family', '')}
                All matching colors from that family: {', '.join(recent_creation.get('all_matching_colors', []))}
                """
                
                if recent_discussion:
                    context_info += f"\nRecent discussion: {recent_discussion}"
                
                # Create AI prompt to understand the color query and suggest examples
                color_analysis_prompt = f"""
                A user is asking about colors for custom team merchandise: "{text}"
                
                {context_info}
                
                Available colors for Jersey Tee: {', '.join(jersey_colors)}
                Available colors for Hoodie: {', '.join(hoodie_colors)}
                
                Please analyze their query and respond with a JSON object:
                {{
                    "is_color_query": true/false,
                    "color_family_requested": "description of what colors they want (e.g., 'light blue colors', 'purple options', 'green shades')",
                    "matching_colors": ["list", "of", "matching", "color", "names"],
                    "best_example_color": "single best color to create as example",
                    "suggested_product": "shirt" or "hoodie",
                    "proactive_message": "friendly message explaining the colors and what example you'll create"
                }}
                
                Guidelines:
                - Use RECENT CONTEXT to understand pronouns like "that color", "same color", "this shade"
                - If asking about light blue, blue tones, or sky colors - find blue-family colors
                - If asking about purple, violet - find purple-family colors  
                - If asking about orange, burnt orange - find orange-family colors
                - If asking about green, forest, kelly - find green-family colors
                - If they reference "that color" and recent context shows a specific color, use that color family
                - When they ask for a different product in "that color", find the exact color if available
                - Choose the most appealing color as the example (avoid basic "Black" unless specifically requested)
                - Default to creating a t-shirt unless they mention hoodie
                - Be enthusiastic and explain what you're doing
                """
                
                # Get AI analysis
                try:
                    response = openai_service.client.chat.completions.create(
                        model="gpt-4-turbo-preview",
                        messages=[
                            {"role": "system", "content": color_analysis_prompt},
                            {"role": "user", "content": text}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )
                    
                    import json
                    ai_analysis = json.loads(response.choices[0].message.content)
                    
                    if ai_analysis.get("is_color_query") and ai_analysis.get("matching_colors") and ai_analysis.get("best_example_color"):
                        detected_colors = ai_analysis["matching_colors"]
                        example_color = ai_analysis["best_example_color"]
                        proactive_message = ai_analysis.get("proactive_message", f"Here are the colors available: {', '.join(detected_colors)}. Let me create a {example_color} example!")
                        
                        # Send immediate response about creating example
                        self._send_message(conversation.get('channel', ''), proactive_message)
                        
                        # Create the example product
                        product_id = "12"  # Jersey Tee (default)
                        if ai_analysis.get("suggested_product") == "hoodie":
                            product_id = "92"
                        
                        selected_variant = product_service._find_variant_by_color(product_id, example_color)
                        if selected_variant:
                            product_title = "Unisex Jersey Short Sleeve Tee" if product_id == "12" else "Unisex College Hoodie"
                            product_info = {"id": product_id, "formatted": {"title": product_title}}
                            
                            # Get conversation details for the creation
                            channel = conversation.get('channel', '')
                            user = conversation.get('user', '')
                            
                            # Create the mockup
                            response = self._create_single_mockup_with_variant(conversation, logo_info, product_info, selected_variant, channel, user)
                            
                            if response and response.get("image_url") and response.get("purchase_url"):
                                # Send the product with alternatives
                                other_colors = [c for c in detected_colors if c != example_color]
                                
                                self._send_product_result_with_alternatives(
                                    channel, 
                                    response["image_url"], 
                                    response["purchase_url"], 
                                    f"Team {response['product_title']} ({example_color})",
                                    other_colors,
                                    "product_created",
                                    logo_info.get("url")
                                )
                                
                                # Store recent product creation context for follow-up questions
                                recent_creation = {
                                    "color": example_color,
                                    "product": product_title,
                                    "color_family": ai_analysis.get("color_family_requested", ""),
                                    "all_matching_colors": detected_colors
                                }
                                conversation_manager.update_conversation(channel, user, {"recent_creation": recent_creation})
                                
                                return {"status": "created_example", "color": example_color, "alternatives": other_colors}
                
                except Exception as e:
                    logger.error(f"AI color analysis failed: {e}")
                    # Fall through to regular response
            
            # Fallback to regular informational response if no proactive creation
            # Get available products and colors for AI context
            all_products = product_service.get_all_products()
            
            # Get colors for both products
            jersey_colors = product_service.get_colors_for_product('12')
            hoodie_colors = product_service.get_colors_for_product('92')
            
            # Create system prompt for AI to understand the query
            system_prompt = f"""You are helping a user explore available options for custom team merchandise.
            
            Available products:
            - Unisex Jersey Short Sleeve Tee (ID: 12) - available in {len(jersey_colors)} colors
            - Unisex College Hoodie (ID: 92) - available in {len(hoodie_colors)} colors
            
            Available colors for Jersey Tee: {', '.join(jersey_colors[:20])}{'...' if len(jersey_colors) > 20 else ''}
            Available colors for College Hoodie: {', '.join(hoodie_colors[:20])}{'...' if len(hoodie_colors) > 20 else ''}
            
            The user is asking: "{text}"
            
            Analyze their question and respond appropriately:
            1. If asking about specific colors (like purple, orange, blue), list those specific colors
            2. If asking about products, explain the available products
            3. If asking generally about options, give helpful overview
            4. Always end with clear instructions on how to create a product
            
            Be conversational and helpful. Use emojis appropriately.
            
            Please respond with a JSON object in this format:
            {{
                "response_type": "color_list|product_list|general_help",
                "message": "your helpful response here"
            }}"""
            
            # Get AI response
            response = openai_service.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get('message', 'I can help you explore our color and product options! What would you like to know?')
            
        except Exception as e:
            logger.error(f"AI options query failed: {e}")
            # Fallback response
            return "I can help you with colors and products! Try asking 'what purple colors do you have?' or 'show me the available products'"
    

# Global instance
slack_bot = SlackBot() 