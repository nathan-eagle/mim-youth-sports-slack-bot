#!/usr/bin/env python3
"""
Fulfill your actual hat order
Order ID: c184bceb-859c-42a4-9818-d29eb85f3807
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def get_order_from_supabase():
    """Get order details from Supabase"""
    
    order_id = "c184bceb-859c-42a4-9818-d29eb85f3807"
    
    print(f"🔍 Looking up order: {order_id}")
    print("\n📋 SQL Query to run in Supabase:")
    print(f"""
-- Get order details
SELECT 
  id, first_name, last_name, email, phone, 
  total_amount, payment_status, fulfillment_status,
  created_at, printify_order_id
FROM customer_orders 
WHERE id = '{order_id}';

-- Get shipping address  
SELECT 
  address1, address2, city, state, zip, country
FROM shipping_addresses 
WHERE order_id = '{order_id}';

-- Get order items
SELECT 
  product_design_id, quantity, unit_price, total_price
FROM order_items 
WHERE order_id = '{order_id}';
""")
    
    return order_id

def fulfill_via_storefront():
    """Fulfill order via your Next.js storefront API"""
    
    order_id = "c184bceb-859c-42a4-9818-d29eb85f3807"
    storefront_url = "https://mim-drop.vercel.app"  # Your production URL
    
    print(f"🌐 Fulfilling via storefront: {storefront_url}")
    print(f"📦 Order ID: {order_id}")
    
    try:
        response = requests.post(
            f"{storefront_url}/api/fulfill-order",
            headers={
                "Content-Type": "application/json",
                "User-Agent": "MiM-Fulfillment-Test/1.0"
            },
            json={"order_id": order_id},
            timeout=60
        )
        
        print(f"📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Fulfillment Success!")
            print(f"   ✓ Printify Order ID: {result.get('printify_order_id')}")
            print(f"   ✓ Status: {result.get('status')}")
            print(f"   ✓ Message: {result.get('message', 'Order fulfilled')}")
            
            if result.get('printify_order_id'):
                print(f"\n🎯 Next Steps:")
                print(f"   1. Your hat is now in Printify's production queue!")
                print(f"   2. Production time: 2-7 business days")
                print(f"   3. Shipping time: 3-5 business days")
                print(f"   4. Total delivery: 5-12 business days")
                print(f"\n📋 Printify Order ID: {result.get('printify_order_id')}")
                print(f"   - Save this ID to track your order in Printify dashboard")
            
        elif response.status_code == 400:
            error_data = response.json()
            print("⚠️  Order Issue:")
            print(f"   Error: {error_data.get('error')}")
            
        elif response.status_code == 404:
            print("❌ Order Not Found!")
            print("   - Check if the order ID exists in Supabase")
            print("   - Verify the order was paid successfully")
            
        else:
            print("❌ Fulfillment Failed!")
            error_text = response.text
            print(f"   Status: {response.status_code}")
            print(f"   Error: {error_text}")
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out - this might be normal for fulfillment")
        print("   Check your order status in a few minutes")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Failed!")
        print("   - Check if your storefront is deployed and accessible")
        print(f"   - Verify URL: {storefront_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_order_status():
    """Check the status of your order"""
    
    order_id = "c184bceb-859c-42a4-9818-d29eb85f3807"
    storefront_url = "https://mim-drop.vercel.app"
    
    print(f"\n📊 Checking order status...")
    
    try:
        response = requests.get(
            f"{storefront_url}/api/check-order-status/{order_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("📋 Order Status:")
            print(f"   Order ID: {result.get('order_id')}")
            print(f"   Status: {result.get('status')}")
            print(f"   Printify Order: {result.get('printify_order_id', 'Not yet fulfilled')}")
            
            if result.get('tracking_number'):
                print(f"   Tracking: {result.get('tracking_number')}")
                print(f"   Carrier: {result.get('carrier')}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Status check error: {e}")

if __name__ == "__main__":
    print("🎩 MiM Youth Sports - Fulfill Your Hat Order!")
    print("=" * 55)
    
    # Step 1: Show how to check Supabase
    order_id = get_order_from_supabase()
    
    print("\n" + "=" * 55)
    print("🚀 Ready to fulfill your order?")
    user_input = input("Press ENTER to fulfill your hat order (or 'q' to quit): ")
    
    if user_input.lower() != 'q':
        # Step 2: Fulfill the order
        fulfill_via_storefront()
        
        print("\n" + "=" * 55)
        print("⏱️  Waiting 5 seconds before checking status...")
        import time
        time.sleep(5)
        
        # Step 3: Check status
        check_order_status()
    
    print("\n" + "=" * 55)
    print("🎯 Summary:")
    print(f"   • Order ID: {order_id}")
    print(f"   • Product: Team Snapback Trucker Cap")
    print(f"   • Design: 89971e25-16ee-4c93-a9ba-f1dbc649520d")
    print("   • Next: Check Printify dashboard for production updates!") 