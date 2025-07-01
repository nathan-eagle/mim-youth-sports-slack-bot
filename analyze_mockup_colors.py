#!/usr/bin/env python3
"""
Download and analyze actual mockup images to detect their colors
"""

import os
import requests
from PIL import Image
import numpy as np
from collections import Counter
import tempfile

def download_image(url):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.content
        else:
            print(f"Failed to download: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def analyze_image_colors(image_data):
    """Analyze the dominant colors in an image"""
    try:
        # Save to temp file and open with PIL
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            tmp_file.write(image_data)
            tmp_file.flush()
            
            # Open image
            image = Image.open(tmp_file.name)
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for faster processing
            image = image.resize((150, 150))
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Focus on the center area where the t-shirt would be
            h, w = img_array.shape[:2]
            center_area = img_array[h//4:3*h//4, w//4:3*w//4]
            
            # Reshape to list of RGB values
            pixels = center_area.reshape(-1, 3)
            
            # Count color frequencies
            colors = [tuple(pixel) for pixel in pixels]
            color_counts = Counter(colors)
            
            # Get most common colors
            most_common = color_counts.most_common(10)
            
            # Analyze dominant colors
            dominant_colors = []
            for color, count in most_common:
                r, g, b = color
                
                # Classify color
                if r > 200 and g > 200 and b > 200:
                    color_name = "White"
                elif r < 60 and g < 60 and b < 60:
                    color_name = "Black"
                elif r > g and r > b:
                    color_name = "Red-ish"
                elif g > r and g > b:
                    color_name = "Green-ish"
                elif b > r and b > g:
                    color_name = "Blue-ish"
                elif r > 100 and g > 100 and b < 80:
                    color_name = "Yellow-ish"
                elif r > 120 and g < 80 and b > 120:
                    color_name = "Purple-ish"
                else:
                    color_name = f"RGB({r},{g},{b})"
                
                percentage = (count / len(colors)) * 100
                dominant_colors.append((color_name, color, percentage))
            
            # Clean up temp file
            os.unlink(tmp_file.name)
            
            return dominant_colors
            
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return []

def test_mockup_colors():
    """Test the actual mockup URLs from the Slack interaction"""
    print("🎨 ANALYZING ACTUAL MOCKUP IMAGE COLORS")
    print("=" * 60)
    
    # URLs from the current products in our shop
    test_urls = [
        {
            "name": "Test Team Jersey (Variant 18395)",
            "url": "https://images-api.printify.com/mockup/6864162ddc1c5f6b050eb4c1/18395/92547/custom-unisex-jersey-short-sleeve-tee-for-test-team.jpg?camera_label=front",
            "expected": "White/Default"
        },
        {
            "name": "Test Team Jersey (Variant 18486)",
            "url": "https://images-api.printify.com/mockup/68641c1278d26655fa0c7383/18486/92547/custom-unisex-jersey-short-sleeve-tee-for-test-team.jpg?camera_label=front",
            "expected": "Navy/Blue"
        },
        {
            "name": "Test Team Jersey (Variant 18395 from Product 2)",
            "url": "https://images-api.printify.com/mockup/68641c1278d26655fa0c7383/18395/92547/custom-unisex-jersey-short-sleeve-tee-for-test-team.jpg?camera_label=front",
            "expected": "White/Default"
        }
    ]
    
    results = []
    
    for test in test_urls:
        print(f"\n🔍 Analyzing: {test['name']}")
        print(f"   Expected: {test['expected']}")
        print(f"   URL: {test['url']}")
        
        # Download image
        image_data = download_image(test['url'])
        if not image_data:
            print("   ❌ Failed to download image")
            continue
        
        print(f"   ✅ Downloaded {len(image_data)} bytes")
        
        # Analyze colors
        colors = analyze_image_colors(image_data)
        if colors:
            print("   🎨 Dominant colors found:")
            for i, (color_name, rgb, percentage) in enumerate(colors[:5]):
                print(f"      {i+1}. {color_name}: {percentage:.1f}% {rgb}")
            
            # Determine the likely shirt color
            shirt_colors = [c for c in colors if c[2] > 5 and c[0] not in ['White']]  # Exclude white background
            if shirt_colors:
                likely_shirt_color = shirt_colors[0][0]
                print(f"   👕 Likely shirt color: {likely_shirt_color}")
            else:
                likely_shirt_color = "Unknown"
                print(f"   ❓ Could not determine shirt color")
            
            results.append({
                "name": test['name'],
                "expected": test['expected'],
                "detected": likely_shirt_color,
                "all_colors": colors[:3]
            })
        else:
            print("   ❌ Failed to analyze colors")
    
    # Summary
    print(f"\n📊 ANALYSIS SUMMARY")
    print("=" * 60)
    
    for result in results:
        print(f"\n{result['name']}:")
        print(f"   Expected: {result['expected']}")
        print(f"   Detected: {result['detected']}")
        
        # Check if colors match expectations
        expected = result['expected'].lower()
        detected = result['detected'].lower()
        
        if 'navy' in expected or 'blue' in expected:
            matches = 'blue' in detected
        elif 'red' in expected:
            matches = 'red' in detected
        elif 'black' in expected:
            matches = 'black' in detected
        elif 'white' in expected:
            matches = 'white' in detected
        else:
            matches = True  # Default case
        
        print(f"   Match: {'✅' if matches else '❌'}")
    
    # Final verdict
    all_match = all('blue' in r['detected'].lower() if 'blue' in r['expected'].lower() else
                   'red' in r['detected'].lower() if 'red' in r['expected'].lower() else True 
                   for r in results)
    
    print(f"\n🎯 FINAL VERDICT:")
    if all_match:
        print("✅ Colors are working correctly!")
    else:
        print("❌ Colors are NOT working - images don't match expected colors")
        print("   The mockup images are still showing wrong colors")

if __name__ == "__main__":
    test_mockup_colors()