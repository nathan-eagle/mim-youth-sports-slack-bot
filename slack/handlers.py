"""
Message and file handlers for different conversation states
"""
import logging
from typing import Dict, Optional
from conversation_manager import conversation_manager
from logo_processor import logo_processor
from .conversation_flow import ConversationFlow
from .mockup_generator import MockupGenerator

logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles text messages based on conversation state"""
    
    def __init__(self, bot):
        self.bot = bot
        self.conversation_flow = ConversationFlow(bot)
        self.mockup_generator = MockupGenerator(bot)
    
    def handle_restart(self, channel: str, user: str) -> Dict:
        """Handle restart/reset command"""
        conversation_manager.reset_conversation(channel, user)
        
        # Automatically use default logo and create initial drops
        default_logo_url = "https://static.wixstatic.com/media/d072b4_a933c375e992435ea9f972afc685cff9~mv2.png/v1/fill/w_190,h_190,al_c,q_85,usm_0.66_1.00_0.01,enc_avif,quality_auto/MiM%20Color%20Logo.png"
        
        # Create new conversation with default logo
        conversation = conversation_manager.get_or_create_conversation(channel, user)
        conversation_manager.update_conversation(channel, user, {
            'state': 'product_selection',
            'selected_products': [],
            'logo_url': default_logo_url,
            'is_default_logo': True
        })
        
        self.bot.send_message(
            channel,
            "👋 Hi! I'm here to help you create custom products for your youth sports team!\n\n"
            "I'll use our default MiM logo for now. You can upload your own team logo anytime by dragging it into this chat.\n\n"
            "What type of product would you like to create? I recommend starting with:\n"
            "• *T-shirts* - Perfect for team practice and casual wear\n"
            "• *Hoodies* - Great for cooler weather and team unity\n"
            "• *Hats* - Popular for fans and players\n\n"
            "Just tell me what you're looking for, and I'll show you some options!"
        )
        
        return {"status": "success", "action": "restart_conversation"}
    
    def route_message(self, text: str, conversation: Dict, event: Dict, channel: str, user: str) -> Dict:
        """Route message to appropriate handler based on conversation state"""
        current_state = conversation.get('state', 'initial')
        
        # Route based on state
        if current_state == 'initial':
            return self.conversation_flow.handle_initial_message(text, conversation, channel, user)
        elif current_state == 'product_selection':
            return self.conversation_flow.handle_product_selection(text, conversation, channel, user)
        elif current_state == 'awaiting_logo':
            return self.conversation_flow.handle_logo_request(text, conversation, event, channel, user)
        elif current_state == 'completed':
            return self.conversation_flow.handle_completed_conversation(text, conversation, channel, user)
        elif current_state == 'creating_mockups':
            return self.conversation_flow.handle_creating_mockups_interruption(text, conversation, channel, user)
        elif current_state == 'selecting_colors':
            return self.conversation_flow.handle_color_selection(text, conversation, channel, user)
        else:
            logger.warning(f"Unknown conversation state: {current_state}")
            return {"status": "unknown_state"}


class FileHandler:
    """Handles file upload events (logo uploads)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.mockup_generator = MockupGenerator(bot)
    
    def handle_file_upload(self, event: Dict, conversation: Dict, channel: str, user: str) -> Dict:
        """Process uploaded file as logo"""
        try:
            files = event.get('files', [])
            if not files:
                return {"status": "no_files"}
            
            file_info = files[0]  # Take first file
            file_type = file_info.get('mimetype', '')
            
            # Check if it's an image
            if not file_type.startswith('image/'):
                self.bot.send_message(
                    channel,
                    "Please upload an image file (PNG, JPG, etc.) for your logo."
                )
                return {"status": "non_image_file"}
            
            # Process the logo
            file_url = file_info.get('url_private_download') or file_info.get('url_private')
            if not file_url:
                self.bot.send_error_message(channel, user, "Could not access the uploaded file")
                return {"status": "no_file_url"}
            
            # Download and process the logo
            logo_result = logo_processor.process_logo(file_url)
            
            if not logo_result['success']:
                self.bot.send_error_message(channel, user, f"Error processing logo: {logo_result.get('error', 'Unknown error')}")
                return {"status": "logo_processing_error"}
            
            # Update conversation with logo info
            current_state = conversation.get('state', 'initial')
            selected_products = conversation.get('selected_products', [])
            
            conversation_manager.update_conversation(channel, user, {
                'logo_url': logo_result['url'],
                'logo_file': logo_result.get('file_path'),
                'is_default_logo': False,
                'state': 'creating_mockups' if selected_products else 'product_selection'
            })
            
            # Handle based on current state
            if selected_products:
                # Products already selected, create mockups
                self.bot.send_message(
                    channel,
                    "Great! I've received your logo. Let me create some mockups for you..."
                )
                
                # Update conversation for mockup creation
                updated_conversation = conversation_manager.get_or_create_conversation(channel, user)
                return self.mockup_generator.create_custom_product(updated_conversation, logo_result, channel, user)
            else:
                # No products selected yet
                self.bot.send_message(
                    channel,
                    "Perfect! I've received your logo. Now, what type of products would you like to create?\n\n"
                    "Popular options include:\n"
                    "• *T-shirts* - Great for team practice\n"
                    "• *Hoodies* - Perfect for cooler weather\n"
                    "• *Hats* - Popular with fans\n\n"
                    "Just let me know what you're interested in!"
                )
                
                return {"status": "logo_uploaded", "state": "product_selection"}
                
        except Exception as e:
            logger.error(f"Error processing file upload: {e}", exc_info=True)
            self.bot.send_error_message(channel, user, "Error processing your file upload")
            return {"status": "error", "message": str(e)}