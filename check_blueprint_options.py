#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_blueprint_options():
    """Check if blueprint options contain hex color information"""
    
    api_token = os.getenv('PRINTIFY_API_TOKEN')
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Get blueprint with print provider details
    blueprint_id = 12
    provider_id = 99
    
    # Try the print provider specific endpoint
    print("🔍 Checking print provider specific blueprint options...")
    provider_blueprint_url = f"https://api.printify.com/v1/catalog/blueprints/{blueprint_id}/print_providers/{provider_id}.json"
    
    response = requests.get(provider_blueprint_url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Provider blueprint response keys: {list(data.keys())}")
        
        # Look for variant options or color information
        if 'variant_options' in data:
            print(f"\n🎨 Variant options found:")
            variant_options = data['variant_options']
            for option in variant_options:
                print(f"   Option: {json.dumps(option, indent=2)[:300]}...")
        
        if 'options' in data:
            print(f"\n🎨 Options found:")
            options = data['options']
            for option in options:
                print(f"   Option: {json.dumps(option, indent=2)[:400]}...")
        
        # Show full response structure (first 1000 chars)
        print(f"\n📋 Full response preview:")
        print(json.dumps(data, indent=2)[:1000] + "...")
    
    else:
        print(f"❌ Provider blueprint request failed: {response.status_code}")
        print(f"Response: {response.text[:200]}")

if __name__ == "__main__":
    check_blueprint_options()