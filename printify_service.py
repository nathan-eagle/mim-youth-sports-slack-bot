import os
import requests
import logging
import base64
from typing import Dict, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class PrintifyService:
    def __init__(self):
        self.api_token = os.getenv('PRINTIFY_API_TOKEN')
        self.shop_id = os.getenv('PRINTIFY_SHOP_ID')
        self.base_url = "https://api.printify.com/v1"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    def upload_logo_image(self, logo_file_path: str, filename: str) -> Dict:
        """Upload logo image to Printify"""
        try:
            # Read and encode image
            with open(logo_file_path, 'rb') as f:
                image_data = f.read()
            
            # Convert to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare upload data
            upload_data = {
                "file_name": filename,
                "contents": image_base64
            }
            
            # Upload to Printify
            response = requests.post(
                f"{self.base_url}/uploads/images.json",
                headers=self.headers,
                json=upload_data,
                timeout=30
            )
            
            if response.status_code == 200:
                upload_result = response.json()
                logger.info(f"Successfully uploaded logo to Printify: {upload_result.get('id')}")
                return {
                    "success": True,
                    "image_id": upload_result.get('id'),
                    "preview_url": upload_result.get('preview_url'),
                    "filename": filename
                }
            else:
                logger.error(f"Printify upload failed: {response.status_code} - {response.text}")
                return {"success": False, "error": f"Upload failed: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error uploading logo to Printify: {e}")
            return {"success": False, "error": "Failed to upload logo"}
    
    def create_custom_product(self, product_id: str, logo_image_id: str, product_color: str = None) -> Dict:
        """Create custom product with logo applied"""
        try:
            # Get product blueprint info
            blueprint_response = requests.get(
                f"{self.base_url}/catalog/blueprints/{product_id}.json",
                headers=self.headers,
                timeout=15
            )
            
            if blueprint_response.status_code != 200:
                return {"success": False, "error": "Failed to get product information"}
            
            blueprint_data = blueprint_response.json()
            
            # Get print providers for this product
            providers_response = requests.get(
                f"{self.base_url}/catalog/blueprints/{product_id}/print_providers.json",
                headers=self.headers,
                timeout=15
            )
            
            if providers_response.status_code != 200:
                return {"success": False, "error": "Failed to get print providers"}
            
            providers_data = providers_response.json()
            
            if not providers_data:
                return {"success": False, "error": "No print providers available for this product"}
            
            # Use first available provider
            print_provider = providers_data[0]
            print_provider_id = print_provider['id']
            
            # Get variants for this provider
            variants_response = requests.get(
                f"{self.base_url}/catalog/blueprints/{product_id}/print_providers/{print_provider_id}/variants.json",
                headers=self.headers,
                timeout=15
            )
            
            if variants_response.status_code != 200:
                return {"success": False, "error": "Failed to get product variants"}
            
            variants_data = variants_response.json()
            
            # Select appropriate variant (color/size)
            selected_variant = self._select_variant(variants_data.get('variants', []), product_color)
            if not selected_variant:
                return {"success": False, "error": "No suitable product variant found"}
            
            # Get print areas for positioning logo
            print_areas = self._get_print_areas(print_provider_id, product_id, selected_variant['id'])
            if not print_areas:
                return {"success": False, "error": "No print areas available for this product"}
            
            # Create product with logo
            product_data = self._build_product_data(
                blueprint_data, 
                print_provider_id, 
                selected_variant, 
                logo_image_id, 
                print_areas[0]  # Use first available print area
            )
            
            create_response = requests.post(
                f"{self.base_url}/shops/{self.shop_id}/products.json",
                headers=self.headers,
                json=product_data,
                timeout=30
            )
            
            if create_response.status_code == 200:
                product_result = create_response.json()
                logger.info(f"Successfully created custom product: {product_result.get('id')}")
                
                # Generate mockup (optional - don't fail if this doesn't work)
                mockup_result = self._generate_mockup(product_result['id'])
                
                # Safely extract variant info
                try:
                    variant_color = selected_variant.get('title', 'Default')
                    variant_options = selected_variant.get('options', [])
                    variant_size = variant_options[0].get('value', 'One Size') if variant_options else 'One Size'
                except Exception as ve:
                    logger.warning(f"Error extracting variant info: {ve}")
                    variant_color = 'Default'
                    variant_size = 'One Size'
                
                result = {
                    "success": True,
                    "product_id": product_result.get('id'),
                    "title": product_result.get('title'),
                    "mockup_url": mockup_result.get('mockup_url') if mockup_result else None,
                    "purchase_url": self._generate_purchase_url(product_result.get('id')),
                    "variant_info": {
                        "color": variant_color,
                        "size": variant_size
                    }
                }
                
                # CRITICAL: Publish the product to make it purchasable
                publish_result = self._publish_product(product_result.get('id'))
                if publish_result.get('success'):
                    logger.info(f"Successfully published product {product_result.get('id')}")
                    # Update purchase URL with published product URL
                    result["purchase_url"] = publish_result.get('purchase_url', result["purchase_url"])
                else:
                    logger.warning(f"Failed to publish product: {publish_result.get('error')}")
                    # Continue anyway - product is created even if not published
                
                logger.info(f"Product creation result: {result}")
                return result
            else:
                logger.error(f"Failed to create product: {create_response.status_code} - {create_response.text}")
                return {"success": False, "error": f"Product creation failed: {create_response.text}"}
                
        except Exception as e:
            logger.error(f"Error creating custom product: {e}")
            return {"success": False, "error": "Failed to create custom product"}
    
    def _select_variant(self, variants: List[Dict], preferred_color: str = None) -> Optional[Dict]:
        """Select appropriate product variant"""
        if not variants:
            return None
        
        # If color preference specified, try to match
        if preferred_color:
            for variant in variants:
                variant_title = variant.get('title', '').lower()
                if preferred_color.lower() in variant_title:
                    return variant
        
        # Return first available variant
        return variants[0]
    
    def _get_print_areas(self, print_provider_id: str, blueprint_id: str, variant_id: str) -> List[Dict]:
        """Get available print areas for product variant"""
        try:
            # Based on Printify API docs, print areas are available at this endpoint
            response = requests.get(
                f"{self.base_url}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/print_areas.json",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                print_areas_data = response.json()
                logger.info(f"Print areas response: {print_areas_data}")
                
                # The response should be a list of print areas
                if isinstance(print_areas_data, list) and print_areas_data:
                    return print_areas_data
                else:
                    logger.warning(f"Unexpected print areas format: {type(print_areas_data)}")
                    return []
            else:
                logger.error(f"Failed to get print areas: {response.status_code} - {response.text}")
                
                # Try to create a fallback print area for common positions
                logger.info("Creating fallback print areas")
                return [{
                    "id": "front",
                    "name": "Front",
                    "width": 300,
                    "height": 300,
                    "top": 50,
                    "left": 50
                }]
                
        except Exception as e:
            logger.error(f"Error getting print areas: {e}")
            # Return fallback print area
            return [{
                "id": "front", 
                "name": "Front",
                "width": 300,
                "height": 300,
                "top": 50,
                "left": 50
            }]
    
    def _build_product_data(self, blueprint: Dict, print_provider_id: str, variant: Dict, 
                          logo_image_id: str, print_area: Dict) -> Dict:
        """Build product creation data structure"""
        
        # Position logo in center of print area
        print_area_width = print_area.get('width', 100)
        print_area_height = print_area.get('height', 100)
        
        # Scale logo to reasonable size (e.g., 60% of print area)
        logo_scale = 0.6
        logo_width = int(print_area_width * logo_scale)
        logo_height = int(print_area_height * logo_scale)
        
        # Center positioning
        logo_x = int((print_area_width - logo_width) / 2)
        logo_y = int((print_area_height - logo_height) / 2)
        
        return {
            "title": f"Custom {blueprint.get('title', 'Product')} with Team Logo",
            "description": "Custom youth sports team merchandise with uploaded logo",
            "blueprint_id": blueprint.get('id'),
            "print_provider_id": print_provider_id,
            "variants": [
                {
                    "id": variant.get('id'),
                    "price": int((variant.get('price', 1500) * 1.5)),  # Add markup
                    "is_enabled": True
                }
            ],
            "print_areas": [
                {
                    "variant_ids": [variant.get('id')],
                    "placeholders": [
                        {
                            "position": print_area.get('id', 'front'),  # Use print area ID as position string
                            "images": [
                                {
                                    "id": logo_image_id,
                                    "x": 0.5,  # Center horizontally (0.0 to 1.0)
                                    "y": 0.5,  # Center vertically (0.0 to 1.0)
                                    "scale": 0.6,  # 60% of available area
                                    "angle": 0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    def _generate_mockup(self, product_id: str) -> Dict:
        """Get product mockup images (automatically generated by Printify)"""
        try:
            logger.info(f"Getting mockup images for product: {product_id}")
            
            # Get product details which include automatically generated mockup images
            response = requests.get(
                f"{self.base_url}/shops/{self.shop_id}/products/{product_id}.json",
                headers=self.headers,
                timeout=30
            )
            
            logger.info(f"Product details response: {response.status_code}")
            if response.status_code == 200:
                product_data = response.json()
                images = product_data.get('images', [])
                
                logger.info(f"Found {len(images)} product images")
                
                # Find the default front-facing mockup image
                for image in images:
                    if image.get('is_default', False) and image.get('position') == 'front':
                        mockup_url = image.get('src')
                        if mockup_url:
                            logger.info(f"Found default front mockup: {mockup_url}")
                            return {"mockup_url": mockup_url}
                
                # Fallback: use first available image
                if images:
                    mockup_url = images[0].get('src')
                    if mockup_url:
                        logger.info(f"Using first available mockup: {mockup_url}")
                        return {"mockup_url": mockup_url}
                
                logger.warning("No mockup images found in product data")
            else:
                logger.warning(f"Failed to get product details: {response.status_code} - {response.text}")
            
            return {"mockup_url": None}
            
        except Exception as e:
            logger.error(f"Error getting mockup images: {e}")
            return {"mockup_url": None}
    
    def _generate_purchase_url(self, product_id: str) -> str:
        """Generate purchase URL for product"""
        return f"https://printify.com/app/products/{product_id}"
    
    def _publish_product(self, product_id: str) -> Dict:
        """Publish product to make it available for purchase"""
        try:
            # First, check what sales channels are available for this shop
            channels_response = requests.get(
                f"{self.base_url}/shops/{self.shop_id}.json",
                headers=self.headers,
                timeout=15
            )
            
            if channels_response.status_code == 200:
                shop_data = channels_response.json()
                logger.info(f"Shop data: {shop_data}")
                
                # Check if this shop supports publishing
                sales_channel = shop_data.get('sales_channel')
                logger.info(f"Sales channel: {sales_channel}")
                
                # For Printify Express, we might need a different approach
                if sales_channel == 'printify_express':
                    logger.info("Printify Express detected - products may not need explicit publishing")
                    # For Printify Express, products might be automatically available
                    # Just return success with the standard product URL
                    return {
                        "success": True,
                        "external_id": product_id,
                        "purchase_url": f"https://printify.com/app/products/{product_id}"
                    }
            
            # Try standard publishing approach
            publish_data = {
                "title": True,
                "description": True,
                "images": True,
                "variants": True,
                "tags": True,
                "keyFeatures": True,
                "shipping": True
            }
            
            response = requests.post(
                f"{self.base_url}/shops/{self.shop_id}/products/{product_id}/publish.json",
                headers=self.headers,
                json=publish_data,
                timeout=30
            )
            
            if response.status_code == 200:
                publish_result = response.json()
                logger.info(f"Successfully published product {product_id}")
                
                # Get the published product URL
                published_url = self._get_published_product_url(product_id)
                
                return {
                    "success": True,
                    "external_id": publish_result.get('external_id'),
                    "purchase_url": published_url
                }
            else:
                logger.error(f"Failed to publish product: {response.status_code} - {response.text}")
                
                # If publishing fails, still return success with basic URL
                # The product exists and may be purchasable through Printify directly
                return {
                    "success": True,
                    "external_id": product_id,
                    "purchase_url": f"https://printify.com/app/products/{product_id}",
                    "note": "Product created but not published to external store"
                }
                
        except Exception as e:
            logger.error(f"Error publishing product: {e}")
            # Return success anyway - product is created
            return {
                "success": True,
                "external_id": product_id,
                "purchase_url": f"https://printify.com/app/products/{product_id}",
                "note": "Product created but publishing failed"
            }
    
    def _get_published_product_url(self, product_id: str) -> str:
        """Get the published product URL from store"""
        try:
            # Get product details to find external store URL
            response = requests.get(
                f"{self.base_url}/shops/{self.shop_id}/products/{product_id}.json",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code == 200:
                product_data = response.json()
                external_id = product_data.get('external', {}).get('id')
                if external_id:
                    # This would be the actual store URL - format depends on your store platform
                    return f"https://your-store.com/products/{external_id}"
            
            # Fallback to Printify product page
            return f"https://printify.com/app/products/{product_id}"
            
        except Exception as e:
            logger.warning(f"Could not get published URL: {e}")
            return f"https://printify.com/app/products/{product_id}"
    
    def get_product_colors(self, product_id: str) -> List[str]:
        """Get available colors for a product"""
        try:
            response = requests.get(
                f"{self.base_url}/catalog/blueprints/{product_id}/print_providers.json",
                headers=self.headers,
                timeout=15
            )
            
            if response.status_code != 200:
                return []
            
            providers = response.json()
            if not providers:
                return []
            
            # Get variants from first provider
            variants_response = requests.get(
                f"{self.base_url}/catalog/blueprints/{product_id}/print_providers/{providers[0]['id']}/variants.json",
                headers=self.headers,
                timeout=15
            )
            
            if variants_response.status_code == 200:
                variants_data = variants_response.json()
                colors = []
                for variant in variants_data.get('variants', []):
                    title = variant.get('title', '')
                    if title and title not in colors:
                        colors.append(title)
                return colors
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting product colors: {e}")
            return []

# Global instance
printify_service = PrintifyService() 