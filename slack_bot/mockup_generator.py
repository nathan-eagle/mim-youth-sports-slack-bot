"""
Mockup generation logic using Printify API
"""
import logging
import time
from typing import Dict, List, Optional
from conversation_manager import conversation_manager
from services.product_service import product_service
from printify_service import printify_service
from simple_database_service import database_service
from ai_color_service import ai_color_service
from openai_service import openai_service

logger = logging.getLogger(__name__)


class MockupGenerator:
    """Handles mockup generation for products"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def create_custom_product(self, conversation: Dict, logo_result: Dict, channel: str, user: str) -> Dict:
        """Create custom product mockups"""
        try:
            selected_products = conversation.get('selected_products', ['tshirt', 'hoodie'])
            logo_url = logo_result['url']
            
            # Update conversation state
            conversation_manager.update_conversation(channel, user, {'state': 'creating_mockups'})
            
            # Get AI-recommended colors for each product
            logger.info("Getting AI-recommended colors for products")
            default_colors = self._get_ai_default_colors_for_products(logo_url)
            
            # Generate mockups
            logger.info(f"Generating mockups for products: {selected_products}")
            return self._generate_all_mockups_with_default_colors(
                conversation, logo_result, channel, user, default_colors
            )
            
        except Exception as e:
            logger.error(f"Error creating custom product: {e}", exc_info=True)
            self.bot.send_error_message(channel, user, f"Error creating product: {str(e)}")
            
            conversation_manager.update_conversation(channel, user, {'state': 'completed'})
            return {"status": "error", "message": str(e)}
    
    def create_custom_product_with_color(self, conversation: Dict, logo_info: Dict, selected_color: str, channel: str, user: str) -> Dict:
        """Create custom product with specific color"""
        try:
            selected_products = conversation.get('selected_products', ['tshirt', 'hoodie'])
            
            # Create color mapping for all products
            selected_variants = {}
            for product_type in selected_products:
                selected_variants[product_type] = selected_color
            
            return self._generate_all_mockups_with_colors(
                conversation, logo_info, selected_variants, channel, user
            )
            
        except Exception as e:
            logger.error(f"Error creating product with color: {e}", exc_info=True)
            self.bot.send_error_message(channel, user, f"Error creating product: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _generate_all_mockups_with_default_colors(self, conversation: Dict, logo_info: Dict, channel: str, user: str, default_colors: Dict[str, str]) -> Dict:
        """Generate all mockups with AI-selected default colors"""
        try:
            selected_products = conversation.get('selected_products', ['tshirt', 'hoodie'])
            logo_url = logo_info['url']
            generated_mockups = []
            all_alternative_colors = []
            
            # Load Printify Choice products
            products_cache = product_service.load_printify_choice_products()
            if not products_cache:
                raise Exception("Failed to load Printify Choice products")
            
            all_products = products_cache.get('products', {})
            
            for product_type in selected_products:
                logger.info(f"Generating mockup for {product_type}")
                
                # Get best product for this type
                matching_products = [
                    p for p in all_products.values() 
                    if p['category'] == product_type and p.get('is_printify_choice', False)
                ]
                
                if not matching_products:
                    logger.warning(f"No Printify Choice products found for {product_type}")
                    continue
                
                # Sort by popularity score and take the best one
                matching_products.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
                product = matching_products[0]
                
                # Get default color for this product
                default_color = default_colors.get(product_type, 'Black')
                
                # Find matching variant
                selected_variant = None
                for variant in product.get('variants', []):
                    if variant['color'].lower() == default_color.lower():
                        selected_variant = variant
                        break
                
                # If exact match not found, find closest
                if not selected_variant and product.get('variants'):
                    selected_variant = product['variants'][0]  # Fallback to first variant
                    default_color = selected_variant['color']
                
                if not selected_variant:
                    logger.error(f"No variants found for {product['title']}")
                    continue
                
                # Create mockup
                mockup_result = self._create_single_mockup_with_variant(
                    conversation, logo_info, product, selected_variant, channel, user
                )
                
                if mockup_result.get('status') == 'success':
                    generated_mockups.append({
                        'product_type': product_type,
                        'product_name': product['title'],
                        'color': default_color,
                        'mockup_url': mockup_result.get('mockup_url'),
                        'drop_url': mockup_result.get('drop_url'),
                        'design_id': mockup_result.get('design_id')
                    })
                    
                    # Get alternative colors (top 5 different from default)
                    available_colors = list(set(v['color'] for v in product.get('variants', [])))
                    alt_colors = [c for c in available_colors if c.lower() != default_color.lower()][:5]
                    all_alternative_colors.extend(alt_colors)
            
            # Send results
            if generated_mockups:
                for mockup in generated_mockups:
                    self.bot.send_product_result_with_alternatives(
                        channel=channel,
                        image_url=mockup['mockup_url'],
                        purchase_url=mockup['drop_url'],
                        product_name=f"{mockup['product_name']} - {mockup['color']}",
                        available_colors=list(set(all_alternative_colors))[:8],
                        logo_url=logo_url
                    )
                
                # Update conversation
                conversation_manager.update_conversation(channel, user, {
                    'state': 'completed',
                    'generated_mockups': generated_mockups,
                    'colors_shown': list(set(all_alternative_colors))
                })
                
                # Final message
                self.bot.send_message(
                    channel,
                    "✅ Your custom products are ready! Click the links above to view and customize further.\n\n"
                    "Would you like to see these products in different colors? Just let me know!"
                )
                
                return {"status": "success", "mockups": generated_mockups}
            else:
                raise Exception("No mockups were generated successfully")
                
        except Exception as e:
            logger.error(f"Error generating mockups: {e}", exc_info=True)
            self.bot.send_error_message(channel, user, f"Error generating mockups: {str(e)}")
            conversation_manager.update_conversation(channel, user, {'state': 'completed'})
            return {"status": "error", "message": str(e)}
    
    def _generate_all_mockups_with_colors(self, conversation: Dict, logo_info: Dict, selected_variants: Dict, channel: str, user: str) -> Dict:
        """Generate mockups with specific colors"""
        try:
            generated_mockups = []
            logo_url = logo_info['url']
            
            # Load Printify Choice products
            products_cache = product_service.load_printify_choice_products()
            if not products_cache:
                raise Exception("Failed to load Printify Choice products")
            
            all_products = products_cache.get('products', {})
            
            for product_type, selected_color in selected_variants.items():
                logger.info(f"Generating {selected_color} mockup for {product_type}")
                
                # Get best product for this type
                matching_products = [
                    p for p in all_products.values() 
                    if p['category'] == product_type and p.get('is_printify_choice', False)
                ]
                
                if not matching_products:
                    continue
                
                # Sort by popularity score
                matching_products.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
                product = matching_products[0]
                
                # Find matching variant
                selected_variant = None
                for variant in product.get('variants', []):
                    if selected_color.lower() in variant['color'].lower():
                        selected_variant = variant
                        break
                
                if not selected_variant:
                    logger.warning(f"Color {selected_color} not found for {product['title']}")
                    continue
                
                # Create mockup
                mockup_result = self._create_single_mockup_with_variant(
                    conversation, logo_info, product, selected_variant, channel, user
                )
                
                if mockup_result.get('status') == 'success':
                    generated_mockups.append({
                        'product_type': product_type,
                        'product_name': product['title'],
                        'color': selected_variant['color'],
                        'mockup_url': mockup_result.get('mockup_url'),
                        'drop_url': mockup_result.get('drop_url')
                    })
            
            # Send results
            if generated_mockups:
                for mockup in generated_mockups:
                    self.bot.send_image_message(
                        channel=channel,
                        image_url=mockup['mockup_url'],
                        caption=f"{mockup['product_name']} in {mockup['color']}\n{mockup['drop_url']}"
                    )
                
                conversation_manager.update_conversation(channel, user, {
                    'state': 'completed',
                    'generated_mockups': generated_mockups
                })
                
                return {"status": "success", "mockups": generated_mockups}
            else:
                raise Exception("No mockups generated with selected colors")
                
        except Exception as e:
            logger.error(f"Error generating colored mockups: {e}", exc_info=True)
            self.bot.send_error_message(channel, user, f"Error: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _create_single_mockup_with_variant(self, conversation: Dict, logo_info: Dict, product_info: Dict, selected_variant: Dict, channel: str, user: str) -> Dict:
        """Create a single mockup with specific variant"""
        try:
            logo_url = logo_info['url']
            
            # Prepare design request
            design_request = {
                'blueprint_id': product_info['blueprint_id'],
                'print_provider_id': product_info['print_provider_id'],
                'variant_id': selected_variant['id'],
                'print_areas': {
                    'front': logo_url
                }
            }
            
            # Generate mockup
            logger.info(f"Generating mockup for {product_info['title']} - {selected_variant['color']}")
            mockup_result = printify_service.create_design_mockup(design_request)
            
            if not mockup_result['success']:
                raise Exception(mockup_result.get('error', 'Mockup generation failed'))
            
            # Save to database
            design_data = {
                'product_name': product_info['title'],
                'product_id': product_info['id'],
                'variant_id': selected_variant['id'],
                'color': selected_variant['color'],
                'size': selected_variant.get('size', 'Standard'),
                'mockup_url': mockup_result['mockup_url'],
                'logo_url': logo_url,
                'price': selected_variant.get('price', 25.00),
                'printify_data': {
                    'blueprint_id': product_info['blueprint_id'],
                    'print_provider_id': product_info['print_provider_id']
                }
            }
            
            design_id = database_service.save_product_design(design_data)
            drop_url = f"{database_service.get_drop_base_url()}/design/{design_id}"
            
            return {
                'status': 'success',
                'mockup_url': mockup_result['mockup_url'],
                'drop_url': drop_url,
                'design_id': design_id
            }
            
        except Exception as e:
            logger.error(f"Error creating single mockup: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    def _get_ai_default_colors_for_products(self, logo_url: str) -> Dict[str, str]:
        """Get AI-recommended default colors for each product type"""
        try:
            result = ai_color_service.get_default_colors_for_products(logo_url)
            
            if result['success']:
                return result['colors']
            else:
                logger.warning(f"AI color selection failed: {result.get('error')}")
                # Fallback defaults
                return {
                    'tshirt': 'Black',
                    'hoodie': 'Black',
                    'headwear': 'Black',
                    'tank': 'Black',
                    'long_sleeve': 'Black'
                }
                
        except Exception as e:
            logger.error(f"Error getting AI colors: {e}")
            # Fallback defaults
            return {
                'tshirt': 'Black',
                'hoodie': 'Black',
                'headwear': 'Black',
                'tank': 'Black',
                'long_sleeve': 'Black'
            }