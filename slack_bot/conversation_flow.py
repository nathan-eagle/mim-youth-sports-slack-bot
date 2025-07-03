"""
Conversation flow logic for different states
"""
import logging
from typing import Dict, List
from conversation_manager import conversation_manager
from services.product_service import product_service
from services.product_selector import product_selector
from openai_service import openai_service
from .mockup_generator import MockupGenerator
from .utils import is_asking_for_options, extract_requested_color

logger = logging.getLogger(__name__)


class ConversationFlow:
    """Manages conversation flow through different states"""
    
    def __init__(self, bot):
        self.bot = bot
        self.mockup_generator = MockupGenerator(bot)
    
    def handle_initial_message(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle the initial message from a user"""
        logger.info(f"Handling initial message: {text}")
        
        # Check if they're mentioning products
        if any(keyword in text.lower() for keyword in ['shirt', 'hoodie', 'hat', 'jersey', 'uniform']):
            # They're already talking about products
            conversation_manager.update_conversation(channel, user, {'state': 'product_selection'})
            return self.handle_product_selection(text, conversation, channel, user)
        
        # Default welcome message
        self.bot.send_message(
            channel,
            "👋 Hi! I'm here to help you create custom products for your youth sports team!\n\n"
            "To get started, I'll need:\n"
            "1. Your team logo (drag and drop an image here)\n"
            "2. What type of products you'd like (t-shirts, hoodies, hats, etc.)\n\n"
            "You can start by uploading your logo or telling me what products you're interested in!"
        )
        
        conversation_manager.update_conversation(channel, user, {'state': 'product_selection'})
        return {"status": "success", "action": "initial_greeting"}
    
    def handle_product_selection(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle product selection state"""
        logger.info(f"Handling product selection: {text}")
        
        # Use AI-powered product selector
        selection_result = product_selector.select_products_from_conversation(text, conversation)
        
        if not selection_result['success']:
            # Show suggestions
            suggestions = selection_result.get('suggested_products', [])
            suggestion_text = ""
            if suggestions:
                suggestion_text = "\n\nPopular options include:\n" + "\n".join([
                    f"• *{p['title']}* ({p['category'].title()})" for p in suggestions[:3]
                ])
            
            self.bot.send_message(
                channel,
                f"I'm having trouble understanding your request. Could you tell me what type of products you'd like? "
                f"For example: 't-shirts', 'hoodies', 'hats', etc.{suggestion_text}"
            )
            return {"status": "ai_error"}
        
        requested_products = selection_result.get('categories', [])
        
        if not requested_products:
            # Couldn't understand products, ask for clarification
            self.bot.send_message(
                channel,
                "I want to make sure I understand correctly. What type of products are you looking for?\n\n"
                "Popular options include:\n"
                "• *T-shirts* - Great for team practice and games\n"
                "• *Hoodies* - Perfect for cooler weather\n"
                "• *Hats* - Popular with players and fans\n"
                "• *Tank tops* - Good for summer sports\n"
                "• *Long sleeve shirts* - Versatile option\n\n"
                "Just let me know what interests you!"
            )
            return {"status": "need_clarification"}
        
        # Get product alternatives and suggestions like color selection
        alternatives = selection_result.get('alternatives', {})
        complementary = product_selector.suggest_complementary_products(requested_products)
        
        # Update conversation with selected products
        conversation_manager.update_conversation(channel, user, {
            'selected_products': requested_products,
            'product_alternatives': alternatives,
            'complementary_products': complementary,
            'state': 'awaiting_logo' if not conversation.get('logo_url') else 'creating_mockups'
        })
        
        # Build message with alternatives like color selection
        product_message = f"Perfect! I'll create mockups for {', '.join(requested_products)}."
        
        # Add alternatives message
        alternatives_message = product_selector.format_product_suggestions_message(alternatives, complementary)
        if alternatives_message:
            product_message += f"\n\n{alternatives_message}"
        
        # Check if we have a logo
        if conversation.get('logo_url'):
            # We have a logo, create mockups
            self.bot.send_message(channel, product_message + "\n\nLet me generate those mockups for you...")
            
            # Create mockups
            logo_result = {
                'success': True,
                'url': conversation['logo_url'],
                'file_path': conversation.get('logo_file')
            }
            
            updated_conversation = conversation_manager.get_or_create_conversation(channel, user)
            return self.mockup_generator.create_custom_product(updated_conversation, logo_result, channel, user)
        else:
            # Need logo
            logo_message = f"Great choice! I'll help you create custom {', '.join(requested_products)}."
            
            if alternatives_message:
                logo_message += f"\n\n{alternatives_message}"
            
            logo_message += ("\n\nNow I just need your team logo. Please drag and drop your logo image into this chat, "
                           "or you can say 'use default logo' to use our sample logo.")
            
            self.bot.send_message(channel, logo_message)
            return {"status": "awaiting_logo"}
    
    def handle_logo_request(self, text: str, conversation: Dict, event: Dict, channel: str, user: str) -> Dict:
        """Handle state when waiting for logo"""
        logger.info(f"Handling logo request: {text}")
        
        # Check if they want to use default logo
        if 'default' in text.lower() or 'sample' in text.lower():
            default_logo_url = "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png/v1/fill/w_190,h_190,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/MiM%20Color%20Logo.png"
            
            conversation_manager.update_conversation(channel, user, {
                'logo_url': default_logo_url,
                'is_default_logo': True,
                'state': 'creating_mockups'
            })
            
            self.bot.send_message(
                channel,
                "Using our default MiM logo. Creating your mockups now..."
            )
            
            # Create mockups
            logo_result = {
                'success': True,
                'url': default_logo_url,
                'file_path': None
            }
            
            updated_conversation = conversation_manager.get_or_create_conversation(channel, user)
            return self.mockup_generator.create_custom_product(updated_conversation, logo_result, channel, user)
        
        # Otherwise remind them to upload
        self.bot.send_message(
            channel,
            "Please upload your team logo by dragging and dropping an image file into this chat. "
            "Or you can say 'use default logo' to proceed with our sample logo."
        )
        
        return {"status": "awaiting_logo"}
    
    def handle_completed_conversation(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle messages after conversation is completed"""
        logger.info(f"Handling completed conversation message: {text}")
        
        # Check for color change requests
        if any(word in text.lower() for word in ['color', 'colour', 'different', 'change']):
            return self.handle_color_change_request(text, conversation, channel, user)
        
        # Check if they want to start over
        if any(phrase in text.lower() for phrase in ['new', 'another', 'different product', 'start over']):
            return self.bot.message_handler.handle_restart(channel, user)
        
        # Default response
        self.bot.send_message(
            channel,
            "I've already created your custom products! You can:\n"
            "• Click the links above to view and purchase\n"
            "• Say 'different color' to see other color options\n"
            "• Say 'start over' to create new products\n"
            "• Upload a new logo to create products with a different design"
        )
        
        return {"status": "completed_reminder"}
    
    def handle_creating_mockups_interruption(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle messages while creating mockups"""
        logger.info(f"Message during mockup creation: {text}")
        
        self.bot.send_message(
            channel,
            "I'm currently creating your mockups. This should just take a moment... ⏳"
        )
        
        return {"status": "creating_mockups"}
    
    def handle_color_selection(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle color selection state"""
        logger.info(f"Handling color selection: {text}")
        
        # Extract requested color
        requested_color = extract_requested_color(text)
        
        if not requested_color:
            self.bot.send_message(
                channel,
                "Please specify a color for your products. For example: 'red', 'blue', 'black', etc."
            )
            return {"status": "need_color"}
        
        # Get available colors for the products
        selected_products = conversation.get('selected_products', [])
        all_colors = set()
        
        for product_type in selected_products:
            products = product_service.get_products_by_type(product_type)
            for product in products:
                all_colors.update(product.get('available_colors', []))
        
        # Find matching color
        matching_colors = [color for color in all_colors if requested_color.lower() in color.lower()]
        
        if not matching_colors:
            self.bot.send_message(
                channel,
                f"Sorry, '{requested_color}' isn't available. Available colors include:\n" +
                "\n".join([f"• {color}" for color in sorted(list(all_colors))[:10]]) +
                "\n\nPlease choose from the available colors."
            )
            return {"status": "color_not_available"}
        
        # Use first matching color
        selected_color = matching_colors[0]
        
        # Update conversation
        conversation_manager.update_conversation(channel, user, {
            'selected_color': selected_color,
            'state': 'creating_mockups'
        })
        
        self.bot.send_message(
            channel,
            f"Great! Creating mockups in {selected_color}..."
        )
        
        # Create mockups with selected color
        updated_conversation = conversation_manager.get_or_create_conversation(channel, user)
        logo_info = {
            'success': True,
            'url': updated_conversation['logo_url'],
            'file_path': updated_conversation.get('logo_file')
        }
        
        return self.mockup_generator.create_custom_product_with_color(
            updated_conversation, logo_info, selected_color, channel, user
        )
    
    def handle_color_change_request(self, text: str, conversation: Dict, channel: str, user: str) -> Dict:
        """Handle color change requests after completion"""
        requested_color = extract_requested_color(text)
        
        if requested_color:
            # Update state to color selection
            conversation_manager.update_conversation(channel, user, {
                'state': 'selecting_colors'
            })
            return self.handle_color_selection(text, conversation, channel, user)
        
        # Show color options
        colors_shown = conversation.get('colors_shown', [])
        self.bot.send_message(
            channel,
            "Here are some other color options:\n" +
            "\n".join([f"• {color}" for color in colors_shown[:10]]) +
            "\n\nJust tell me which color you'd like!"
        )
        
        conversation_manager.update_conversation(channel, user, {
            'state': 'selecting_colors'
        })
        
        return {"status": "showing_color_options"}