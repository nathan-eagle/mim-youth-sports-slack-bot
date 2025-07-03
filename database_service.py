#!/usr/bin/env python3
"""
Simple database service that works without database persistence
"""

import logging
from typing import Dict, Optional
import uuid

logger = logging.getLogger(__name__)

class SimpleDatabaseService:
    """Simple database service with fallback behavior"""
    
    def __init__(self):
        # Don't try to connect to database - just use in-memory
        self.designs = {}
        logger.info("Using in-memory design storage")
    
    def save_product_design(self, design_data: Dict) -> str:
        """Save product design in-memory"""
        design_id = str(uuid.uuid4())
        self.designs[design_id] = design_data
        logger.info(f"Saved product design in-memory: {design_id}")
        return design_id
    
    def get_product_design(self, design_id: str) -> Optional[Dict]:
        """Get product design"""
        return self.designs.get(design_id)
    
    def find_existing_product_design(self, blueprint_id: int, print_provider_id: int, 
                                   image_id: str, variant_id: int) -> Optional[Dict]:
        """Find existing design - always return None for now"""
        return None

# Global instance
database_service = SimpleDatabaseService()