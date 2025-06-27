#!/usr/bin/env python3
"""
Database Service for Custom Drop
Handles product designs and order management
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self, storage_file: str = "drop_data.json", supabase_url: str = None, supabase_key: str = None):
        """Initialize database service with file-based storage or Supabase"""
        self.storage_file = storage_file
        self.supabase = None
        
        # Initialize Supabase if credentials provided
        if supabase_url and supabase_key:
            try:
                from supabase import create_client
                self.supabase = create_client(supabase_url, supabase_key)
                logger.info("Connected to Supabase database")
            except ImportError:
                logger.warning("Supabase not available, falling back to file storage")
                self.supabase = None
        
        # Fallback to JSON files if no Supabase
        if not self.supabase:
            self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from storage file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "product_designs": {},
                    "customer_orders": {},
                    "order_items": {},
                    "shipping_addresses": {}
                }
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return {
                "product_designs": {},
                "customer_orders": {},
                "order_items": {},
                "shipping_addresses": {}
            }
    
    def _save_data(self):
        """Save data to storage file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            logger.debug("Data saved successfully")
        except Exception as e:
            logger.error(f"Error saving data: {e}")
    
    def save_product_design(self, design_data: Dict) -> str:
        """Save a product design from Slack bot"""
        try:
            design_id = str(uuid.uuid4())
            
            product_design = {
                "id": design_id,
                "name": design_data.get("name", "Custom Team Product"),
                "description": design_data.get("description", "Custom youth sports team merchandise"),
                "blueprint_id": design_data["blueprint_id"],
                "print_provider_id": design_data["print_provider_id"],
                "team_logo_image_id": design_data["team_logo_image_id"],
                "mockup_image_url": design_data.get("mockup_image_url"),
                "base_price": design_data.get("base_price", 20.00),
                "markup_percentage": design_data.get("markup_percentage", 50.0),
                "created_at": datetime.now().isoformat(),
                "created_by": design_data.get("created_by", "slack_user"),
                "status": "active",
                "team_info": design_data.get("team_info", {}),
                "product_type": design_data.get("product_type", "apparel")
            }
            
            if self.supabase:
                # Save to Supabase
                result = self.supabase.table("product_designs").insert(product_design).execute()
                if result.data:
                    logger.info(f"Saved product design to Supabase: {design_id}")
                    return design_id
                else:
                    raise Exception("Failed to save to Supabase")
            else:
                # Save to JSON file
                self.data["product_designs"][design_id] = product_design
                self._save_data()
                logger.info(f"Saved product design to file: {design_id}")
                return design_id
            
        except Exception as e:
            logger.error(f"Error saving product design: {e}")
            raise e
    
    def get_product_design(self, design_id: str) -> Optional[Dict]:
        """Get a product design by ID"""
        try:
            if self.supabase:
                # Query Supabase first
                result = self.supabase.table("product_designs").select("*").eq("id", design_id).execute()
                if result.data and len(result.data) > 0:
                    logger.info(f"Retrieved product design from Supabase: {design_id}")
                    return result.data[0]
                else:
                    logger.warning(f"Product design {design_id} not found in Supabase")
                    return None
            else:
                # Fallback to JSON file
                return self.data["product_designs"].get(design_id)
        except Exception as e:
            logger.error(f"Error getting product design {design_id}: {e}")
            return None
    
    def get_active_product_designs(self) -> List[Dict]:
        """Get all active product designs"""
        try:
            designs = []
            for design in self.data["product_designs"].values():
                if design.get("status") == "active":
                    designs.append(design)
            return designs
        except Exception as e:
            logger.error(f"Error getting active designs: {e}")
            return []
    
    def create_customer_order(self, order_data: Dict) -> str:
        """Create a new customer order"""
        try:
            order_id = str(uuid.uuid4())
            
            customer_order = {
                "id": order_id,
                "email": order_data["email"],
                "first_name": order_data.get("first_name", ""),
                "last_name": order_data.get("last_name", ""),
                "phone": order_data.get("phone", ""),
                "total_amount": order_data["total_amount"],
                "payment_status": "pending",
                "stripe_payment_intent_id": order_data.get("stripe_payment_intent_id"),
                "fulfillment_status": "pending",
                "printify_order_id": None,
                "created_at": datetime.now().isoformat()
            }
            
            self.data["customer_orders"][order_id] = customer_order
            self._save_data()
            
            logger.info(f"Created customer order: {order_id}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error creating customer order: {e}")
            raise e
    
    def update_order_payment_status(self, order_id: str, payment_status: str, stripe_payment_intent_id: str = None) -> bool:
        """Update order payment status"""
        try:
            if order_id in self.data["customer_orders"]:
                self.data["customer_orders"][order_id]["payment_status"] = payment_status
                if stripe_payment_intent_id:
                    self.data["customer_orders"][order_id]["stripe_payment_intent_id"] = stripe_payment_intent_id
                self._save_data()
                logger.info(f"Updated payment status for order {order_id}: {payment_status}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            return False
    
    def update_order_printify_id(self, order_id: str, printify_order_id: str) -> bool:
        """Update order with Printify order ID after fulfillment"""
        try:
            if order_id in self.data["customer_orders"]:
                self.data["customer_orders"][order_id]["printify_order_id"] = printify_order_id
                self.data["customer_orders"][order_id]["fulfillment_status"] = "processing"
                self._save_data()
                logger.info(f"Updated order {order_id} with Printify ID: {printify_order_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating Printify order ID: {e}")
            return False

    def get_order_by_id(self, order_id: str) -> dict:
        """Get order details by order ID"""
        try:
            return self.data["customer_orders"].get(order_id)
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None
    
    def add_order_item(self, order_id: str, item_data: Dict) -> str:
        """Add an item to an order"""
        try:
            item_id = str(uuid.uuid4())
            
            order_item = {
                "id": item_id,
                "order_id": order_id,
                "product_design_id": item_data["product_design_id"],
                "variant_id": item_data.get("variant_id"),
                "quantity": item_data["quantity"],
                "unit_price": item_data["unit_price"],
                "total_price": item_data["quantity"] * item_data["unit_price"]
            }
            
            self.data["order_items"][item_id] = order_item
            self._save_data()
            
            logger.info(f"Added order item: {item_id} to order {order_id}")
            return item_id
            
        except Exception as e:
            logger.error(f"Error adding order item: {e}")
            raise e
    
    def save_shipping_address(self, order_id: str, address_data: Dict) -> str:
        """Save shipping address for an order"""
        try:
            address_id = str(uuid.uuid4())
            
            shipping_address = {
                "id": address_id,
                "order_id": order_id,
                "first_name": address_data.get("first_name", ""),
                "last_name": address_data.get("last_name", ""),
                "address1": address_data.get("address1", ""),
                "address2": address_data.get("address2", ""),
                "city": address_data.get("city", ""),
                "state": address_data.get("state", ""),
                "zip": address_data.get("zip", ""),
                "country": address_data.get("country", "US")
            }
            
            self.data["shipping_addresses"][address_id] = shipping_address
            self._save_data()
            
            logger.info(f"Saved shipping address: {address_id} for order {order_id}")
            return address_id
            
        except Exception as e:
            logger.error(f"Error saving shipping address: {e}")
            raise e
    
    def get_order_with_items(self, order_id: str) -> Optional[Dict]:
        """Get order with all associated items and shipping address"""
        try:
            order = self.data["customer_orders"].get(order_id)
            if not order:
                return None
            
            # Get order items
            order_items = []
            for item in self.data["order_items"].values():
                if item["order_id"] == order_id:
                    # Enrich with product design info
                    design = self.get_product_design(item["product_design_id"])
                    item["product_design"] = design
                    order_items.append(item)
            
            # Get shipping address
            shipping_address = None
            for address in self.data["shipping_addresses"].values():
                if address["order_id"] == order_id:
                    shipping_address = address
                    break
            
            return {
                **order,
                "items": order_items,
                "shipping_address": shipping_address
            }
            
        except Exception as e:
            logger.error(f"Error getting order with items: {e}")
            return None
    
    def generate_drop_url(self, design_id: str, base_domain: str = "https://mim-drop.vercel.app") -> str:
        """Generate drop URL for a product design"""
        return f"{base_domain}/design/{design_id}"

# Global instance - will be initialized with Supabase credentials if available
database_service = DatabaseService(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_SERVICE_KEY")
) 