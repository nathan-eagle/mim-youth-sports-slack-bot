"""
Compatibility wrapper for product_service
Redirects to the new modular services
"""
import logging
from services.product_service import ProductService as NewProductService
from services.product_selector import product_selector
from services.variant_manager import variant_manager

logger = logging.getLogger(__name__)


class ProductService:
    """Compatibility wrapper for the old ProductService API"""
    
    def __init__(self):
        self._service = NewProductService()
        self._selector = product_selector
        self._variant_manager = variant_manager
    
    # Core methods - delegate to new service
    def get_all_products(self):
        return self._service.get_all_products()
    
    def get_products_by_category(self, category):
        return {str(i): p for i, p in enumerate(self._service.get_products_by_category(category))}
    
    def get_products_by_type(self, product_type):
        return self._service.get_products_by_type(product_type)
    
    def get_product_by_id(self, product_id):
        return self._service.get_product_by_id(product_id)
    
    def load_printify_choice_products(self):
        return self._service.load_printify_choice_products()
    
    # Variant methods - delegate to variant manager
    def get_product_variants(self, product_id):
        return self._variant_manager.get_product_variants(product_id)
    
    def get_colors_for_product(self, product_id):
        return self._variant_manager.get_available_colors(product_id)
    
    def get_sizes_for_product(self, product_id):
        return self._variant_manager.get_available_sizes(product_id)
    
    def find_variant_by_options(self, product_id, color, size):
        return self._variant_manager.find_variant_by_color_and_size(product_id, color, size)
    
    # Legacy methods - simplified implementations
    def get_best_products(self):
        """Get default products (t-shirt and hoodie)"""
        defaults = self._service.get_default_products()
        result = {}
        for i, product in enumerate(defaults):
            result[str(product['id'])] = product
        return result
    
    def validate_product_data(self, product_id):
        """Validate product data"""
        product = self._service.get_product_by_id(product_id)
        return {
            'exists': product is not None,
            'has_variants': bool(product and product.get('variants')),
            'has_colors': bool(product and product.get('available_colors')),
            'is_printify_choice': bool(product and product.get('is_printify_choice'))
        }


# Create singleton instance for compatibility
product_service = ProductService()