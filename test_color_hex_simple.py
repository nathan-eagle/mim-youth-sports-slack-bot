#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_color_structure():
    """Simple test to see exact API response structure"""
    
    api_token = os.getenv('PRINTIFY_API_TOKEN')
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Test blueprint 12 (Jersey Tee)
    blueprint_id = 12
    
    print(f"🔍 Testing Blueprint {blueprint_id} structure:")
    
    # Get blueprint details
    blueprint_url = f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}.json"
    response = requests.get(blueprint_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📋 Blueprint response keys: {list(data.keys())}")
        
        # Show actual structure
        if 'options' in data:
            print(f"\n🎨 Options structure:")
            for i, option in enumerate(data['options'][:2]):  # Show first 2 options
                print(f"   Option {i+1}: {json.dumps(option, indent=2)[:300]}...")
        else:
            print("❌ No 'options' key found")
    
    # Test variants endpoint
    print(f"\n🔍 Testing variants structure:")
    variants_url = f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers/99/variants.json"
    response = requests.get(variants_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"📦 Variants response type: {type(data)}")
        
        if isinstance(data, dict):
            print(f"📦 Variants response keys: {list(data.keys())}")
            if 'variants' in data:
                variants = data['variants']
            else:
                variants = []
        elif isinstance(data, list):
            variants = data
            print(f"📦 Direct list of {len(variants)} variants")
        else:
            variants = []
        
        if variants:
            print(f"\n🎯 First variant structure:")
            first_variant = variants[0]
            print(f"   Type: {type(first_variant)}")
            if isinstance(first_variant, dict):
                print(f"   Keys: {list(first_variant.keys())}")
                print(f"   Sample: {json.dumps(first_variant, indent=2)[:500]}...")
            else:
                print(f"   Value: {first_variant}")

if __name__ == "__main__":
    test_color_structure()