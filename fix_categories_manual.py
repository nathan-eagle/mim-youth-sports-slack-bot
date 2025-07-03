#!/usr/bin/env python3
"""
Manual fix for product categorization using keyword matching
"""

import json

def fix_categories_manual():
    """Fix categories using simple keyword matching"""
    print("🔧 MANUAL CATEGORIZATION FIX")
    print("=" * 40)
    
    # Load current cache
    with open('printifychoicecache.json', 'r') as f:
        cache = json.load(f)
    
    products = cache['products']
    fixes = 0
    changes = []
    
    for product_id, product in products.items():
        title = product['title'].lower()
        old_category = product['category']
        new_category = old_category
        
        # T-shirts and tees
        if any(word in title for word in ['tee', 't-shirt', 'shirt', 'jersey']) and 'long' not in title and 'sweat' not in title:
            new_category = 'tshirt'
        
        # Hoodies and sweatshirts
        elif any(word in title for word in ['hoodie', 'sweatshirt', 'pullover', 'fleece hoodie']):
            new_category = 'hoodie'
        
        # Tank tops
        elif any(word in title for word in ['tank', 'racerback', 'muscle']):
            new_category = 'tank'
        
        # Long sleeve
        elif any(word in title for word in ['long sleeve', 'longsleeve', 'long-sleeve']):
            new_category = 'long_sleeve'
        
        # Headwear (actual hats/caps)
        elif any(word in title for word in ['hat', 'cap', 'beanie', 'visor', 'snapback']):
            new_category = 'headwear'
        
        # Other items
        elif any(word in title for word in ['mug', 'sticker', 'blanket', 'poster', 'towel', 'bodysuit', 'onesie']):
            new_category = 'other'
        
        # Apply fix if needed
        if new_category != old_category:
            product['category'] = new_category
            changes.append({
                'title': product['title'],
                'old': old_category,
                'new': new_category
            })
            fixes += 1
    
    # Update category counts
    new_categories = {}
    for product in products.values():
        cat = product['category']
        new_categories[cat] = new_categories.get(cat, 0) + 1
    
    cache['categories'] = new_categories
    cache['metadata']['manual_categorization_applied'] = True
    cache['metadata']['manual_fixes'] = fixes
    
    # Save updated cache
    with open('printifychoicecache.json', 'w') as f:
        json.dump(cache, f, indent=2)
    
    # Also update drop directory
    import os, shutil
    if os.path.exists('drop/'):
        shutil.copy('printifychoicecache.json', 'drop/')
    
    print(f"✅ Applied {fixes} manual categorization fixes")
    print(f"📊 New category counts: {new_categories}")
    
    if changes:
        print(f"\n📋 Key changes:")
        for change in changes[:15]:  # Show first 15
            print(f"  • {change['title']}: {change['old']} → {change['new']}")
        
        if len(changes) > 15:
            print(f"  ... and {len(changes) - 15} more changes")
    
    return fixes

if __name__ == "__main__":
    fix_categories_manual()