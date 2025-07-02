#!/usr/bin/env python3
"""
Test mockup URL format from Printify to debug Slack display issues
"""

import json

def check_mockup_urls():
    """Check mockup URL format in drop_data.json"""
    print("🔍 CHECKING MOCKUP URL FORMATS")
    print("=" * 60)
    
    try:
        with open("drop_data.json", 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load drop_data.json: {e}")
        return
    
    designs = data.get("product_designs", {})
    
    print(f"Found {len(designs)} product designs\n")
    
    # Check each design's mockup URL
    for design_id, design in list(designs.items())[:5]:  # First 5 designs
        mockup_url = design.get("mockup_image_url", "")
        product_name = design.get("name", "Unknown")
        
        print(f"📦 {product_name}")
        print(f"   ID: {design_id}")
        print(f"   URL: {mockup_url}")
        
        # Analyze URL structure
        if mockup_url:
            if mockup_url.startswith("https://images-api.printify.com"):
                print("   ✅ Valid Printify URL format")
            else:
                print(f"   ⚠️  Unusual URL format: {mockup_url[:50]}...")
                
            # Check for common issues
            if " " in mockup_url:
                print("   ❌ URL contains spaces!")
            if "&amp;" in mockup_url:
                print("   ⚠️  URL contains HTML-encoded ampersands")
                
        else:
            print("   ❌ No mockup URL found")
            
        print()

if __name__ == "__main__":
    check_mockup_urls()