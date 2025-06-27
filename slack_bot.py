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
                # Send the new service description message
                service_msg = """Welcome to the team merchandise service! How can I assist you with customizing products for your child's sports team today?

Here are our recommended products for youth sports teams:
• Kids Heavy Cotton™ Tee (Shirt)
  Available colors: Ash, Azalea, Black, Cardinal Red, Carolina Blue, Charcoal, Daisy, Dark Chocolate (+30 more)
• Youth Heavy Blend Hooded Sweatshirt (Shirt)
  Available colors: Black, Cardinal Red, Carolina Blue, Charcoal, Dark Heather, Forest Green, Gold, Graphite Heather (+12 more)  
• Snapback Trucker Cap (Hat)
  Available colors: Black, Brown, Caramel, Charcoal, Cranberry, Dark Heather Grey, Evergreen, Heather Grey (+8 more)

🚀 **Quick Start**: Upload your team logo now and I'll create mockups of all 3 products instantly! You can then choose which ones to purchase. 📸"""
                self._send_message(channel, service_msg)
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
                
                # Update conversation with persistent logo
                conversation_manager.update_conversation(channel, user, {
                    "logo_info": logo_info
                })
                
                # Clean up temporary logo file
                logo_processor.cleanup_logo(logo_result["file_path"])
                
                # If product is already selected, create it immediately
                if conversation.get("product_selected"):
                    response = self._create_custom_product_with_stored_logo(conversation, logo_info, channel, user)
                    
                    # Send response with purchase link
                    if response.get("image_url") and response.get("purchase_url"):
                        self._send_product_result(channel, response["image_url"], response["purchase_url"], response["product_title"], response.get("publish_method"))
                    elif response.get("message"):
                        self._send_message(channel, response["message"])
                    
                    # Update conversation state to completed
                    conversation_manager.update_conversation(channel, user, {"state": "completed"})
                else:
                    # Generate all 3 mockups in series for instant selection
                    self._generate_all_mockups_in_series(conversation, logo_info, channel, user)
                
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
            
            # Always set to awaiting_logo state for new optimized flow
            updates["state"] = "awaiting_logo"
            conversation_manager.update_conversation(channel, user, updates)
            
            suggestion_message = product_service.get_product_suggestions_text()
            
            # Service description with immediate logo request
            service_description = """Welcome to the team merchandise service! How can I assist you with customizing products for your child's sports team today?

Here are our recommended products for youth sports teams:
• Kids Heavy Cotton™ Tee (Shirt)
  Available colors: Ash, Azalea, Black, Cardinal Red, Carolina Blue, Charcoal, Daisy, Dark Chocolate (+30 more)
• Youth Heavy Blend Hooded Sweatshirt (Shirt)
  Available colors: Black, Cardinal Red, Carolina Blue, Charcoal, Dark Heather, Forest Green, Gold, Graphite Heather (+12 more)  
• Snapback Trucker Cap (Hat)
  Available colors: Black, Brown, Caramel, Charcoal, Cranberry, Dark Heather Grey, Evergreen, Heather Grey (+8 more)

🚀 **Quick Start**: Upload your team logo now and I'll create mockups of all 3 products instantly! You can then choose which ones to purchase. 📸"""
            
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
                    
                    conversation_manager.update_conversation(channel, user, {"logo_info": logo_info})
                    
                    # Generate all 3 mockups in series using the new method
                    self._generate_all_mockups_in_series(conversation, logo_info, channel, user)
                    
                    # Clean up temporary file
                    logo_processor.cleanup_logo(logo_result["file_path"])
                    
                    return {"message": "Creating mockups..."}
            
            # Not a URL, remind about logo requirement (prefer URLs)
            return {"message": "Please provide your team logo! For best results, share a direct URL link to your logo image (like from Google Drive, Dropbox, or any image hosting site). You can also upload an image file if needed."}
            
        except Exception as e:
            logger.error(f"Error in _handle_logo_request: {e}")
            raise e
    
    def _handle_completed_conversation(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle messages after product has been completed using LLM intelligence"""
        try:
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
                
                Available products: shirt (Kids Heavy Cotton™ Tee), hoodie (Youth Heavy Blend Hooded Sweatshirt), hat (Snapback Trucker Cap)
                
                Respond as an enthusiastic youth sports merchandise assistant.
                """
                
                # Get LLM response for context-aware handling
                llm_response = openai_service.get_contextual_response(context_prompt, text)
                
                # Check if user wants a different product
                product_match = product_service.find_product_by_intent(text)
                if product_match and product_match.get('id'):
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
                    product_match = product_service.find_product_by_intent(text)
                    if product_match and product_match.get('id') and product_match.get('formatted'):
                        conversation_manager.update_conversation(channel, user, {
                            "product_selected": product_match,
                            "state": "awaiting_logo"
                        })
                        return {"message": f"Great! Let's create a {product_match['formatted']['title']} for your team. Please upload your logo or provide a URL."}
                    else:
                        suggestion_message = product_service.get_product_suggestions_text()
                        return {"message": f"What would you like to create next?\n\n{suggestion_message}"}
                
                # Default positive response
                return {"message": "I'm so glad you like it! 🎉 Is there anything else you'd like to create for your team? Just let me know what product you're interested in!"}
            
        except Exception as e:
            logger.error(f"Error in _handle_completed_conversation: {e}")
            raise e
    
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
                'print_provider_id': product_details.get('print_provider_id'),
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
                product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}"
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
            self._send_message(channel, f"🎨 Perfect! Creating custom mockups for {team_name}... Starting with the T-shirt!")
            
            # Get the 3 best products in order: T-shirt, Hoodie, Hat
            best_products = product_service.get_best_products()
            products_order = [
                ("157", "Kids Heavy Cotton™ Tee"),  # T-shirt first
                ("314", "Youth Heavy Blend Hooded Sweatshirt"),  # Hoodie second  
                ("1446", "Snapback Trucker Cap")  # Hat third
            ]
            
            for product_id, product_name in products_order:
                if product_id not in best_products:
                    continue
                    
                try:
                    # Create mockup for this product
                    product_info = {"id": product_id, "formatted": {"title": product_name}}
                    response = self._create_single_mockup(conversation, logo_info, product_info, channel, user)
                    
                    if response.get("image_url") and response.get("purchase_url"):
                        # Send this mockup immediately
                        self._send_product_result(channel, response["image_url"], response["purchase_url"], response["product_title"], response.get("publish_method"))
                        
                        # Add brief pause and next product message (except for last item)
                        if product_id != "1446":  # Not the last item
                            next_product = "hoodie" if product_id == "157" else "hat"
                            self._send_message(channel, f"⚡ Working on the {next_product} next...")
                    
                except Exception as e:
                    logger.error(f"Error creating mockup for {product_name}: {e}")
                    self._send_message(channel, f"Had trouble with the {product_name}, but continuing with other products...")
            
            # Final message
            self._send_message(channel, "🎉 All done! Click any purchase link above to customize sizes, colors, and quantities. Need a different design? Just upload a new logo!")
            
            # Update conversation state
            conversation_manager.update_conversation(channel, user, {"state": "completed"})
            
        except Exception as e:
            logger.error(f"Error in _generate_all_mockups_in_series: {e}")
            self._send_message(channel, "Sorry, had some issues creating the mockups. Please try uploading your logo again!")
    
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
                'print_provider_id': product_details.get('print_provider_id'),
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
                product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}"
            )
            
            if not design_result["success"]:
                return {"message": f"Design creation failed: {design_result['error']}"}
            
            # Save design to database
            design_data = {
                "name": f"{team_info.get('name', 'Team')} {selected_product['title']}",
                "description": f"Custom {selected_product['title']} with team logo",
                "blueprint_id": selected_product['blueprint_id'],
                "print_provider_id": selected_product['print_provider_id'],
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
                'print_provider_id': product_details.get('print_provider_id'),
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
                product_title=f"Custom {selected_product['title']} for {team_info.get('name', 'Team')}"
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
            # Create messaging for custom drop approach
            success_message = f"""🎉 *Custom {product_name} Created Successfully!*

✅ Your team logo has been applied to the product
✅ High-quality mockup generated and ready to view
✅ Product design saved and ready for purchase

🛒 **Purchase your team gear here:** {purchase_url}

Your custom design is ready! Click the link above to select sizes, quantities, and complete your order. We'll handle the rest! 🏆"""

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
            logger.error(f"Error sending product result: {e}")
            # Fallback message without image
            self.client.chat_postMessage(
                channel=channel,
                text=f"🎉 Custom {product_name} created! Purchase here: {purchase_url}"
            )

# Global instance
slack_bot = SlackBot() 