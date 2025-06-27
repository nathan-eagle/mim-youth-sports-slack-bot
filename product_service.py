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
            '1221': {  # Dad Hat with Leather Patch (Rectangle)
                'blueprint_id': 1221,     # Dad Hat with Leather Patch (Rectangle)
                'print_provider_id': 261, # Fancy Fanny (dye-sublimation - faster than embroidery)
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
            ],
            '1221': [  # Dad Hat with Leather Patch (blueprint 1221 + provider 261) - Real variants from API
                {'id': 93560, 'title': 'Black / Black patch / Rectangle / One size', 'options': {'color': 'Black / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93558, 'title': 'Black / Grey patch / Rectangle / One size', 'options': {'color': 'Black / Grey patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93562, 'title': 'Black / Light Brown / Rectangle / One size', 'options': {'color': 'Black / Light Brown', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93566, 'title': 'Black / Pink patch / Rectangle / One size', 'options': {'color': 'Black / Pink patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93584, 'title': 'Navy / Black patch / Rectangle / One size', 'options': {'color': 'Navy / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93586, 'title': 'Navy / Grey patch / Rectangle / One size', 'options': {'color': 'Navy / Grey patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93592, 'title': 'Red / Black patch / Rectangle / One size', 'options': {'color': 'Red / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93556, 'title': 'White / Light Brown patch / Rectangle / One size', 'options': {'color': 'White / Light Brown patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93564, 'title': 'White / Black patch / Rectangle / One size', 'options': {'color': 'White / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93600, 'title': 'White / Grey patch / Rectangle / One size', 'options': {'color': 'White / Grey patch', 'shape': 'Rectangle', 'size': 'One size'}}
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
    
    def get_available_colors_for_best_products(self) -> Dict:
        """Get available colors for each of the 3 best products"""
        colors_by_product = {}
        
        # Product IDs for our 3 best products
        product_ids = ['157', '314', '1221']
        
        # Real variants data from our mappings
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
            ],
            '1221': [  # Dad Hat with Leather Patch (blueprint 1221 + provider 261) - Real variants from API
                {'id': 93560, 'title': 'Black / Black patch / Rectangle / One size', 'options': {'color': 'Black / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93558, 'title': 'Black / Grey patch / Rectangle / One size', 'options': {'color': 'Black / Grey patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93562, 'title': 'Black / Light Brown / Rectangle / One size', 'options': {'color': 'Black / Light Brown', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93566, 'title': 'Black / Pink patch / Rectangle / One size', 'options': {'color': 'Black / Pink patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93584, 'title': 'Navy / Black patch / Rectangle / One size', 'options': {'color': 'Navy / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93586, 'title': 'Navy / Grey patch / Rectangle / One size', 'options': {'color': 'Navy / Grey patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93592, 'title': 'Red / Black patch / Rectangle / One size', 'options': {'color': 'Red / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93556, 'title': 'White / Light Brown patch / Rectangle / One size', 'options': {'color': 'White / Light Brown patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93564, 'title': 'White / Black patch / Rectangle / One size', 'options': {'color': 'White / Black patch', 'shape': 'Rectangle', 'size': 'One size'}},
                {'id': 93600, 'title': 'White / Grey patch / Rectangle / One size', 'options': {'color': 'White / Grey patch', 'shape': 'Rectangle', 'size': 'One size'}}
            ]
        }
        
        for product_id in product_ids:
            if product_id not in real_variants:
                continue
                
            # Extract unique colors from variants
            variants = real_variants[product_id]
            colors = set()
            
            for variant in variants:
                color = variant.get('options', {}).get('color')
                if color:
                    colors.add(color)
            
            colors_by_product[product_id] = sorted(list(colors))
            
        return colors_by_product
    
    def format_color_selection_message(self) -> str:
        """Format a message showing color options for all products"""
        colors_by_product = self.get_available_colors_for_best_products()
        
        if not colors_by_product:
            return "🎨 *Choose colors for your products:*\n\nSorry, color options are currently unavailable."
        
        message_parts = ["🎨 *Choose colors for your products:*\n"]
        
        product_names = {
            '157': 'T-shirt',
            '314': 'Hoodie', 
            '1221': 'Hat'
        }
        
        for product_id, colors in colors_by_product.items():
            product_name = product_names.get(product_id, f"Product {product_id}")
            if colors:
                # Limit to first 6 colors for display
                display_colors = colors[:6]
                color_text = ", ".join(display_colors)
                if len(colors) > 6:
                    color_text += f" (+{len(colors) - 6} more)"
                    
                message_parts.append(f"• *{product_name}:* {color_text}")
        
        message_parts.append("\n*Just tell me your color preferences!* For example:")
        message_parts.append("• \"Black t-shirt, navy hoodie, white hat\"")
        message_parts.append("• \"All black\" or \"All white\"")
        message_parts.append("• \"Default colors\" (uses first available color for each)")
        
        return "\n".join(message_parts)
    
    def parse_color_preferences(self, user_input: str) -> Dict:
        """Parse user color preferences and return selected variants for each product"""
        user_input_lower = user_input.lower().strip()
        
        # Get available colors for each product
        colors_by_product = self.get_available_colors_for_best_products()
        
        selected_variants = {}
        product_names_map = {
            'tshirt': '157', 't-shirt': '157', 'shirt': '157', 'tee': '157',
            'hoodie': '314', 'sweatshirt': '314', 'pullover': '314',
            'hat': '1221', 'cap': '1221'
        }
        
        # Check for "default" or "default colors"
        if 'default' in user_input_lower:
            for product_id in ['157', '314', '1221']:
                if product_id in colors_by_product and colors_by_product[product_id]:
                    first_color = colors_by_product[product_id][0]
                    selected_variants[product_id] = self._find_variant_by_color(product_id, first_color)
            return selected_variants
        
        # Check for "all [color]" pattern
        all_color_match = None
        for color_name in ['black', 'white', 'navy', 'red', 'royal', 'ash']:
            if f'all {color_name}' in user_input_lower:
                all_color_match = color_name.title()
                break
        
        if all_color_match:
            for product_id in ['157', '314', '1221']:
                variant = self._find_variant_by_color(product_id, all_color_match)
                if variant:
                    selected_variants[product_id] = variant
            return selected_variants
        
        # Parse specific product color assignments
        # Look for patterns like "black t-shirt", "navy hoodie", "white hat"
        import re
        
        for product_name, product_id in product_names_map.items():
            # Find mentions of this product in the input
            pattern = rf'(\w+)\s+{re.escape(product_name)}'
            matches = re.findall(pattern, user_input_lower)
            
            if matches:
                # Try to match the color word before the product name
                color_word = matches[0].strip()
                colors = colors_by_product.get(product_id, [])
                
                for color in colors:
                    color_simple = color.split('/')[0].strip().lower()  # Handle "Black / Black patch" -> "black"
                    if color_simple == color_word:
                        variant = self._find_variant_by_color(product_id, color)
                        if variant:
                            selected_variants[product_id] = variant
                        break
            elif product_name in user_input_lower:
                # Fallback: look for any color words near the product name
                colors = colors_by_product.get(product_id, [])
                for color in colors:
                    color_simple = color.split('/')[0].strip()  # Handle "Black / Black patch" -> "Black"
                    if color_simple.lower() in user_input_lower:
                        variant = self._find_variant_by_color(product_id, color)
                        if variant:
                            selected_variants[product_id] = variant
                        break
        
        # If no specific assignments found, try to find colors for any unassigned products
        if not selected_variants:
            available_colors = set()
            for colors in colors_by_product.values():
                for color in colors:
                    available_colors.add(color.split('/')[0].strip().lower())
            
            mentioned_colors = []
            for color in available_colors:
                if color in user_input_lower:
                    mentioned_colors.append(color.title())
            
            # Assign first mentioned color to all products if possible
            if mentioned_colors:
                primary_color = mentioned_colors[0]
                for product_id in ['157', '314', '1221']:
                    variant = self._find_variant_by_color(product_id, primary_color)
                    if variant:
                        selected_variants[product_id] = variant
        
        # Fill in missing products with defaults
        for product_id in ['157', '314', '1221']:
            if product_id not in selected_variants:
                if product_id in colors_by_product and colors_by_product[product_id]:
                    first_color = colors_by_product[product_id][0]
                    selected_variants[product_id] = self._find_variant_by_color(product_id, first_color)
        
        return selected_variants
    
    def _find_variant_by_color(self, product_id: str, color: str) -> Optional[Dict]:
        """Find a variant for a product that matches the specified color"""
        product_details = self.get_product_by_id(product_id)
        if not product_details or 'variants' not in product_details:
            return None
            
        variants = product_details['variants']
        
        # Try exact match first
        for variant in variants:
            variant_color = variant.get('options', {}).get('color', '')
            if variant_color == color:
                return variant
        
        # Try partial match (for hat colors like "Black / Black patch")
        for variant in variants:
            variant_color = variant.get('options', {}).get('color', '')
            if variant_color.startswith(color) or color in variant_color:
                return variant
                
        return None

# Global instance
product_service = ProductService() 