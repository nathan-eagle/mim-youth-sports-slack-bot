#!/usr/bin/env python3
"""
Simple fallback database service for when Supabase isn't set up
"""

import logging
from typing import Dict, Optional
import uuid

logger = logging.getLogger(__name__)

class SimpleDatabaseService:
    """Simple in-memory database service with same interface"""
    
    def __init__(self):
        self.designs = {}
        logger.info("Using in-memory database fallback")
    
    def save_product_design(self, design_data: Dict) -> str:
        """Save product design in-memory"""
        design_id = str(uuid.uuid4())
        self.designs[design_id] = design_data
        logger.info(f"Saved product design in-memory: {design_id}")
        return design_id
    
    def get_product_design(self, design_id: str) -> Optional[Dict]:
        """Get product design"""
        return self.designs.get(design_id)
    
    def get_drop_base_url(self) -> str:
        """Get the base URL for the drop storefront"""
        return "https://mim-drop.vercel.app"
    
    def find_existing_product_design(self, blueprint_id: int, print_provider_id: int, 
                                   image_id: str, variant_id: int) -> Optional[Dict]:
        """Find existing design - always return None for now"""
        return None

# Try to use real database service, fall back to simple one
try:
    from database_service import database_service
    # Test if it works
    database_service.get_drop_base_url()
    logger.info("Using real database service")
except Exception as e:
    logger.warning(f"Database service failed, using fallback: {e}")
    database_service = SimpleDatabaseService()