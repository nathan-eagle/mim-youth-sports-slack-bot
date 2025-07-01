#!/usr/bin/env python3
"""
Test that the red jersey fix works correctly
"""

import os
from dotenv import load_dotenv
from product_service import ProductService
from slack_bot import SlackBot
import requests
from PIL import Image
import tempfile
import numpy as np
from collections import Counter

load_dotenv()

def analyze_shirt_color(url):
    """Quick analysis of shirt color"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return "download_failed"
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            
            image = Image.open(tmp_file.name)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image = image.resize((150, 150))
            img_array = np.array(image)
            
            # Focus on center area
            h, w = img_array.shape[:2]
            center_area = img_array[h//4:3*h//4, w//4:3*w//4]
            pixels = center_area.reshape(-1, 3)
            colors = [tuple(pixel) for pixel in pixels]
            color_counts = Counter(colors)
            
            # Find non-white dominant color
            for color, count in color_counts.most_common(20):
                r, g, b = color
                if r < 200 or g < 200 or b < 200:  # Not white
                    percentage = (count / len(colors)) * 100
                    if percentage > 3:  # Significant portion
                        if r > g + 20 and r > b + 20:
                            return "RED"
                        elif b > r + 20 and b > g + 20:
                            return "BLUE"
                        elif r < 80 and g < 80 and b < 80:
                            return "BLACK"
                        else:
                            return f"OTHER_RGB({r},{g},{b})"
            
            return "WHITE_ONLY"
            
    except Exception as e:
        return f"ERROR: {e}"
    finally:
        try:
            os.unlink(tmp_file.name)
        except:
            pass

def test_red_jersey():
    """Test red jersey creation with the fix"""
    print("🧪 TESTING RED JERSEY AFTER BUG FIX")
    print("=" * 60)
    
    slack_bot = SlackBot()
    product_service = ProductService()
    
    # Simulate conversation state
    conversation = {
        "state": "completed",
        "team_info": {"name": "Test Team"},
        "logo_info": {"printify_image_id": "685d8aee5638948d7abca30a"}
    }
    
    # Parse red jersey request
    variants = product_service.parse_color_preferences("red jersey")
    if not variants:
        print("❌ Failed to parse red jersey request")
        return False
    
    variant_info = variants[0]
    print(f"✅ Parsed: {variant_info['product_name']} in {variant_info['color']}")
    print(f"   Variant ID: {variant_info['variant']['id']}")
    
    # Create product info
    product_info = {
        "id": variant_info['product_id'],
        "formatted": {"title": variant_info['product_name']}
    }
    
    # Test mockup creation
    print(f"\n🔄 Creating red jersey mockup...")
    result = slack_bot._create_single_mockup_with_variant(
        conversation=conversation,
        logo_info=conversation['logo_info'],
        product_info=product_info,
        selected_variant=variant_info['variant'],
        channel="test_channel",
        user="test_user"
    )
    
    if not result.get("image_url"):
        print(f"❌ Failed to create mockup: {result}")
        return False
    
    mockup_url = result["image_url"]
    print(f"✅ Mockup created: {mockup_url}")
    
    # Extract variant ID from URL
    url_parts = mockup_url.split('/')
    url_variant_id = None
    for part in url_parts:
        if part.isdigit() and len(part) > 4:
            url_variant_id = part
            break
    
    print(f"   URL variant ID: {url_variant_id}")
    print(f"   Expected variant ID: {variant_info['variant']['id']}")
    
    # Analyze the actual mockup color
    print(f"\n🎨 Analyzing mockup image color...")
    detected_color = analyze_shirt_color(mockup_url)
    print(f"   Detected shirt color: {detected_color}")
    
    # Check results
    variant_id_correct = str(variant_info['variant']['id']) == url_variant_id
    color_correct = "RED" in detected_color
    
    print(f"\n📊 RESULTS:")
    print(f"   Variant ID correct: {'✅' if variant_id_correct else '❌'}")
    print(f"   Color correct: {'✅' if color_correct else '❌'}")
    
    if variant_id_correct and color_correct:
        print(f"\n🎉 SUCCESS: Red jersey fix is working!")
        print(f"   - Correct variant ID in URL")
        print(f"   - Red shirt visible in mockup")
        return True
    else:
        print(f"\n❌ STILL BROKEN:")
        if not variant_id_correct:
            print(f"   - Wrong variant ID: got {url_variant_id}, expected {variant_info['variant']['id']}")
        if not color_correct:
            print(f"   - Wrong color: got {detected_color}, expected RED")
        return False

if __name__ == "__main__":
    success = test_red_jersey()
    print(f"\n{'🎉 FIX SUCCESSFUL' if success else '❌ STILL BROKEN'}")