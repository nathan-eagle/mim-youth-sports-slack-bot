#!/usr/bin/env python3
"""
Test script to manually fulfill a Printify order
Run this to test the fulfillment process for your hat order
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_fulfillment():
    """Test the fulfillment process"""
    
    # Real order data for your hat purchase
    test_order_data = {
        "order_id": "c184bceb-859c-42a4-9818-d29eb85f3807",  # Your actual order ID
        "customer_info": {
            "first_name": "Customer",  # Update with your real info from Supabase
            "last_name": "Name", 
            "email": "your-email@domain.com",  # Update with your real email
            "phone": "555-123-4567",
            "address1": "Your Street Address",  # Update with your real address
            "address2": "",
            "city": "Your City",
            "state": "Your State",
            "zip": "Your ZIP",
            "country": "US"
        },
        "order_items": [
            {
                "design_id": "89971e25-16ee-4c93-a9ba-f1dbc649520d",  # Your hat design ID
                "quantity": 1,
                "unit_price": 30.00
            }
        ]
    }
    
    print("🧪 Testing Printify Fulfillment...")
    print(f"Order ID: {test_order_data['order_id']}")
    print(f"Design ID: {test_order_data['order_items'][0]['design_id']}")
    
    # Test the fulfillment endpoint
    try:
        response = requests.post(
            "http://localhost:5001/api/fulfill-printify-order",
            headers={"Content-Type": "application/json"},
            json=test_order_data,
            timeout=30
        )
        
        print(f"\n📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Fulfillment Success!")
            print(f"   Printify Order ID: {result.get('printify_order_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Total Cost: ${result.get('total_cost', 'N/A')}")
        else:
            print("❌ Fulfillment Failed!")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Failed!")
        print("   Make sure the Flask fulfillment service is running:")
        print("   python printify_fulfillment.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_via_storefront():
    """Test fulfillment via the Next.js storefront API"""
    
    storefront_url = os.getenv('NEXT_PUBLIC_DOMAIN', 'http://localhost:3000')
    
    test_data = {
        "order_id": "c184bceb-859c-42a4-9818-d29eb85f3807"  # Your actual order ID
    }
    
    print(f"\n🌐 Testing via storefront: {storefront_url}")
    
    try:
        response = requests.post(
            f"{storefront_url}/api/fulfill-order",
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=30
        )
        
        print(f"📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Storefront Fulfillment Success!")
            print(f"   Result: {result}")
        else:
            print("❌ Storefront Fulfillment Failed!")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def check_printify_service():
    """Test if Printify service is working"""
    from printify_service import PrintifyService
    
    print("\n🔧 Testing Printify Service...")
    
    try:
        service = PrintifyService()
        
        # Test getting available products
        products = service.get_available_products()
        print(f"✅ Found {len(products)} available products")
        
        # Show first few products
        for i, product in enumerate(products[:3]):
            print(f"   {i+1}. {product.get('title', 'Unknown')} (ID: {product.get('id')})")
            
    except Exception as e:
        print(f"❌ Printify Service Error: {e}")
        print("   Check your PRINTIFY_API_TOKEN environment variable")

if __name__ == "__main__":
    print("🚀 MiM Youth Sports - Printify Fulfillment Test")
    print("=" * 50)
    
    # Check Printify service first
    check_printify_service()
    
    # Test direct fulfillment
    test_fulfillment()
    
    # Test via storefront (uncomment when ready)
    # test_via_storefront()
    
    print("\n" + "=" * 50)
    print("💡 Next Steps:")
    print("1. Run: python printify_fulfillment.py")
    print("2. Update test_order_data with your real order ID")
    print("3. Make sure your Printify API token is valid")
    print("4. Test the complete flow!") 