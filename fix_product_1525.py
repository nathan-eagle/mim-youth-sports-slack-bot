#!/usr/bin/env python3
"""
Fix the swapped color/size fields in product 1525 (Midweight Softstyle Fleece Hoodie)
"""

import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_product_1525():
    """Fix the swapped color and size fields in product 1525"""
    
    cache_file = "top3_product_cache_optimized.json"
    
    # Load the cache
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cache file: {e}")
        return False
    
    # Check if product 1525 exists
    if "1525" not in data.get("products", {}):
        logger.error("Product 1525 not found in cache")
        return False
    
    product = data["products"]["1525"]
    variants = product.get("variants", [])
    
    if not variants:
        logger.error("No variants found for product 1525")
        return False
    
    logger.info(f"Found {len(variants)} variants to fix in product 1525")
    
    # Show before/after for first few variants
    logger.info("BEFORE (first 3 variants):")
    for i, variant in enumerate(variants[:3]):
        logger.info(f"  Variant {variant['id']}: color='{variant['color']}', size='{variant['size']}'")
    
    # Fix all variants by swapping color and size fields
    fixed_count = 0
    for variant in variants:
        old_color = variant["color"]
        old_size = variant["size"]
        
        # Swap the fields
        variant["color"] = old_size
        variant["size"] = old_color
        fixed_count += 1
    
    logger.info(f"Fixed {fixed_count} variants")
    logger.info("AFTER (first 3 variants):")
    for i, variant in enumerate(variants[:3]):
        logger.info(f"  Variant {variant['id']}: color='{variant['color']}', size='{variant['size']}'")
    
    # Save the corrected cache
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved corrected cache to {cache_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save corrected cache: {e}")
        return False

def verify_fix():
    """Verify that the fix worked"""
    cache_file = "top3_product_cache_optimized.json"
    
    try:
        with open(cache_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load cache file for verification: {e}")
        return False
    
    product = data.get("products", {}).get("1525", {})
    variants = product.get("variants", [])
    
    if not variants:
        logger.error("No variants found during verification")
        return False
    
    # Check first few variants to ensure fields are correct
    sizes = {"S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"}
    colors = {"Cocoa", "Paragon", "Pink Lemonade", "Charcoal", "Dark Heather", "Maroon", "Navy", "Pistachio"}
    
    correct_variants = 0
    for variant in variants[:10]:  # Check first 10
        if variant["size"] in sizes and variant["color"] in colors:
            correct_variants += 1
    
    logger.info(f"Verification: {correct_variants}/10 variants have correct field mapping")
    return correct_variants >= 8  # Allow some margin

if __name__ == "__main__":
    logger.info("🔧 FIXING PRODUCT 1525 COLOR/SIZE FIELD SWAPPING")
    logger.info("=" * 60)
    
    if fix_product_1525():
        logger.info("✅ Fix applied successfully")
        
        if verify_fix():
            logger.info("✅ Verification passed - fields are now correct")
            logger.info("🎉 Product 1525 fix completed successfully!")
        else:
            logger.error("❌ Verification failed - something went wrong")
    else:
        logger.error("❌ Fix failed")