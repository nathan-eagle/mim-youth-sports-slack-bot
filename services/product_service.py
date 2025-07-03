"""
Product service for managing Printify Choice products
"""
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProductService:
    """Manages product catalog and basic operations"""
    
    def __init__(self, cache_file_path: str = "printifychoicecache.json"):
        self.cache_file_path = cache_file_path
        self.products_cache = {}
        self.cache_metadata = {}
        self.categories = {}
        
        self._load_cache()
    
    def _load_cache(self) -> bool:
        """Load Printify Choice products cache"""
        try:
            with open(self.cache_file_path, 'r') as f:
                data = json.load(f)
                self.products_cache = data.get('products', {})
                self.cache_metadata = data.get('metadata', {})
                self.categories = data.get('categories', {})
                
                logger.info(f"Loaded Printify Choice cache: {len(self.products_cache)} products, {len(self.categories)} categories")
                return True
        except Exception as e:
            logger.error(f"Failed to load product cache from {self.cache_file_path}: {e}")
            return False
    
    def load_printify_choice_products(self) -> Optional[Dict]:
        """Load and return the full Printify Choice cache"""
        try:
            with open(self.cache_file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Printify Choice products: {e}")
            return None
    
    def get_all_products(self) -> Dict:
        """Get all cached products"""
        return self.products_cache
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Get products by category, sorted by popularity"""
        matching_products = [
            product for product in self.products_cache.values()
            if product.get('category') == category
        ]
        
        # Sort by popularity score
        matching_products.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
        return matching_products
    
    def get_products_by_type(self, product_type: str) -> List[Dict]:
        """Alias for get_products_by_category for compatibility"""
        return self.get_products_by_category(product_type)
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get specific product by ID"""
        return self.products_cache.get(str(product_id))
    
    def get_best_products_by_category(self) -> Dict[str, List[Dict]]:
        """Get top 3 products per category"""
        best_by_category = {}
        
        for category in self.categories.keys():
            products = self.get_products_by_category(category)
            best_by_category[category] = products[:3]  # Top 3 by popularity
        
        return best_by_category
    
    def get_default_products(self) -> List[Dict]:
        """Get default products to show (t-shirt and hoodie)"""
        default_products = []
        
        # Get best t-shirt
        tshirts = self.get_products_by_category('tshirt')
        if tshirts:
            default_products.append(tshirts[0])
        
        # Get best hoodie
        hoodies = self.get_products_by_category('hoodie')
        if hoodies:
            default_products.append(hoodies[0])
        
        return default_products
    
    def get_available_categories(self) -> List[str]:
        """Get list of available product categories"""
        return list(self.categories.keys())
    
    def search_products(self, query: str) -> List[Dict]:
        """Search products by title or description"""
        query_lower = query.lower()
        results = []
        
        for product in self.products_cache.values():
            title_lower = product.get('title', '').lower()
            description_lower = product.get('description', '').lower()
            
            if query_lower in title_lower or query_lower in description_lower:
                results.append(product)
        
        # Sort by popularity
        results.sort(key=lambda x: x.get('popularity_score', 0), reverse=True)
        return results
    
    def get_category_summary(self) -> Dict[str, int]:
        """Get summary of products per category"""
        return self.categories.copy()


# Create singleton instance
product_service = ProductService()