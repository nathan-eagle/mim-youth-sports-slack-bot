#!/usr/bin/env python3
"""
Refresh the product cache with live data from Printify's API
This will get current blueprint_ids, variant_ids, and provider info
"""

import os
import json
import requests
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class PrintifyAPIRefresh:
    def __init__(self):
        self.api_token = os.getenv('PRINTIFY_API_TOKEN')
        self.base_url = "https://api.printify.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        if not self.api_token:
            raise ValueError("PRINTIFY_API_TOKEN not found in environment variables")
    
    def get_all_blueprints(self):
        """Get all available blueprints from Printify"""
        try:
            response = requests.get(f"{self.base_url}/catalog/blueprints.json", headers=self.headers)
            if response.status_code == 200:
                blueprints = response.json()
                logger.info(f"Retrieved {len(blueprints)} blueprints from Printify")
                return blueprints
            else:
                logger.error(f"Failed to get blueprints: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Exception getting blueprints: {e}")
            return []
    
    def get_blueprint_details(self, blueprint_id):
        """Get detailed information about a specific blueprint"""
        try:
            response = requests.get(f"{self.base_url}/catalog/blueprints/{blueprint_id}.json", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get blueprint {blueprint_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception getting blueprint {blueprint_id}: {e}")
            return None
    
    def get_blueprint_print_providers(self, blueprint_id):
        """Get print providers for a specific blueprint"""
        try:
            response = requests.get(f"{self.base_url}/catalog/blueprints/{blueprint_id}/print_providers.json", headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get print providers for blueprint {blueprint_id}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception getting print providers for blueprint {blueprint_id}: {e}")
            return []
    
    def get_blueprint_variants(self, blueprint_id, print_provider_id):
        """Get variants for a specific blueprint and print provider"""
        try:
            url = f"{self.base_url}/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                # Handle different response formats
                if 'variants' in data:
                    return data['variants']
                elif isinstance(data, list):
                    return data
                else:
                    return []
            else:
                logger.warning(f"Failed to get variants for blueprint {blueprint_id}, provider {print_provider_id}: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Exception getting variants: {e}")
            return []
    
    def refresh_product_cache(self):
        """Refresh our product cache with live Printify data"""
        print("🔄 Refreshing product cache with live Printify data...")
        
        # Target products we want to update (from our current cache)
        target_products = {
            12: "Unisex Jersey Short Sleeve Tee",
            92: "Unisex College Hoodie", 
            6: "Unisex Heavy Cotton Tee",
            145: "Unisex Softstyle T-Shirt",
            1525: "Unisex Midweight Softstyle Fleece Hoodie",
            499: "Unisex Supply Hoodie"
        }
        
        # Get all blueprints to find our target products
        blueprints = self.get_all_blueprints()
        if not blueprints:
            print("❌ Failed to get blueprints from Printify API")
            return False
        
        updated_products = {}
        
        for blueprint in blueprints:
            blueprint_id = blueprint.get('id')
            title = blueprint.get('title', '')
            
            # Check if this is one of our target products
            if blueprint_id in target_products:
                print(f"🎯 Found target product: {title} (Blueprint {blueprint_id})")
                
                # Get print providers for this blueprint
                print_providers = self.get_blueprint_print_providers(blueprint_id)
                if not print_providers:
                    print(f"  ❌ No providers available for {title}")
                    continue
                
                # Show available providers and prefer Printify Choice, but use any available
                provider_info = [(p.get('id'), p.get('title')) for p in print_providers]
                print(f"  📋 Available providers: {provider_info}")
                
                # Try to find Printify Choice first
                selected_provider = None
                for provider in print_providers:
                    if provider.get('id') == 99:  # Printify Choice
                        selected_provider = provider
                        print(f"  ✅ Using Printify Choice provider")
                        break
                
                # If no Printify Choice, use the first available provider
                if not selected_provider:
                    selected_provider = print_providers[0]
                    provider_id = selected_provider.get('id')
                    provider_name = selected_provider.get('title')
                    print(f"  ⚠️ Printify Choice not available, using {provider_name} (ID: {provider_id})")
                
                # Get current variants using the selected provider
                provider_id = selected_provider.get('id')
                variants = self.get_blueprint_variants(blueprint_id, provider_id)
                if not variants:
                    print(f"  ❌ No variants found for {title}")
                    continue
                
                print(f"  📦 Retrieved {len(variants)} current variants")
                
                # Build product data structure
                is_printify_choice = provider_id == 99
                product_data = {
                    "id": blueprint_id,
                    "title": title,
                    "category": self._categorize_product(title),
                    "blueprint_id": blueprint_id,
                    "primary_print_provider_id": provider_id,
                    "print_provider_id": provider_id,  # Add this for compatibility
                    "print_providers": [provider_id],
                    "is_printify_choice": is_printify_choice,
                    "variants": self._format_variants(variants),
                    "available": True,
                    "popularity_score": 200  # High score for our selected products
                }
                
                updated_products[str(blueprint_id)] = product_data
                print(f"  ✅ Updated product data for {title}")
        
        if updated_products:
            self._save_updated_cache(updated_products)
            return True
        else:
            print("❌ No products were successfully updated")
            return False
    
    def _categorize_product(self, title):
        """Categorize product based on title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['hoodie', 'sweatshirt']):
            return 'hoodie'
        elif any(word in title_lower for word in ['tee', 't-shirt', 'shirt']):
            return 'shirt'
        else:
            return 'other'
    
    def _format_variants(self, variants):
        """Format variants for our cache structure"""
        formatted_variants = []
        for variant in variants:
            formatted_variant = {
                "id": variant.get('id'),
                "color": variant.get('title', '').replace(' / ', '/').split('/')[0] if '/' in variant.get('title', '') else variant.get('title', ''),
                "size": variant.get('title', '').replace(' / ', '/').split('/')[-1] if '/' in variant.get('title', '') else 'One size',
                "available": True,  # Assume available if returned by API
                "price": variant.get('price', 20.0)  # Default price if not provided
            }
            formatted_variants.append(formatted_variant)
        
        return formatted_variants
    
    def _save_updated_cache(self, updated_products):
        """Save the updated cache to disk"""
        try:
            # Load existing cache structure
            cache_file = "top3_product_cache_optimized.json"
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                # Create new cache structure if file doesn't exist
                cache = {
                    "version": "3.0-top3-live",
                    "optimization_info": {},
                    "category_info": {},
                    "providers": {"99": "Printify Choice"},
                    "products": {}
                }
            
            # Update products with fresh data
            cache["products"] = updated_products
            cache["last_update"] = datetime.now().isoformat()
            cache["version"] = "3.0-top3-live"
            
            # Update metadata
            categories = set(product.get('category') for product in updated_products.values())
            cache["category_info"] = {cat: {"total_available": 1, "top3_selected": 1, "avg_popularity": 200} for cat in categories}
            cache["optimization_info"] = {
                "source": "live_printify_api",
                "original_products": len(updated_products),
                "optimized_products": len(updated_products), 
                "categories_included": len(categories),
                "selection_criteria": "live_api_refresh",
                "api_refresh_date": datetime.now().isoformat()
            }
            
            # Save main cache
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            
            # Copy to drop directory
            import shutil
            shutil.copy(cache_file, "drop/")
            
            print(f"✅ Successfully saved updated cache with {len(updated_products)} products")
            print(f"📁 Updated both {cache_file} and drop/{cache_file}")
            
        except Exception as e:
            logger.error(f"Failed to save updated cache: {e}")

def main():
    print("🚀 REFRESHING PRODUCT CACHE FROM PRINTIFY API")
    print("=" * 60)
    
    try:
        api = PrintifyAPIRefresh()
        success = api.refresh_product_cache()
        
        if success:
            print("\n✅ Cache refresh completed successfully!")
            print("The cache now contains fresh data from Printify's live API.")
            print("Try testing the mockup generation again.")
        else:
            print("\n❌ Cache refresh failed.")
            print("Check the error messages above for details.")
    
    except Exception as e:
        print(f"\n❌ Error during cache refresh: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()