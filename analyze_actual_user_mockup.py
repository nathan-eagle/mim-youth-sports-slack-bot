#!/usr/bin/env python3
"""
Analyze the ACTUAL mockup URL the user just received to see what color it shows
"""

import requests
from PIL import Image
import tempfile
import numpy as np
from collections import Counter
import os

def analyze_mockup_color(url):
    """Download and analyze the shirt color in the user's actual mockup"""
    print(f"🔍 ANALYZING USER'S ACTUAL MOCKUP")
    print(f"URL: {url}")
    print("-" * 80)
    
    try:
        # Download the image
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to download: HTTP {response.status_code}")
            return None
        
        print(f"✅ Downloaded {len(response.content)} bytes")
        
        # Save and analyze
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            
            # Open and analyze
            image = Image.open(tmp_file.name)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for analysis
            image = image.resize((200, 200))
            img_array = np.array(image)
            
            # Focus on center area where shirt would be
            h, w = img_array.shape[:2]
            center_area = img_array[h//3:2*h//3, w//3:2*w//3]
            
            # Get all pixels
            pixels = center_area.reshape(-1, 3)
            colors = [tuple(pixel) for pixel in pixels]
            color_counts = Counter(colors)
            
            print(f"🎨 TOP 10 COLORS IN MOCKUP:")
            for i, (color, count) in enumerate(color_counts.most_common(10), 1):
                r, g, b = color
                percentage = (count / len(colors)) * 100
                
                # Classify color
                if r > 220 and g > 220 and b > 220:
                    color_name = "WHITE"
                elif r < 50 and g < 50 and b < 50:
                    color_name = "BLACK"
                elif r > g + 30 and r > b + 30:
                    color_name = "RED"
                elif b > r + 30 and b > g + 30:
                    color_name = "BLUE"
                elif g > r + 30 and g > b + 30:
                    color_name = "GREEN"
                else:
                    color_name = "OTHER"
                
                print(f"   {i}. {color_name}: {percentage:.1f}% - RGB{color}")
            
            # Determine shirt color (non-white dominant color)
            shirt_color = None
            for color, count in color_counts.most_common(20):
                r, g, b = color
                if r < 200 or g < 200 or b < 200:  # Not white background
                    percentage = (count / len(colors)) * 100
                    if percentage > 5:  # Significant portion
                        if r > g + 20 and r > b + 20:
                            shirt_color = f"RED (RGB{color})"
                        elif b > r + 20 and b > g + 20:
                            shirt_color = f"BLUE (RGB{color})"
                        elif g > r + 20 and g > b + 20:
                            shirt_color = f"GREEN (RGB{color})"
                        elif r < 80 and g < 80 and b < 80:
                            shirt_color = f"BLACK (RGB{color})"
                        else:
                            shirt_color = f"OTHER (RGB{color})"
                        break
            
            if not shirt_color:
                shirt_color = "WHITE ONLY"
            
            print(f"\n🎯 SHIRT COLOR DETECTED: {shirt_color}")
            
            # Clean up
            os.unlink(tmp_file.name)
            
            return shirt_color
            
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        return None

def main():
    print("🧪 ANALYZING THE USER'S ACTUAL RED JERSEY MOCKUP")
    print("=" * 80)
    
    # The actual URL the user received for "red jersey"
    red_jersey_url = "https://images-api.printify.com/mockup/6864202147882184f10d16e1/18486/92547/custom-unisex-jersey-short-sleeve-tee-for-team.jpg?camera_label=front"
    
    print("This is the EXACT mockup URL the user received when they asked for 'red jersey'")
    print("Let's see what color shirt it actually shows...")
    print()
    
    result = analyze_mockup_color(red_jersey_url)
    
    print(f"\n📊 ANALYSIS RESULT:")
    if result and "RED" in result:
        print("✅ SUCCESS: The mockup DOES show a red shirt!")
        print("   The color system is working correctly.")
    elif result and "WHITE" in result:
        print("❌ FAILURE: The mockup shows a WHITE shirt!")
        print("   This explains the user's frustration - colors are NOT working.")
        print("   Even though we used variant 18486, it's still showing white.")
    else:
        print(f"❓ UNCLEAR: The mockup shows: {result}")
        print("   Need to investigate further.")
    
    print(f"\n🔗 USER CAN VIEW THE MOCKUP HERE:")
    print(f"{red_jersey_url}")
    print(f"\nNote: Variant 18486 in the URL should correspond to a specific color.")
    print(f"If it's showing white, then Printify's mockup generation has issues.")

if __name__ == "__main__":
    main()