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