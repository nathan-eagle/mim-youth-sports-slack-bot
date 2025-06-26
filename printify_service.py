import os
import requests
import logging
from typing import Dict, List, Optional
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrintifyService:
    def __init__(self):
        self.api_token = os.getenv('PRINTIFY_API_TOKEN')
        self.shop_id = os.getenv('PRINTIFY_SHOP_ID')
        self.base_url = "https://api.printify.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "User-Agent": "MiM-Youth-Sports-Bot/1.0"
        }
        
        if not self.api_token or not self.shop_id:
            raise ValueError("Missing required environment variables: PRINTIFY_API_TOKEN, PRINTIFY_SHOP_ID")

    def upload_image(self, image_url: str, filename: str) -> Dict:
        """Upload an image to Printify and return the image ID"""
        try:
            upload_data = {
                "file_name": filename,
                "url": image_url
            }
            
            response = requests.post(
                f"{self.base_url}/uploads/images.json",
                headers=self.headers,
                json=upload_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Image uploaded successfully: {result.get('id')}")
                return {
                    "success": True,
                    "image_id": result.get('id'),
                    "preview_url": result.get('preview_url')
                }
            else:
                logger.error(f"Image upload failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Upload failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Exception during image upload: {e}")
            return {"success": False, "error": str(e)}

    def upload_image_from_file(self, file_path: str, filename: str) -> Dict:
        """Upload an image from local file path to Printify"""
        try:
            # Read and encode image
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            upload_data = {
                "file_name": filename,
                "contents": image_base64
            }
            
            response = requests.post(
                f"{self.base_url}/uploads/images.json",
                headers=self.headers,
                json=upload_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Image uploaded successfully from file: {result.get('id')}")
                return {
                    "success": True,
                    "image_id": result.get('id'),
                    "preview_url": result.get('preview_url')
                }
            else:
                logger.error(f"Image upload failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Upload failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Exception during file upload: {e}")
            return {"success": False, "error": str(e)}

    def create_order(self, customer_info: Dict, line_items: List[Dict]) -> Dict:
        """Create an order directly with Printify for fulfillment"""
        try:
            order_data = {
                "external_id": f"custom-order-{customer_info.get('email', 'unknown')}",
                "label": f"Custom Order for {customer_info.get('name', 'Customer')}",
                "line_items": line_items,
                "shipping_method": 1,  # Standard shipping
                "send_shipping_notification": True,
                "address_to": {
                    "first_name": customer_info.get('first_name', ''),
                    "last_name": customer_info.get('last_name', ''),
                    "email": customer_info.get('email', ''),
                    "phone": customer_info.get('phone', ''),
                    "country": customer_info.get('country', 'US'),
                    "region": customer_info.get('state', ''),
                    "address1": customer_info.get('address1', ''),
                    "address2": customer_info.get('address2', ''),
                    "city": customer_info.get('city', ''),
                    "zip": customer_info.get('zip', '')
                }
            }
            
            response = requests.post(
                f"{self.base_url}/shops/{self.shop_id}/orders.json",
                headers=self.headers,
                json=order_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Order created successfully: {result.get('id')}")
                return {
                    "success": True,
                    "order_id": result.get('id'),
                    "status": result.get('status'),
                    "total_cost": result.get('total_cost'),
                    "total_shipping": result.get('total_shipping'),
                    "total_tax": result.get('total_tax')
                }
            else:
                logger.error(f"Order creation failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Order creation failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Exception during order creation: {e}")
            return {"success": False, "error": str(e)}

    def create_line_item_for_blueprint(self, blueprint_id: int, print_provider_id: int, 
                                     variant_id: int, image_id: str, quantity: int = 1) -> Dict:
        """Create a line item for direct order placement with custom design"""
        try:
            # Get blueprint details for print areas
            blueprint_response = requests.get(
                f"{self.base_url}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json",
                headers=self.headers
            )
            
            if blueprint_response.status_code != 200:
                return {"error": f"Failed to get blueprint variants: {blueprint_response.status_code}"}
            
            variants = blueprint_response.json()
            selected_variant = next((v for v in variants if v['id'] == variant_id), None)
            
            if not selected_variant:
                return {"error": f"Variant {variant_id} not found"}
            
            # Create line item with print areas
            line_item = {
                "print_provider_id": print_provider_id,
                "blueprint_id": blueprint_id,
                "variant_id": variant_id,
                "quantity": quantity,
                "print_areas": [
                    {
                        "position": "front",
                        "images": [
                            {
                                "id": image_id,
                                "x": 0.5,
                                "y": 0.5,
                                "scale": 1,
                                "angle": 0
                            }
                        ]
                    }
                ]
            }
            
            return {"success": True, "line_item": line_item}
            
        except Exception as e:
            logger.error(f"Exception creating line item: {e}")
            return {"success": False, "error": str(e)}

    def get_order_status(self, order_id: str) -> Dict:
        """Get the current status of an order"""
        try:
            response = requests.get(
                f"{self.base_url}/shops/{self.shop_id}/orders/{order_id}.json",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "order_id": order_id,
                    "status": result.get('status'),
                    "created_at": result.get('created_at'),
                    "total_cost": result.get('total_cost'),
                    "tracking_number": result.get('shipments', [{}])[0].get('tracking_number'),
                    "tracking_url": result.get('shipments', [{}])[0].get('tracking_url')
                }
            else:
                return {"success": False, "error": f"Failed to get order: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Exception getting order status: {e}")
            return {"success": False, "error": str(e)}

    def get_available_products(self) -> List[Dict]:
        """Get simplified product catalog for storefront display"""
        try:
            # Use existing product cache for performance
            import json
            
            try:
                with open('product_cache.json', 'r') as f:
                    cache_data = json.load(f)
                    products = cache_data.get('products', {})
                    
                    # Filter for best products and simplify for storefront
                    storefront_products = []
                    for product_id, product in products.items():
                        if 'best' in product.get('tags', []):
                            storefront_products.append({
                                'id': product['id'],
                                'title': product['title'],
                                'description': product.get('description', ''),
                                'type': product.get('type', 'apparel'),
                                'base_price': product.get('base_price', 0),
                                'image_url': product.get('image_url', ''),
                                'blueprint_id': product.get('blueprint_id'),
                                'print_provider_id': product.get('print_provider_id'),
                                'variants': product.get('variants', [])
                            })
                    
                    return storefront_products
                    
            except FileNotFoundError:
                logger.warning("Product cache not found, returning empty list")
                return []
                
        except Exception as e:
            logger.error(f"Exception getting products: {e}")
            return []

    def create_product_design(self, blueprint_id: int, print_provider_id: int, 
                            variant_id: int, image_id: str, product_title: str = None) -> Dict:
        """Create a product design for mockup generation (no full product creation)"""
        try:
            # Get all available variants for this blueprint and print provider
            all_variant_ids = self._get_all_variant_ids_for_blueprint(blueprint_id, print_provider_id)
            
            # If we couldn't get variants from API, use a fallback approach
            if not all_variant_ids:
                logger.warning(f"Could not get variants for blueprint {blueprint_id}, provider {print_provider_id}. Using single variant.")
                all_variant_ids = [variant_id]
            
            # Create temporary product for mockup generation
            design_data = {
                "title": product_title or "Custom Team Product",
                "description": "Custom youth sports team merchandise with uploaded logo",
                "blueprint_id": blueprint_id,
                "print_provider_id": print_provider_id,
                "variants": [
                    {
                        "id": variant_id,
                        "price": 2000,  # Temporary price for mockup
                        "is_enabled": True
                    }
                ],
                "print_areas": [
                    {
                        "variant_ids": all_variant_ids,  # Include ALL available variants
                        "placeholders": [
                            {
                                "position": "front",
                                "images": [
                                    {
                                        "id": image_id,
                                        "x": 0.5,  # Center horizontally
                                        "y": 0.5,  # Center vertically
                                        "scale": 0.6,  # 60% of available area
                                        "angle": 0
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            # Create temporary product in Printify for mockup generation
            response = requests.post(
                f"{self.base_url}/shops/{self.shop_id}/products.json",
                headers=self.headers,
                json=design_data
            )
            
            if response.status_code == 200:
                product_result = response.json()
                product_id = product_result.get('id')
                
                logger.info(f"Created temporary product for mockup: {product_id}")
                
                # Generate mockup from the created product
                mockup_result = self._get_product_mockup(product_id)
                
                # Delete the temporary product (we only needed it for mockup)
                self._delete_temporary_product(product_id)
                
                return {
                    "success": True,
                    "mockup_url": mockup_result.get("mockup_url"),
                    "product_title": design_data["title"],
                    "blueprint_id": blueprint_id,
                    "print_provider_id": print_provider_id,
                    "variant_id": variant_id,
                    "image_id": image_id
                }
            else:
                logger.error(f"Failed to create design: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Design creation failed: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Exception creating product design: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_product_mockup(self, product_id: str) -> Dict:
        """Get mockup images from a created product"""
        try:
            response = requests.get(
                f"{self.base_url}/shops/{self.shop_id}/products/{product_id}.json",
                headers=self.headers
            )
            
            if response.status_code == 200:
                product_data = response.json()
                images = product_data.get('images', [])
                
                # Find the default front-facing mockup image
                for image in images:
                    if image.get('is_default', False) and image.get('position') == 'front':
                        return {"mockup_url": image.get('src')}
                
                # Fallback: use first available image
                if images:
                    return {"mockup_url": images[0].get('src')}
                
                return {"mockup_url": None}
            else:
                logger.warning(f"Failed to get product mockup: {response.status_code}")
                return {"mockup_url": None}
                
        except Exception as e:
            logger.error(f"Error getting product mockup: {e}")
            return {"mockup_url": None}
    
    def _get_all_variant_ids_for_blueprint(self, blueprint_id: int, print_provider_id: int) -> List[int]:
        """Get all available variant IDs for a specific blueprint and print provider combination"""
        try:
            response = requests.get(
                f"{self.base_url}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json",
                headers=self.headers
            )
            
            if response.status_code == 200:
                variants = response.json()
                variant_ids = [variant['id'] for variant in variants if variant.get('available', True)]
                logger.info(f"Found {len(variant_ids)} variants for blueprint {blueprint_id}, provider {print_provider_id}")
                return variant_ids
            else:
                logger.warning(f"Failed to get variants: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Exception getting variants: {e}")
            return []

    def _delete_temporary_product(self, product_id: str):
        """Delete temporary product after getting mockup"""
        try:
            response = requests.delete(
                f"{self.base_url}/shops/{self.shop_id}/products/{product_id}.json",
                headers=self.headers
            )
            
            if response.status_code == 200:
                logger.info(f"Deleted temporary product: {product_id}")
            else:
                logger.warning(f"Failed to delete temporary product {product_id}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error deleting temporary product: {e}")

# Global instance (only create if environment variables are available)
printify_service = None
try:
    if os.getenv('PRINTIFY_API_TOKEN') and os.getenv('PRINTIFY_SHOP_ID'):
        printify_service = PrintifyService()
except Exception:
    # Will be None if env vars not available - that's ok for testing
    pass 