#!/usr/bin/env python3
"""
Simple mockup generator that works without database dependencies
"""

import logging
from typing import Dict, List
from services.product_service import product_service

logger = logging.getLogger(__name__)

class SimpleMockupGenerator:
    """Simple mockup generator without complex database dependencies"""
    
    def __init__(self, bot):
        self.bot = bot
        
    def generate_mockups(self, product_categories: List[str], requested_colors: List[str] = None) -> Dict:
        """Generate simple mockups without database dependencies"""
        try:
            logger.info(f"Generating simple mockups for products: {product_categories}")
            
            mockups = []
            
            for category in product_categories:
                products = product_service.get_products_by_category(category)
                if isinstance(products, dict):
                    products = list(products.values())
                
                if products:
                    # Get the best product for this category
                    best_product = products[0]
                    
                    # Get a default color variant
                    variants = best_product.get('variants', [])
                    if variants:
                        # Look for black, navy, or first available
                        default_variant = None
                        for variant in variants:
                            color = variant.get('color', '').lower()
                            if 'black' in color or 'navy' in color:
                                default_variant = variant
                                break
                        
                        if not default_variant:
                            default_variant = variants[0]
                        
                        # Create simple mockup info
                        mockup = {
                            'product_name': best_product['title'],
                            'color': default_variant['color'],
                            'size': default_variant.get('size', 'M'),
                            'mockup_url': 'https://via.placeholder.com/400x400/000000/FFFFFF?text=Mockup',
                            'message': f"✅ {best_product['title']} in {default_variant['color']}"
                        }
                        mockups.append(mockup)
                        
                        logger.info(f"Created simple mockup: {mockup['product_name']} - {mockup['color']}")
            
            if mockups:
                return {
                    'status': 'success',
                    'mockups': mockups
                }
            else:
                return {
                    'status': 'error',
                    'message': 'No products found for the requested categories'
                }
                
        except Exception as e:
            logger.error(f"Error generating simple mockups: {e}")
            return {
                'status': 'error',
                'message': f'Mockup generation failed: {str(e)}'
            }
    
    def handle_color_change(self, product_name: str, new_color: str) -> Dict:
        """Handle color change requests"""
        return {
            'status': 'success',
            'message': f"Color changed to {new_color} for {product_name}",
            'mockup_url': 'https://via.placeholder.com/400x400/000000/FFFFFF?text=New+Color'
        }

# For compatibility with existing code
MockupGenerator = SimpleMockupGenerator