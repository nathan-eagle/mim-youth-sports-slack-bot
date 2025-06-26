import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self, cache_file_path: str = "product_cache.json"):
        self.cache_file_path = cache_file_path
        self.products_cache = {}
        self.best_products = {}
        
        # Real mappings from Printify API for the 3 best products
        self.product_mappings = {
            '157': {  # Kids Heavy Cotton™ Tee
                'blueprint_id': 6,        # Unisex Heavy Cotton Tee (Gildan 5000)
                'print_provider_id': 3,   # Marco Fine Arts (default provider)
                'category': 'shirt'
            },
            '314': {  # Youth Heavy Blend Hooded Sweatshirt  
                'blueprint_id': 314,      # Youth Heavy Blend Hooded Sweatshirt (Gildan 18500B)
                'print_provider_id': 249, # HFT71 Sp. z o.o (verified working provider)
                'category': 'hoodie'
            },
            '1446': {  # Snapback Trucker Cap
                'blueprint_id': 1446,     # Snapback Trucker Cap (Yupoong 6606)
                'print_provider_id': 217, # Fulfill Engine (default provider)
                'category': 'hat'
            }
        }
        
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
        """Get specific product by ID with enhanced data including variants"""
        base_product = self.products_cache.get(str(product_id))
        if not base_product:
            return None
            
        # Enhance with blueprint/provider data and variants
        enhanced_product = base_product.copy()
        
        # Add blueprint and print provider info from our mappings
        if str(product_id) in self.product_mappings:
            mapping = self.product_mappings[str(product_id)]
            enhanced_product['blueprint_id'] = mapping['blueprint_id']
            enhanced_product['print_provider_id'] = mapping['print_provider_id']
            enhanced_product['category'] = mapping['category']
        
        # Use real variants for our specific blueprint + provider combinations
        real_variants = {
            '157': [  # T-shirt (blueprint 6 + provider 3) - Real variants from API
                {'id': 11848, 'title': 'Ash / L', 'options': {'color': 'Ash', 'size': 'L'}},
                {'id': 11849, 'title': 'Ash / M', 'options': {'color': 'Ash', 'size': 'M'}},
                {'id': 11850, 'title': 'Ash / S', 'options': {'color': 'Ash', 'size': 'S'}},
                {'id': 12100, 'title': 'White / L', 'options': {'color': 'White', 'size': 'L'}},
                {'id': 12101, 'title': 'White / M', 'options': {'color': 'White', 'size': 'M'}},
                {'id': 12102, 'title': 'White / S', 'options': {'color': 'White', 'size': 'S'}},
                {'id': 12124, 'title': 'Black / L', 'options': {'color': 'Black', 'size': 'L'}},
                {'id': 12126, 'title': 'Black / S', 'options': {'color': 'Black', 'size': 'S'}},
                {'id': 12028, 'title': 'Royal / L', 'options': {'color': 'Royal', 'size': 'L'}},
                {'id': 12029, 'title': 'Royal / M', 'options': {'color': 'Royal', 'size': 'M'}},
                {'id': 12030, 'title': 'Royal / S', 'options': {'color': 'Royal', 'size': 'S'}},
                {'id': 12022, 'title': 'Red / L', 'options': {'color': 'Red', 'size': 'L'}},
                {'id': 12023, 'title': 'Red / M', 'options': {'color': 'Red', 'size': 'M'}},
                {'id': 12024, 'title': 'Red / S', 'options': {'color': 'Red', 'size': 'S'}},
                {'id': 11986, 'title': 'Navy / L', 'options': {'color': 'Navy', 'size': 'L'}},
                {'id': 11987, 'title': 'Navy / M', 'options': {'color': 'Navy', 'size': 'M'}},
                {'id': 11988, 'title': 'Navy / S', 'options': {'color': 'Navy', 'size': 'S'}}
            ],
            '314': [  # Youth Heavy Blend Hooded Sweatshirt (blueprint 314 + provider 249) - Real variants from API
                {'id': 43880, 'title': 'Black / S', 'options': {'color': 'Black', 'size': 'S'}},
                {'id': 43899, 'title': 'Black / M', 'options': {'color': 'Black', 'size': 'M'}},
                {'id': 43918, 'title': 'Black / L', 'options': {'color': 'Black', 'size': 'L'}},
                {'id': 43937, 'title': 'Black / XL', 'options': {'color': 'Black', 'size': 'XL'}},
                {'id': 64304, 'title': 'Black / XS', 'options': {'color': 'Black', 'size': 'XS'}},
                {'id': 43873, 'title': 'Navy / S', 'options': {'color': 'Navy', 'size': 'S'}},
                {'id': 43892, 'title': 'Navy / M', 'options': {'color': 'Navy', 'size': 'M'}},
                {'id': 43911, 'title': 'Navy / L', 'options': {'color': 'Navy', 'size': 'L'}},
                {'id': 43930, 'title': 'Navy / XL', 'options': {'color': 'Navy', 'size': 'XL'}},
                {'id': 64296, 'title': 'Navy / XS', 'options': {'color': 'Navy', 'size': 'XS'}},
                {'id': 43877, 'title': 'Royal / S', 'options': {'color': 'Royal', 'size': 'S'}},
                {'id': 43896, 'title': 'Royal / M', 'options': {'color': 'Royal', 'size': 'M'}},
                {'id': 43915, 'title': 'Royal / L', 'options': {'color': 'Royal', 'size': 'L'}},
                {'id': 43934, 'title': 'Royal / XL', 'options': {'color': 'Royal', 'size': 'XL'}},
                {'id': 64300, 'title': 'Royal / XS', 'options': {'color': 'Royal', 'size': 'XS'}},
                {'id': 43876, 'title': 'Red / S', 'options': {'color': 'Red', 'size': 'S'}},
                {'id': 43895, 'title': 'Red / M', 'options': {'color': 'Red', 'size': 'M'}},
                {'id': 43914, 'title': 'Red / L', 'options': {'color': 'Red', 'size': 'L'}},
                {'id': 43933, 'title': 'Red / XL', 'options': {'color': 'Red', 'size': 'XL'}},
                {'id': 64299, 'title': 'Red / XS', 'options': {'color': 'Red', 'size': 'XS'}}
            ]
        }
        
        if str(product_id) in real_variants:
            enhanced_product['variants'] = real_variants[str(product_id)]
            logger.info(f"Using real Printify variants for product {product_id}: {len(enhanced_product['variants'])} variants")
        else:
            # Fallback: try to load variants from complete cache
            try:
                with open('product_cache_complete.json', 'r') as f:
                    complete_data = json.load(f)
                    complete_products = complete_data.get('products', {})
                    
                    if str(product_id) in complete_products:
                        complete_product = complete_products[str(product_id)]
                        
                        # Add variants if available
                        if 'variants' in complete_product:
                            enhanced_product['variants'] = complete_product['variants']
                        
                        # Add other useful data
                        if 'description' in complete_product:
                            enhanced_product['description'] = complete_product['description']
                            
            except Exception as e:
                logger.warning(f"Could not load complete cache for variants: {e}")
                # Provide a default variant if none found
                enhanced_product['variants'] = [
                    {
                        'id': 1,  # Default variant
                        'title': 'Default',
                        'price': 2000,  # $20 in cents
                        'available': True
                    }
                ]
        
        return enhanced_product
    
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