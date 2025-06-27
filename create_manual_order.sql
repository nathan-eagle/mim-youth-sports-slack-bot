-- Manual order creation for your hat purchase
-- Run this ONLY if your order doesn't exist in Supabase

-- First check if order exists
SELECT 'Checking for existing order...' as status;
SELECT COUNT(*) as order_count FROM customer_orders 
WHERE id = 'c184bceb-859c-42a4-9818-d29eb85f3807';

-- If count is 0, create the order manually
-- UPDATE THESE VALUES WITH YOUR REAL INFO:

INSERT INTO customer_orders (
  id,
  first_name,
  last_name, 
  email,
  phone,
  total_amount,
  payment_status,
  fulfillment_status,
  stripe_payment_intent_id,
  created_at
) VALUES (
  'c184bceb-859c-42a4-9818-d29eb85f3807',
  'Your First Name',  -- UPDATE THIS
  'Your Last Name',   -- UPDATE THIS
  'your-email@domain.com',  -- UPDATE THIS
  '555-123-4567',     -- UPDATE THIS
  30.00,              -- Hat price
  'paid',
  'pending',
  'pi_your_payment_intent_id',  -- UPDATE THIS
  NOW()
) ON CONFLICT (id) DO NOTHING;

-- Create shipping address
INSERT INTO shipping_addresses (
  order_id,
  address1,
  address2,
  city,
  state,
  zip,
  country
) VALUES (
  'c184bceb-859c-42a4-9818-d29eb85f3807',
  'Your Street Address',  -- UPDATE THIS
  '',                     -- Apt/Suite (optional)
  'Your City',           -- UPDATE THIS  
  'Your State',          -- UPDATE THIS (CA, NY, etc.)
  'Your ZIP',            -- UPDATE THIS
  'US'
) ON CONFLICT (order_id) DO NOTHING;

-- Create order item
INSERT INTO order_items (
  order_id,
  product_design_id,
  quantity,
  unit_price,
  total_price
) VALUES (
  'c184bceb-859c-42a4-9818-d29eb85f3807',
  '89971e25-16ee-4c93-a9ba-f1dbc649520d',  -- Your hat design ID
  1,
  30.00,
  30.00
) ON CONFLICT (order_id, product_design_id) DO NOTHING;

-- Verify the order was created
SELECT 'Order created successfully!' as status;
SELECT * FROM customer_orders 
WHERE id = 'c184bceb-859c-42a4-9818-d29eb85f3807';

SELECT * FROM shipping_addresses
WHERE order_id = 'c184bceb-859c-42a4-9818-d29eb85f3807';

SELECT * FROM order_items
WHERE order_id = 'c184bceb-859c-42a4-9818-d29eb85f3807'; 