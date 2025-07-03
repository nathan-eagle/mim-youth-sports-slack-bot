"""
AI-powered product selection based on user conversation
"""
import logging
from typing import Dict, List, Optional, Tuple
from .product_service import product_service
from openai_service import openai_service

logger = logging.getLogger(__name__)


class ProductSelector:
    """Handles intelligent product selection using AI"""
    
    def __init__(self):
        self.product_service = product_service
    
    def select_products_from_conversation(self, text: str, conversation_context: Dict) -> Dict:
        """Select products based on user input and conversation context"""
        try:
            # Get AI analysis of the request
            ai_result = openai_service.analyze_product_request_conversation(text, conversation_context)
            
            if not ai_result.get('success', False):
                return {
                    'success': False,
                    'error': 'Could not understand product request',
                    'suggested_products': self._get_default_suggestions()
                }
            
            requested_categories = ai_result.get('products', [])
            
            if not requested_categories:
                return {
                    'success': False,
                    'error': 'No specific products mentioned',
                    'suggested_products': self._get_default_suggestions()
                }
            
            # Find matching products for each category
            selected_products = []
            alternatives = {}
            
            for category in requested_categories:
                products = self.product_service.get_products_by_category(category)
                
                # Convert dict to list if needed (from compatibility wrapper)
                if isinstance(products, dict):
                    products = list(products.values())
                
                if products:
                    # Select the most popular product
                    best_product = products[0]
                    selected_products.append(best_product)
                    
                    # Store alternatives (next 4 most popular)
                    alternatives[category] = products[1:5]
                else:
                    logger.warning(f"No products found for category: {category}")
            
            if not selected_products:
                return {
                    'success': False,
                    'error': 'No matching products found',
                    'suggested_products': self._get_default_suggestions()
                }
            
            return {
                'success': True,
                'selected_products': selected_products,
                'alternatives': alternatives,
                'categories': requested_categories
            }
            
        except Exception as e:
            logger.error(f"Error selecting products: {e}")
            return {
                'success': False,
                'error': str(e),
                'suggested_products': self._get_default_suggestions()
            }
    
    def get_alternative_products(self, current_category: str, exclude_product_id: str = None) -> List[Dict]:
        """Get alternative products in the same category"""
        products = self.product_service.get_products_by_category(current_category)
        
        if exclude_product_id:
            products = [p for p in products if str(p.get('id')) != str(exclude_product_id)]
        
        return products[:5]  # Return top 5 alternatives
    
    def suggest_complementary_products(self, selected_categories: List[str]) -> List[Dict]:
        """Suggest complementary products based on what's already selected"""
        # Define complementary categories
        complementary_map = {
            'tshirt': ['hoodie', 'headwear', 'tank'],
            'hoodie': ['tshirt', 'headwear', 'long_sleeve'],
            'headwear': ['tshirt', 'hoodie', 'tank'],
            'tank': ['tshirt', 'hoodie', 'headwear'],
            'long_sleeve': ['hoodie', 'headwear', 'tshirt']
        }
        
        suggested_categories = set()
        
        # Find complementary categories
        for category in selected_categories:
            complementary = complementary_map.get(category, [])
            for comp_cat in complementary:
                if comp_cat not in selected_categories:
                    suggested_categories.add(comp_cat)
        
        # Get best product from each suggested category
        suggestions = []
        for category in suggested_categories:
            products = self.product_service.get_products_by_category(category)
            if products:
                suggestions.append(products[0])  # Best product in category
        
        # Sort by popularity and return top 3
        suggestions.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
        return suggestions[:3]
    
    def format_product_suggestions_message(self, alternatives: Dict[str, List[Dict]], 
                                         complementary: List[Dict] = None) -> str:
        """Format alternative and complementary products into a message"""
        message_parts = []
        
        # Add alternatives
        if alternatives:
            message_parts.append("*Other options in the same categories:*")
            for category, products in alternatives.items():
                if products:
                    product_names = [p['title'] for p in products[:3]]
                    message_parts.append(f"• *{category.title()}:* {', '.join(product_names)}")
        
        # Add complementary suggestions
        if complementary:
            message_parts.append("\n*You might also like:*")
            for product in complementary:
                message_parts.append(f"• *{product['title']}* ({product['category'].title()})")
        
        return "\n".join(message_parts) if message_parts else ""
    
    def _get_default_suggestions(self) -> List[Dict]:
        """Get default product suggestions when AI fails"""
        return self.product_service.get_default_products()
    
    def match_product_to_sport_context(self, sport_keywords: List[str], 
                                     conversation_context: Dict) -> List[str]:
        """Match products to specific sport context"""
        # Sport-specific product recommendations
        sport_product_map = {
            'soccer': ['tshirt', 'hoodie', 'headwear'],
            'football': ['tshirt', 'hoodie', 'headwear', 'long_sleeve'],
            'basketball': ['tank', 'tshirt', 'hoodie', 'headwear'],
            'baseball': ['tshirt', 'headwear', 'hoodie'],
            'volleyball': ['tank', 'tshirt', 'headwear'],
            'swimming': ['tank', 'tshirt'],
            'track': ['tank', 'tshirt', 'long_sleeve'],
            'tennis': ['tshirt', 'tank', 'headwear'],
            'golf': ['tshirt', 'headwear'],
        }
        
        # Find sport context
        text_lower = (conversation_context.get('sport_context', '') + ' ' + 
                     ' '.join(sport_keywords)).lower()
        
        recommended_categories = []
        for sport, categories in sport_product_map.items():
            if sport in text_lower:
                recommended_categories.extend(categories)
                break
        
        # If no specific sport found, return general recommendations
        if not recommended_categories:
            recommended_categories = ['tshirt', 'hoodie', 'headwear']
        
        return list(set(recommended_categories))  # Remove duplicates


# Create singleton instance
product_selector = ProductSelector()