#!/usr/bin/env python3
"""
Supabase-only Database Service for Custom Drop
Handles product designs and order management
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional
from supabase import create_client, Client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseService:
    """Supabase-only database service for Vercel compatibility"""
    
    def __init__(self):
        """Initialize Supabase database service"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Connected to Supabase database")
    
    def save_product_design(self, design_data: Dict) -> str:
        """Save a product design to Supabase"""
        try:
            design_id = str(uuid.uuid4())
            
            # Prepare design data for Supabase
            supabase_design = {
                "id": design_id,
                "product_name": design_data.get("product_name"),
                "product_id": design_data.get("product_id"),
                "variant_id": design_data.get("variant_id"),
                "color": design_data.get("color"),
                "size": design_data.get("size"),
                "mockup_url": design_data.get("mockup_url"),
                "logo_url": design_data.get("logo_url"),
                "price": design_data.get("price", 25.00),
                "printify_data": design_data.get("printify_data", {}),
                "created_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            # Insert into Supabase
            result = self.supabase.table("product_designs").insert(supabase_design).execute()
            
            if result.data:
                logger.info(f"Saved product design to Supabase: {design_id}")
                return design_id
            else:
                raise Exception("Failed to save design to Supabase")
                
        except Exception as e:
            logger.error(f"Error saving product design: {e}")
            raise
    
    def get_product_design(self, design_id: str) -> Optional[Dict]:
        """Get a product design by ID"""
        try:
            result = self.supabase.table("product_designs").select("*").eq("id", design_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                logger.warning(f"Product design not found: {design_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting product design: {e}")
            return None
    
    def save_customer_order(self, order_data: Dict) -> str:
        """Save a customer order to Supabase"""
        try:
            order_id = str(uuid.uuid4())
            
            # Prepare order data
            supabase_order = {
                "id": order_id,
                "customer_email": order_data.get("customer_email"),
                "customer_name": order_data.get("customer_name"),
                "shipping_address": order_data.get("shipping_address", {}),
                "total_amount": order_data.get("total_amount"),
                "stripe_payment_intent": order_data.get("stripe_payment_intent"),
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            # Insert into Supabase
            result = self.supabase.table("customer_orders").insert(supabase_order).execute()
            
            if result.data:
                logger.info(f"Saved customer order to Supabase: {order_id}")
                return order_id
            else:
                raise Exception("Failed to save order to Supabase")
                
        except Exception as e:
            logger.error(f"Error saving customer order: {e}")
            raise
    
    def add_order_item(self, order_id: str, design_id: str, quantity: int = 1, 
                      custom_size: str = None) -> str:
        """Add an item to an order"""
        try:
            item_id = str(uuid.uuid4())
            
            # Get design info
            design = self.get_product_design(design_id)
            if not design:
                raise Exception(f"Design not found: {design_id}")
            
            # Prepare order item data
            order_item = {
                "id": item_id,
                "order_id": order_id,
                "design_id": design_id,
                "product_name": design.get("product_name"),
                "color": design.get("color"),
                "size": custom_size or design.get("size"),
                "quantity": quantity,
                "unit_price": design.get("price", 25.00),
                "total_price": (design.get("price", 25.00) * quantity),
                "created_at": datetime.now().isoformat()
            }
            
            # Insert into Supabase
            result = self.supabase.table("order_items").insert(order_item).execute()
            
            if result.data:
                logger.info(f"Added order item to Supabase: {item_id}")
                return item_id
            else:
                raise Exception("Failed to add order item to Supabase")
                
        except Exception as e:
            logger.error(f"Error adding order item: {e}")
            raise
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order with items"""
        try:
            # Get order details
            order_result = self.supabase.table("customer_orders").select("*").eq("id", order_id).execute()
            
            if not order_result.data:
                return None
            
            order = order_result.data[0]
            
            # Get order items
            items_result = self.supabase.table("order_items").select("*").eq("order_id", order_id).execute()
            order["items"] = items_result.data or []
            
            return order
            
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return None
    
    def update_order_status(self, order_id: str, status: str, 
                           printify_order_id: str = None) -> bool:
        """Update order status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            
            if printify_order_id:
                update_data["printify_order_id"] = printify_order_id
            
            result = self.supabase.table("customer_orders").update(update_data).eq("id", order_id).execute()
            
            if result.data:
                logger.info(f"Updated order status: {order_id} -> {status}")
                return True
            else:
                logger.warning(f"Failed to update order status: {order_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            return False
    
    def get_drop_base_url(self) -> str:
        """Get the base URL for the drop storefront"""
        # This should be set based on your deployment
        drop_url = os.getenv('DROP_BASE_URL', 'https://mim-drop.vercel.app')
        return drop_url
    
    def get_recent_designs(self, limit: int = 10) -> List[Dict]:
        """Get recent product designs"""
        try:
            result = self.supabase.table("product_designs").select("*").order("created_at", desc=True).limit(limit).execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting recent designs: {e}")
            return []
    
    def get_pending_orders(self) -> List[Dict]:
        """Get orders that need fulfillment"""
        try:
            result = self.supabase.table("customer_orders").select("*").eq("status", "pending").execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting pending orders: {e}")
            return []
    
    def cleanup_old_designs(self, days: int = 30):
        """Clean up old designs (optional)"""
        try:
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            result = self.supabase.table("product_designs").delete().lt("created_at", cutoff_date).execute()
            logger.info(f"Cleaned up designs older than {days} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old designs: {e}")


# Create singleton instance
database_service = DatabaseService()