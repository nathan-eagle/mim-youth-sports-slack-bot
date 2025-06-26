import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self, cache_file_path: str = "product_cache.json"):
        self.cache_file_path = cache_file_path
        self.products_cache = {}
        self.best_products = {}
        self._load_cache()
    
    def _load_cache(self) -> bool:
        """Load product cache from disk"""
        try:
            with open(self.cache_file_path, 'r') as f:
                data = json.load(f)
                self.products_cache = data.get('products', {})
                self._filter_best_products()
                logger.info(f"Loaded {len(self.products_cache)} products, {len(self.best_products)} tagged as 'best'")
                return True
        except Exception as e:
            logger.error(f"Failed to load product cache: {e}")
            return False
    
    def _filter_best_products(self):
        """Filter products tagged as 'best'"""
        self.best_products = {}
        for product_id, product in self.products_cache.items():
            if 'best' in product.get('tags', []):
                self.best_products[product_id] = product
                logger.info(f"Found best product: {product.get('title')} (ID: {product_id})")
    
    def get_best_products(self) -> Dict:
        """Get all products tagged as 'best'"""
        return self.best_products.copy()
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get specific product by ID"""
        return self.products_cache.get(str(product_id))
    
    def get_products_by_category(self, category: str) -> Dict:
        """Get best products filtered by category"""
        filtered_products = {}
        for product_id, product in self.best_products.items():
            if product.get('category', '').lower() == category.lower():
                filtered_products[product_id] = product
        return filtered_products
    
    def format_product_for_slack(self, product_id: str, product: Dict) -> Dict:
        """Format product info for Slack display"""
        if not product:
            return {}
        
        title = product.get('title', 'Unknown Product')
        category = product.get('category', 'unknown').title()
        colors = product.get('available_colors', [])
        
        # Limit colors shown to first 8 for readability
        color_display = colors[:8] if len(colors) > 8 else colors
        color_text = ", ".join(color_display)
        if len(colors) > 8:
            color_text += f" (+{len(colors) - 8} more)"
        
        return {
            'id': product_id,
            'title': title,
            'category': category,
            'colors': colors,
            'color_display': color_text,
            'available': product.get('available', False)
        }
    
    def get_product_suggestions_text(self) -> str:
        """Get formatted text showing all best products for parent selection"""
        if not self.best_products:
            return "Sorry, no recommended products are currently available."
        
        suggestions = ["Here are our recommended products for youth sports teams:\n"]
        
        for product_id, product in self.best_products.items():
            formatted = self.format_product_for_slack(product_id, product)
            suggestions.append(
                f"• *{formatted['title']}* ({formatted['category']})\n"
                f"  Available colors: {formatted['color_display']}\n"
            )
        
        suggestions.append("\nWhich type of product would you like to customize for your team?")
        return "".join(suggestions)
    
    def find_product_by_intent(self, user_message: str) -> Optional[Dict]:
        """Find best matching product based on user intent"""
        message_lower = user_message.lower()
        
        # Define keyword mappings for product categories
        category_keywords = {
            'shirt': ['shirt', 'tee', 't-shirt', 'tshirt', 'top'],
            'hoodie': ['hoodie', 'sweatshirt', 'hoodie', 'pullover', 'sweater'],
            'hat': ['hat', 'cap', 'snapback', 'trucker', 'beanie']
        }
        
        # Special handling for specific product requests
        # Check for hoodie/sweatshirt first - map to product ID 314
        hoodie_keywords = ['hoodie', 'sweatshirt', 'pullover', 'sweater', 'hooded', 'heavy blend']
        if any(keyword in message_lower for keyword in hoodie_keywords):
            # Return the Youth Heavy Blend Hooded Sweatshirt (ID: 314)
            if '314' in self.best_products:
                product = self.best_products['314']
                return {
                    'id': '314',
                    'product': product,
                    'formatted': self.format_product_for_slack('314', product)
                }
        
        # Check for hat/cap requests - map to product ID 1446
        hat_keywords = ['hat', 'cap', 'snapback', 'trucker', 'beanie']
        if any(keyword in message_lower for keyword in hat_keywords):
            if '1446' in self.best_products:
                product = self.best_products['1446']
                return {
                    'id': '1446',
                    'product': product,
                    'formatted': self.format_product_for_slack('1446', product)
                }
        
        # Check for shirt/tee requests - map to product ID 157
        shirt_keywords = ['shirt', 'tee', 't-shirt', 'tshirt', 'top']
        if any(keyword in message_lower for keyword in shirt_keywords):
            if '157' in self.best_products:
                product = self.best_products['157']
                return {
                    'id': '157',
                    'product': product,
                    'formatted': self.format_product_for_slack('157', product)
                }
        
        # Fallback: Look for category matches in user message (old logic)
        for category, keywords in category_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                matching_products = self.get_products_by_category(category)
                if matching_products:
                    # Return first matching product
                    product_id = list(matching_products.keys())[0]
                    return {
                        'id': product_id,
                        'product': matching_products[product_id],
                        'formatted': self.format_product_for_slack(product_id, matching_products[product_id])
                    }
        
        return None

# Global instance
product_service = ProductService() 