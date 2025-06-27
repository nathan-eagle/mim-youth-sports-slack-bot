-- Add fulfillment tracking columns to customer_orders table

ALTER TABLE customer_orders 
ADD COLUMN IF NOT EXISTS printify_order_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS fulfillment_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(100),
ADD COLUMN IF NOT EXISTS carrier VARCHAR(50),
ADD COLUMN IF NOT EXISTS shipped_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITH TIME ZONE;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_customer_orders_printify_id ON customer_orders(printify_order_id);
CREATE INDEX IF NOT EXISTS idx_customer_orders_fulfillment_status ON customer_orders(fulfillment_status);

-- Update existing orders to have pending fulfillment status
UPDATE customer_orders 
SET fulfillment_status = 'pending' 
WHERE fulfillment_status IS NULL; 