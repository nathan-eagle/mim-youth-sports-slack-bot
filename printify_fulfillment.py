import os
import logging
from flask import Flask, request, jsonify
from printify_service import PrintifyService
from database_service import DatabaseService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
printify_service = PrintifyService()
db_service = DatabaseService()

app = Flask(__name__)

@app.route('/api/fulfill-printify-order', methods=['POST'])
def fulfill_printify_order():
    """Handle Printify order fulfillment from Next.js storefront"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        order_id = data.get('order_id')
        customer_info = data.get('customer_info')
        order_items = data.get('order_items')
        
        if not all([order_id, customer_info, order_items]):
            return jsonify({"error": "Missing required fields"}), 400
        
        logger.info(f"Processing Printify fulfillment for order {order_id}")
        
        # For now, we'll create a basic line item
        # In a full implementation, you'd get the design details and create proper line items
        line_items = []
        
        for item in order_items:
            # This is a simplified version - you'll need to map your designs to Printify products
            # For now, let's create a basic hat order
            line_item_result = printify_service.create_line_item_for_blueprint(
                blueprint_id=5,  # Snapback trucker cap
                print_provider_id=1,  # Generic provider - you'll need to get actual IDs
                variant_id=17007,  # One size fits most - you'll need actual variant IDs
                image_id="your-uploaded-image-id",  # You'll need to get this from your design
                quantity=item['quantity']
            )
            
            if line_item_result.get('success'):
                line_items.append(line_item_result['line_item'])
            else:
                logger.error(f"Failed to create line item: {line_item_result.get('error')}")
                return jsonify({
                    "success": False,
                    "error": f"Failed to create line item: {line_item_result.get('error')}"
                }), 500
        
        if not line_items:
            return jsonify({
                "success": False,
                "error": "No valid line items could be created"
            }), 500
        
        # Create the Printify order
        order_result = printify_service.create_order(
            customer_info=customer_info,
            line_items=line_items
        )
        
        if order_result.get('success'):
            printify_order_id = order_result['order_id']
            
            # Update our database with the Printify order ID
            db_service.update_order_printify_id(order_id, printify_order_id)
            
            logger.info(f"Successfully created Printify order {printify_order_id} for order {order_id}")
            
            return jsonify({
                "success": True,
                "printify_order_id": printify_order_id,
                "status": order_result.get('status'),
                "total_cost": order_result.get('total_cost')
            })
        else:
            logger.error(f"Printify order creation failed: {order_result.get('error')}")
            return jsonify({
                "success": False,
                "error": order_result.get('error')
            }), 500
            
    except Exception as e:
        logger.error(f"Error in fulfill_printify_order: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/check-order-status/<order_id>', methods=['GET'])
def check_order_status(order_id):
    """Check the status of a Printify order"""
    try:
        # Get order from our database
        order_data = db_service.get_order_by_id(order_id)
        
        if not order_data:
            return jsonify({"error": "Order not found"}), 404
        
        printify_order_id = order_data.get('printify_order_id')
        
        if not printify_order_id:
            return jsonify({
                "order_id": order_id,
                "status": "pending_fulfillment",
                "message": "Order not yet sent to Printify"
            })
        
        # Get status from Printify
        status_result = printify_service.get_order_status(printify_order_id)
        
        if status_result.get('success'):
            return jsonify({
                "order_id": order_id,
                "printify_order_id": printify_order_id,
                "status": status_result.get('status'),
                "tracking_number": status_result.get('tracking_number'),
                "carrier": status_result.get('carrier')
            })
        else:
            return jsonify({
                "error": "Failed to get order status from Printify"
            }), 500
            
    except Exception as e:
        logger.error(f"Error checking order status: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Printify Fulfillment Service"
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 