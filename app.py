import os
import logging
import hashlib
import hmac
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from slack_bot.bot import slack_bot

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Slack signing secret for request verification
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

# Simple in-memory event deduplication (in production, use Redis)
processed_events = set()

def verify_slack_request(request_body, timestamp, signature):
    """Verify that request came from Slack"""
    if not SLACK_SIGNING_SECRET:
        logger.warning("SLACK_SIGNING_SECRET not set - skipping verification")
        return True
    
    # Create expected signature
    sig_basestring = f'v0:{timestamp}:{request_body}'
    expected_signature = 'v0=' + hmac.new(
        SLACK_SIGNING_SECRET.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)

@app.route('/slack/events', methods=['POST'])
def slack_events():
    """Handle Slack Events API"""
    try:
        # Get request data
        request_body = request.get_data(as_text=True)
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        signature = request.headers.get('X-Slack-Signature', '')
        
        # Verify request
        if not verify_slack_request(request_body, timestamp, signature):
            logger.warning("Invalid Slack signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # Parse JSON
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in request")
            return jsonify({"error": "Invalid JSON"}), 400
        
        # Handle URL verification challenge
        if data.get('type') == 'url_verification':
            logger.info("Handling URL verification challenge")
            return jsonify({"challenge": data.get('challenge')})
        
        # Handle event callbacks
        if data.get('type') == 'event_callback':
            event = data.get('event', {})
            event_type = event.get('type')
            
            # Event deduplication using both event_id and a hash of the event content
            event_id = data.get('event_id', '')
            event_hash = str(hash(str(event.get('ts', '')) + str(event.get('user', '')) + str(event.get('text', ''))))
            
            # Create composite key for deduplication
            dedup_key = f"{event_id}_{event_hash}" if event_id else event_hash
            
            if dedup_key in processed_events:
                logger.info(f"Skipping duplicate event: {dedup_key}")
                return jsonify({"status": "ignored"})
            
            processed_events.add(dedup_key)
            # Keep only recent 1000 events to prevent memory bloat
            if len(processed_events) > 1000:
                processed_events.clear()
            
            logger.info(f"Received event: {event_type}")
            
            if event_type == 'message':
                # Skip message subtypes we don't want to handle
                if event.get('subtype') in ['bot_message', 'message_changed', 'message_deleted']:
                    return jsonify({"status": "ignored"})
                
                # Handle regular message
                result = slack_bot.handle_message(event)
                logger.info(f"Message handling result: {result}")
                
            elif event_type == 'file_shared':
                # Handle file upload - add channel info from parent data
                event['channel'] = event.get('channel_id') or data.get('event', {}).get('channel')
                result = slack_bot.handle_file_share(event)
                logger.info(f"File share handling result: {result}")
            
            else:
                logger.info(f"Unhandled event type: {event_type}")
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with conversation state info"""
    from conversation_manager import conversation_manager
    import time
    
    # Get conversation stats
    conversations = conversation_manager.conversations
    active_conversations = 0
    conversations_with_logos = 0
    
    current_time = time.time()
    for conv in conversations.values():
        # Count active conversations (within last 24 hours)
        if (current_time - conv.get('last_activity', 0)) < (24 * 60 * 60):
            active_conversations += 1
        
        # Count conversations with logos
        if conv.get('logo_info') and conv['logo_info'].get('printify_image_id'):
            conversations_with_logos += 1
    
    return jsonify({
        "status": "healthy",
        "service": "MiM Youth Sports Swag Bot",
        "version": "1.0.0",
        "timestamp": time.time(),
        "conversation_stats": {
            "total_conversations": len(conversations),
            "active_24h": active_conversations,
            "with_logos": conversations_with_logos
        }
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint with basic info"""
    return jsonify({
        "service": "MiM Youth Sports Team Swag Bot",
        "description": "A Slack bot that helps parents customize youth sports team merchandise",
        "version": "1.0.0",
        "endpoints": {
            "slack_events": "/slack/events",
            "health": "/health"
        }
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting MiM Youth Sports Swag Bot on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    # Start keep-alive service if production URL is set
    if not debug:
        try:
            from keep_alive import start_keep_alive
            start_keep_alive()
        except Exception as e:
            logger.warning(f"Could not start keep-alive service: {e}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    ) 