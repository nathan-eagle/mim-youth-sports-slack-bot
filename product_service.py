import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ProductService:
    def __init__(self, cache_file_path: str = "top3_product_cache_optimized.json"):
        self.cache_file_path = cache_file_path
        self.products_cache = {}
        self.cache_metadata = {}
        self.providers = {}
        
        self._load_cache()
    
    def _load_cache(self) -> bool:
        """Load the optimized top3 product cache from disk"""
        try:
            with open(self.cache_file_path, 'r') as f:
                data = json.load(f)
                self.products_cache = data.get('products', {})
                self.cache_metadata = data.get('optimization_info', {})
                self.providers = data.get('providers', {})
                
                logger.info(f"Loaded top3 cache: {len(self.products_cache)} products from {self.cache_metadata.get('categories_included', 0)} categories")
                return True
        except Exception as e:
            logger.error(f"Failed to load product cache: {e}")
            return False
    
    def get_all_products(self) -> Dict:
        """Get all available products (these are already the 'best' products)"""
        return self.products_cache.copy()
    
    def get_products_by_category(self, category: str) -> Dict:
        """Get products filtered by category"""
        return {
            product_id: product 
            for product_id, product in self.products_cache.items()
            if product.get('category', '').lower() == category.lower()
        }
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get specific product by ID with all cached data"""
        product = self.products_cache.get(str(product_id))
        if not product:
            logger.warning(f"Product {product_id} not found in cache")
            return None
            
        # The product already has all the data we need from the optimized cache
        enhanced_product = product.copy()
        
        # Add provider name if we have it
        primary_provider_id = product.get('primary_print_provider_id')
        if primary_provider_id and str(primary_provider_id) in self.providers:
            enhanced_product['primary_print_provider_name'] = self.providers[str(primary_provider_id)]
        
        return enhanced_product
    
    def get_best_products(self) -> Dict:
        """Get best products - in this cache, all products are the best"""
        return self.get_all_products()
    
    def get_product_variants(self, product_id: str) -> List[Dict]:
        """Get all variants for a specific product"""
        product = self.get_product_by_id(product_id)
        if not product:
            return []
        
        return product.get('variants', [])
    
    def get_colors_for_product(self, product_id: str) -> List[str]:
        """Get all available colors for a product"""
        variants = self.get_product_variants(product_id)
        colors = set()
        
        for variant in variants:
            if variant.get('available', True):
                color = variant.get('color')
                if color:
                    colors.add(color)
        
        return sorted(list(colors))
    
    def get_sizes_for_product(self, product_id: str) -> List[str]:
        """Get all available sizes for a product"""
        variants = self.get_product_variants(product_id)
        sizes = set()
        
        for variant in variants:
            if variant.get('available', True):
                size = variant.get('size')
                if size:
                    sizes.add(size)
        
        # Sort sizes in logical order
        size_order = ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL']
        sorted_sizes = []
        
        for size in size_order:
            if size in sizes:
                sorted_sizes.append(size)
                sizes.remove(size)
        
        sorted_sizes.extend(sorted(list(sizes)))
        return sorted_sizes
    
    def find_variant_by_options(self, product_id: str, color: str, size: str) -> Optional[Dict]:
        """Find a specific variant by color and size"""
        variants = self.get_product_variants(product_id)
        
        for variant in variants:
            if (variant.get('color', '').lower() == color.lower() and 
                variant.get('size', '').lower() == size.lower() and
                variant.get('available', True)):
                return variant
        
        return None
    
    def _find_variant_by_color(self, product_id: str, color: str) -> Optional[Dict]:
        """Find a variant by color (backward compatibility method)"""
        variants = self.get_product_variants(product_id)
        
        # Try to find exact color match first
        for variant in variants:
            if (variant.get('color', '').lower() == color.lower() and
                variant.get('available', True)):
                return variant
        
        # If no exact match, try partial match
        for variant in variants:
            if (color.lower() in variant.get('color', '').lower() and
                variant.get('available', True)):
                return variant
        
        # Return first available variant as fallback
        for variant in variants:
            if variant.get('available', True):
                return variant
        
        return None
    
    def validate_product_data(self, product_id: str) -> Dict[str, bool]:
        """Validate that a product has all required data for ordering"""
        product = self.get_product_by_id(product_id)
        if not product:
            return {'valid': False, 'error': 'Product not found'}
        
        validation = {
            'valid': True,
            'has_blueprint_id': bool(product.get('blueprint_id')),
            'has_print_areas': bool(product.get('print_areas')),
            'has_variants': bool(product.get('variants')),
            'has_pricing': False,
            'errors': []
        }
        
        # Check if variants have pricing
        variants = product.get('variants', [])
        if variants:
            priced_variants = [v for v in variants if v.get('price')]
            validation['has_pricing'] = len(priced_variants) > 0
        
        # Check for errors
        required_checks = [
            ('has_blueprint_id', 'Missing blueprint_id'),
            ('has_print_areas', 'Missing print_areas'),
            ('has_variants', 'Missing variants'),
            ('has_pricing', 'Missing variant pricing')
        ]
        
        for check, error_msg in required_checks:
            if not validation[check]:
                validation['errors'].append(error_msg)
        
        validation['valid'] = len(validation['errors']) == 0
        return validation
    
    def find_product_by_intent_ai(self, text: str) -> Optional[Dict]:
        """Use AI to find the best product match based on user intent"""
        from openai_service import openai_service
        
        try:
            # Get all available products
            all_products = []
            for product_id, product_data in self.products_cache.items():
                all_products.append({
                    'id': product_id,
                    'title': product_data.get('title', ''),
                    'category': product_data.get('category', 'unknown')
                })
            
            if not all_products:
                logger.error("No products available for AI analysis")
                return None
            
            # Use AI to analyze the request and find best match
            ai_result = openai_service.analyze_product_request(text, all_products)
            best_product_id = ai_result.get('best_product_match')
            
            if best_product_id and best_product_id in self.products_cache:
                product_data = self.products_cache[best_product_id]
                logger.info(f"AI selected product {best_product_id} ({product_data.get('title')}): {ai_result.get('reasoning')}")
                
                return {
                    'id': best_product_id,
                    'product': product_data,
                    'formatted': {
                        'title': product_data.get('title'),
                        'category': product_data.get('category')
                    },
                    'ai_confidence': ai_result.get('confidence', 'medium'),
                    'ai_reasoning': ai_result.get('reasoning', '')
                }
            else:
                logger.warning(f"AI selected invalid product ID: {best_product_id}")
                return None
                
        except Exception as e:
            logger.error(f"AI product selection failed: {e}")
            return self.find_product_by_intent(text)  # Fallback to old method

    def find_product_by_intent(self, text: str) -> Optional[Dict]:
        """Find a product based on user intent/text"""
        text_lower = text.lower()
        
        # Map keywords to product categories and specific products
        keyword_mappings = {
            # Shirts
            'shirt': 'shirt',
            'tee': 'shirt', 
            't-shirt': 'shirt',
            'jersey': '12',  # Jersey Short Sleeve Tee
            'heavy cotton': '6',  # Heavy Cotton Tee
            'softstyle': '145',  # Softstyle T-Shirt
            
            # Hoodies
            'hoodie': 'hoodie',
            'sweatshirt': 'hoodie',
            'hooded': 'hoodie',
            'college': '92',  # College Hoodie
            'midweight': '1525',  # Midweight Softstyle Fleece Hoodie
            'fleece': '1525',  # Midweight Softstyle Fleece Hoodie
            'supply': '499'  # Supply Hoodie
        }
        
        # First try to find specific product by ID
        for keyword, product_id_or_category in keyword_mappings.items():
            if keyword in text_lower:
                # If it's a specific product ID
                if product_id_or_category.isdigit():
                    product = self.get_product_by_id(product_id_or_category)
                    if product:
                        return {
                            'id': product_id_or_category,
                            'product': product,
                            'formatted': {
                                'title': product.get('title'),
                                'category': product.get('category')
                            }
                        }
                # If it's a category
                else:
                    products = self.get_products_by_category(product_id_or_category)
                    if products:
                        # Return the first (highest popularity) product in that category
                        first_product_id = list(products.keys())[0]
                        first_product = products[first_product_id]
                        return {
                            'id': first_product_id,
                            'product': first_product,
                            'formatted': {
                                'title': first_product.get('title'),
                                'category': first_product.get('category')
                            }
                        }
        
        # Default: return the highest popularity product (Jersey Tee)
        default_product = self.get_product_by_id('12')
        if default_product:
            return {
                'id': '12',
                'product': default_product,
                'formatted': {
                    'title': default_product.get('title'),
                    'category': default_product.get('category')
                }
            }
        
        return None
    
    def get_product_suggestions_text(self) -> str:
        """Get formatted text with product suggestions"""
        products = self.get_all_products()
        
        if not products:
            return "No products available at the moment."
        
        # Group by category
        shirts = self.get_products_by_category('shirt')
        hoodies = self.get_products_by_category('hoodie')
        
        suggestions = []
        
        if shirts:
            shirt_list = [f"• {product.get('title')}" for product in list(shirts.values())[:3]]
            suggestions.extend(shirt_list)
        
        if hoodies:
            hoodie_list = [f"• {product.get('title')}" for product in list(hoodies.values())[:3]]
            suggestions.extend(hoodie_list)
        
        return "\n".join(suggestions)
    
    def get_available_colors_for_best_products(self) -> Dict[str, List[str]]:
        """Get available colors for all products (backward compatibility)"""
        colors_by_product = {}
        for product_id in self.products_cache.keys():
            colors_by_product[product_id] = self.get_colors_for_product(product_id)
        return colors_by_product
    
    def parse_color_preferences_ai(self, text: str, logo_url: str = None) -> List[Dict]:
        """AI-powered color preference parsing with logo context"""
        from openai_service import openai_service
        
        selected_variants = []
        
        # Use AI to determine which product(s) the user is requesting
        product_match = self.find_product_by_intent_ai(text)
        
        target_products = []
        if product_match:
            # User specified a specific product
            target_products = [product_match['id']]
        else:
            # No specific product mentioned, try main products
            target_products = ['12', '6', '92']  # Jersey, Heavy Cotton, Hoodie
        
        # For each target product, use AI to find best color match
        for product_id in target_products:
            try:
                # Get available colors for this product
                available_colors = self.get_colors_for_product(product_id)
                if not available_colors:
                    continue
                
                # Get product name
                product_info = self.get_product_by_id(product_id)
                product_name = product_info.get('title', 'Product') if product_info else 'Product'
                
                # Use AI to analyze color request
                ai_result = openai_service.analyze_color_request(
                    user_request=text,
                    logo_url=logo_url or "No logo provided",
                    available_colors=available_colors,
                    product_name=product_name
                )
                
                best_color = ai_result.get('best_color_match')
                if best_color and best_color in available_colors:
                    # Find the variant for this color
                    variant = self._find_variant_by_color(product_id, best_color)
                    if variant:
                        selected_variants.append({
                            'product_id': product_id,
                            'product_name': product_name,
                            'color': best_color,
                            'variant': variant,
                            'ai_confidence': ai_result.get('confidence', 'medium'),
                            'ai_reasoning': ai_result.get('reasoning', ''),
                            'logo_colors_considered': ai_result.get('logo_colors_considered', '')
                        })
                        logger.info(f"AI selected {best_color} for {product_name}: {ai_result.get('reasoning')}")
                
            except Exception as e:
                logger.error(f"AI color analysis failed for product {product_id}: {e}")
                continue
        
        return selected_variants

    def parse_color_preferences(self, text: str) -> List[Dict]:
        """Parse color preferences from text"""
        import re
        
        selected_variants = []
        text_lower = text.lower()
        
        # Color mappings and synonyms
        color_mappings = {
            'light blue': ['Light Blue', 'Carolina Blue', 'Baby Blue', 'Sky Blue', 'Sky'],
            'aqua': ['Aqua', 'Heather Aqua', 'Carolina Blue', 'Sky Blue'],
            'carolina blue': ['Carolina Blue', 'Light Blue', 'Sky Blue'],
            'sky blue': ['Sky Blue', 'Sky', 'Carolina Blue', 'Light Blue'],
            'blue': ['Royal Blue', 'Navy Blue', 'Blue', 'Dark Blue'],
            'red': ['Red', 'Cardinal Red', 'Fire Red', 'Cherry Red', 'Canvas Red'],
            'black': ['Black', 'Jet Black'],
            'white': ['White', 'Arctic White', 'Solid White Blend'],
            'gray': ['Sport Grey', 'Athletic Heather', 'Heather Grey'],
            'grey': ['Sport Grey', 'Athletic Heather', 'Heather Grey'],
            'green': ['Forest Green', 'Kelly Green', 'Irish Green'],
            'navy': ['Navy', 'Oxford Navy', 'Heather Midnight Navy'],
            'purple': ['Purple', 'Royal Purple']
        }
        
        # Product keywords mapping to all available products
        product_keywords = {
            'jersey': '12',  # Unisex Jersey Short Sleeve Tee
            't-shirt': '6',  # Unisex Heavy Cotton Tee
            'tshirt': '6',
            'shirt': '6', 
            'heavy cotton': '6',  # Unisex Heavy Cotton Tee
            'softstyle': '145',  # Unisex Softstyle T-Shirt
            'hoodie': '92',  # Unisex College Hoodie (default)
            'college hoodie': '92',  # Unisex College Hoodie
            'supply hoodie': '499',  # Unisex Supply Hoodie
            'midweight': '1525',  # Unisex Midweight Softstyle Fleece Hoodie
            'midweight hoodie': '1525',
            'fleece hoodie': '1525',
            'softstyle fleece': '1525',
            'sweatshirt': '92'  # Default to College Hoodie
        }
        
        # Prioritize exact color matches for specific products
        priority_matches = []
        fallback_matches = []
        found_combinations = set()  # Prevent duplicates
        
        for color_key, color_options in color_mappings.items():
            if color_key in text_lower:
                for product_key, product_id in product_keywords.items():
                    if product_key in text_lower:
                        # Skip if we already found this combination
                        combo_key = f"{product_id}_{color_key}"
                        if combo_key in found_combinations:
                            continue
                        found_combinations.add(combo_key)
                        
                        # Find the best matching color variant for this product
                        product_colors = self.get_colors_for_product(product_id)
                        
                        # Try to find exact match first
                        best_color = None
                        is_exact_match = False
                        for color_option in color_options:
                            if color_option in product_colors:
                                best_color = color_option
                                is_exact_match = True
                                break
                        
                        # If no exact match, try fuzzy matching
                        if not best_color:
                            for color_option in color_options:
                                for available_color in product_colors:
                                    if color_option.lower() in available_color.lower() or available_color.lower() in color_option.lower():
                                        best_color = available_color
                                        break
                                if best_color:
                                    break
                        
                        if best_color:
                            variant = self._find_variant_by_color(product_id, best_color)
                            if variant:
                                match_info = {
                                    'product_id': product_id,
                                    'color': best_color,
                                    'variant': variant,
                                    'product_name': self.get_product_by_id(product_id).get('title', 'Unknown Product')
                                }
                                
                                # Prioritize exact color matches
                                if is_exact_match:
                                    priority_matches.append(match_info)
                                else:
                                    fallback_matches.append(match_info)
        
        # Return priority matches first, then fallbacks
        # For very specific requests, limit to the best match
        all_matches = priority_matches + fallback_matches
        
        # If user mentioned specific product + color combo, prioritize that single match
        if len(all_matches) > 1:
            # Check if they mentioned a specific product type
            specific_product = None
            if 'jersey' in text_lower and ('t-shirt' in text_lower or 'tshirt' in text_lower or 'shirt' in text_lower):
                specific_product = '12'  # Jersey Short Sleeve Tee
            elif 'jersey' in text_lower and 'hoodie' not in text_lower:
                specific_product = '12'  # Jersey Short Sleeve Tee
            elif 'hoodie' in text_lower:
                specific_product = '92'  # College Hoodie
            elif 't-shirt' in text_lower or 'tshirt' in text_lower:
                specific_product = '6'  # Heavy Cotton Tee
            
            if specific_product:
                # Find matches for that specific product
                specific_matches = [m for m in all_matches if m['product_id'] == specific_product]
                if specific_matches:
                    # Return only the first (best) match for the specific product
                    selected_variants = specific_matches[:1]
                else:
                    selected_variants = all_matches
            else:
                selected_variants = all_matches
        else:
            selected_variants = all_matches
        
        return selected_variants
    
    def format_color_selection_message(self) -> str:
        """Format color selection message (backward compatibility)"""
        products = self.get_all_products()
        if not products:
            return "No products available."
        
        # Show colors for first product as example
        first_product_id = list(products.keys())[0]
        colors = self.get_colors_for_product(first_product_id)[:10]  # First 10 colors
        color_list = ", ".join(colors)
        
        return f"Available colors include: {color_list}. Just let me know your preference!"


# Global instance for backward compatibility
product_service = ProductService()