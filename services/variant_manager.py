"""
Product variant management for colors, sizes, and options
"""
import logging
from typing import Dict, List, Optional, Tuple
from .product_service import product_service

logger = logging.getLogger(__name__)


class VariantManager:
    """Manages product variants (colors, sizes, options)"""
    
    def __init__(self):
        self.product_service = product_service
    
    def get_available_colors(self, product_id: str) -> List[str]:
        """Get available colors for a product"""
        product = self.product_service.get_product_by_id(product_id)
        
        if not product:
            return []
        
        return product.get('available_colors', [])
    
    def get_available_sizes(self, product_id: str) -> List[str]:
        """Get available sizes for a product"""
        product = self.product_service.get_product_by_id(product_id)
        
        if not product:
            return []
        
        return product.get('available_sizes', [])
    
    def get_product_variants(self, product_id: str) -> List[Dict]:
        """Get all variants for a product"""
        product = self.product_service.get_product_by_id(product_id)
        
        if not product:
            return []
        
        return product.get('variants', [])
    
    def find_variant_by_color(self, product_id: str, color: str) -> Optional[Dict]:
        """Find variant by color (fuzzy match)"""
        variants = self.get_product_variants(product_id)
        
        if not variants:
            return None
        
        color_lower = color.lower()
        
        # First try exact match
        for variant in variants:
            variant_color = variant.get('color', '').lower()
            if variant_color == color_lower:
                return variant
        
        # Then try partial match
        for variant in variants:
            variant_color = variant.get('color', '').lower()
            if color_lower in variant_color or variant_color in color_lower:
                return variant
        
        return None
    
    def find_variant_by_color_and_size(self, product_id: str, color: str, size: str) -> Optional[Dict]:
        """Find variant by both color and size"""
        variants = self.get_product_variants(product_id)
        
        if not variants:
            return None
        
        color_lower = color.lower()
        size_lower = size.lower()
        
        # Try exact match first
        for variant in variants:
            variant_color = variant.get('color', '').lower()
            variant_size = variant.get('size', '').lower()
            
            if variant_color == color_lower and variant_size == size_lower:
                return variant
        
        # Try color match with any size
        for variant in variants:
            variant_color = variant.get('color', '').lower()
            if variant_color == color_lower:
                return variant
        
        return None
    
    def get_best_variant_for_color(self, product_id: str, requested_color: str) -> Optional[Dict]:
        """Get the best variant for a requested color"""
        matching_variant = self.find_variant_by_color(product_id, requested_color)
        
        if matching_variant:
            return matching_variant
        
        # If no match, return a default variant
        variants = self.get_product_variants(product_id)
        if variants:
            # Prefer common sizes like M, L for shirts
            preferred_sizes = ['M', 'L', 'Medium', 'Large', 'One Size']
            
            for size in preferred_sizes:
                for variant in variants:
                    if variant.get('size', '').upper() == size.upper():
                        return variant
            
            # Return first variant as fallback
            return variants[0]
        
        return None
    
    def get_color_alternatives(self, product_id: str, exclude_color: str = None) -> List[str]:
        """Get alternative colors for a product"""
        colors = self.get_available_colors(product_id)
        
        if exclude_color:
            exclude_lower = exclude_color.lower()
            colors = [c for c in colors if c.lower() != exclude_lower]
        
        return colors
    
    def validate_color_availability(self, product_id: str, color: str) -> Tuple[bool, Optional[str]]:
        """Validate if a color is available for a product"""
        available_colors = self.get_available_colors(product_id)
        
        if not available_colors:
            return False, None
        
        color_lower = color.lower()
        
        # Check exact match
        for available_color in available_colors:
            if available_color.lower() == color_lower:
                return True, available_color
        
        # Check partial match
        for available_color in available_colors:
            if color_lower in available_color.lower() or available_color.lower() in color_lower:
                return True, available_color
        
        return False, None
    
    def get_variant_price(self, product_id: str, variant_id: str) -> Optional[float]:
        """Get price for a specific variant"""
        variants = self.get_product_variants(product_id)
        
        for variant in variants:
            if str(variant.get('id')) == str(variant_id):
                return variant.get('price')
        
        return None
    
    def get_cheapest_variant(self, product_id: str) -> Optional[Dict]:
        """Get the cheapest variant for a product"""
        variants = self.get_product_variants(product_id)
        
        if not variants:
            return None
        
        return min(variants, key=lambda v: v.get('price', float('inf')))
    
    def group_variants_by_color(self, product_id: str) -> Dict[str, List[Dict]]:
        """Group variants by color"""
        variants = self.get_product_variants(product_id)
        grouped = {}
        
        for variant in variants:
            color = variant.get('color', 'Unknown')
            if color not in grouped:
                grouped[color] = []
            grouped[color].append(variant)
        
        return grouped
    
    def get_size_options_for_color(self, product_id: str, color: str) -> List[str]:
        """Get available sizes for a specific color"""
        variants = self.get_product_variants(product_id)
        sizes = []
        
        color_lower = color.lower()
        
        for variant in variants:
            variant_color = variant.get('color', '').lower()
            if variant_color == color_lower:
                size = variant.get('size')
                if size and size not in sizes:
                    sizes.append(size)
        
        return sizes
    
    def format_variant_options_message(self, product_id: str, current_color: str = None) -> str:
        """Format variant options into a readable message"""
        product = self.product_service.get_product_by_id(product_id)
        
        if not product:
            return "Product not found."
        
        colors = self.get_available_colors(product_id)
        sizes = self.get_available_sizes(product_id)
        
        message_parts = []
        
        if colors:
            if current_color:
                other_colors = [c for c in colors if c.lower() != current_color.lower()]
                if other_colors:
                    message_parts.append(f"*Also available in:* {', '.join(other_colors[:8])}")
            else:
                message_parts.append(f"*Available colors:* {', '.join(colors[:8])}")
        
        if sizes and len(sizes) > 1:
            message_parts.append(f"*Available sizes:* {', '.join(sizes)}")
        
        return "\n".join(message_parts) if message_parts else ""


# Create singleton instance
variant_manager = VariantManager()