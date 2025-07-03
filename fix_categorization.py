#!/usr/bin/env python3
"""
Fix product categorization using AI to properly categorize products
"""

import os
import json
import openai
from dotenv import load_dotenv

load_dotenv()

def fix_product_categories():
    """Use AI to fix product categorization in the cache"""
    print("🔧 FIXING PRODUCT CATEGORIZATION")
    print("=" * 50)
    
    # Set up OpenAI with correct key
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    # Load current cache
    with open('printifychoicecache.json', 'r') as f:
        cache = json.load(f)
    
    products = cache['products']
    category_changes = {}
    
    print(f"Loaded {len(products)} products to categorize")
    
    # Create AI categorization prompt
    system_prompt = """You are an expert product categorizer for youth sports merchandise.

Categorize products into these EXACT categories:
- tshirt (any t-shirt, tee, jersey, short sleeve shirt)
- hoodie (hoodies, sweatshirts, pullover, zip-up)
- tank (tank tops, racerback, muscle shirts, sleeveless)
- long_sleeve (long sleeve shirts, longsleeve tees)
- headwear (hats, caps, beanies, visors)
- other (everything else: bags, mugs, stickers, blankets, etc.)

Respond with just the category name, nothing else."""
    
    fixed_count = 0
    
    for product_id, product in products.items():
        title = product['title']
        current_category = product['category']
        
        # Use AI to determine correct category
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Categorize this product: {title}"}
                ],
                temperature=0.1,
                max_tokens=20
            )
            
            ai_category = response['choices'][0]['message']['content'].strip().lower()
            
            # Validate AI response
            valid_categories = ['tshirt', 'hoodie', 'tank', 'long_sleeve', 'headwear', 'other']
            if ai_category not in valid_categories:
                # Fallback logic
                title_lower = title.lower()
                if any(word in title_lower for word in ['tee', 't-shirt', 'shirt', 'jersey']) and 'long' not in title_lower:
                    ai_category = 'tshirt'
                elif any(word in title_lower for word in ['hoodie', 'sweatshirt', 'pullover']):
                    ai_category = 'hoodie'
                elif any(word in title_lower for word in ['tank', 'racerback']):
                    ai_category = 'tank'
                elif any(word in title_lower for word in ['long sleeve', 'longsleeve']):
                    ai_category = 'long_sleeve'
                elif any(word in title_lower for word in ['hat', 'cap', 'beanie']):
                    ai_category = 'headwear'
                else:
                    ai_category = 'other'
            
            # Check if category needs changing
            if ai_category != current_category:
                print(f"  📝 {title}")
                print(f"     {current_category} → {ai_category}")
                
                product['category'] = ai_category
                category_changes[product_id] = {
                    'title': title,
                    'old': current_category,
                    'new': ai_category
                }
                fixed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error categorizing {title}: {e}")
            # Keep original category on error
    
    # Update category counts
    new_categories = {}
    for product in products.values():
        cat = product['category']
        new_categories[cat] = new_categories.get(cat, 0) + 1
    
    cache['categories'] = new_categories
    cache['metadata']['categorization_fixed'] = True
    cache['metadata']['fixes_applied'] = len(category_changes)
    
    # Save updated cache
    with open('printifychoicecache.json', 'w') as f:
        json.dump(cache, f, indent=2)
    
    # Also update drop directory
    import shutil
    if os.path.exists('drop/'):
        shutil.copy('printifychoicecache.json', 'drop/')
    
    print(f"\n✅ Fixed {fixed_count} product categorizations")
    print(f"📊 New category counts: {new_categories}")
    
    if category_changes:
        print(f"\n📋 Changes made:")
        for change in list(category_changes.values())[:10]:  # Show first 10
            print(f"  • {change['title']}: {change['old']} → {change['new']}")
        
        if len(category_changes) > 10:
            print(f"  ... and {len(category_changes) - 10} more changes")
    
    return len(category_changes) > 0

def main():
    try:
        success = fix_product_categories()
        if success:
            print("\n🎉 Product categorization fixed successfully!")
        else:
            print("\n✅ No categorization changes needed")
    except Exception as e:
        print(f"\n❌ Error fixing categories: {e}")
        # Create simple fallback fix
        print("Applying fallback categorization...")
        
        with open('printifychoicecache.json', 'r') as f:
            cache = json.load(f)
        
        # Simple keyword-based fixes
        fixes = 0
        for product in cache['products'].values():
            title = product['title'].lower()
            old_cat = product['category']
            
            if any(word in title for word in ['tee', 't-shirt', 'shirt', 'jersey']) and 'long' not in title and old_cat != 'tshirt':
                product['category'] = 'tshirt'
                fixes += 1
            elif any(word in title for word in ['hoodie', 'sweatshirt']) and old_cat != 'hoodie':
                product['category'] = 'hoodie'
                fixes += 1
            elif any(word in title for word in ['tank', 'racerback']) and old_cat != 'tank':
                product['category'] = 'tank'
                fixes += 1
            elif any(word in title for word in ['mug', 'sticker', 'blanket', 'bag']) and old_cat != 'other':
                product['category'] = 'other'
                fixes += 1
        
        # Update counts
        new_categories = {}
        for product in cache['products'].values():
            cat = product['category']
            new_categories[cat] = new_categories.get(cat, 0) + 1
        
        cache['categories'] = new_categories
        
        with open('printifychoicecache.json', 'w') as f:
            json.dump(cache, f, indent=2)
        
        print(f"✅ Applied {fixes} fallback fixes")

if __name__ == "__main__":
    main()