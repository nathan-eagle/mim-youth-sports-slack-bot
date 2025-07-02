"""
Simple FastAPI app for MiM Slack Bot with direct fallback
No complex async services - just works with existing slack_bot
"""

import os
import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple FastAPI app
app = FastAPI(
    title="MiM Youth Sports Swag Bot",
    description="Slack bot for youth sports merchandise customization",
    version="2.0.0"
)

def verify_slack_request(request_body: str, timestamp: str, signature: str) -> bool:
    """Verify that request came from Slack using HMAC signature"""
    signing_secret = os.getenv('SLACK_SIGNING_SECRET')
    
    if not signing_secret:
        logger.warning("SLACK_SIGNING_SECRET not set - skipping verification")
        return True
    
    # Create expected signature
    sig_basestring = f'v0:{timestamp}:{request_body}'
    expected_signature = 'v0=' + hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)


@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack Events API using existing slack_bot"""
    try:
        # Get request data
        request_body = await request.body()
        request_body_str = request_body.decode('utf-8')
        timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
        signature = request.headers.get('X-Slack-Signature', '')
        
        # Verify request signature
        if not verify_slack_request(request_body_str, timestamp, signature):
            logger.warning("Invalid Slack signature received")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse JSON
        try:
            data = json.loads(request_body_str)
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in request", error=str(e))
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Handle URL verification challenge
        if data.get('type') == 'url_verification':
            logger.info("Handling URL verification challenge")
            return JSONResponse({"challenge": data.get('challenge')})
        
        # Handle event callbacks using existing slack_bot
        if data.get('type') == 'event_callback':
            # Process in background to avoid timeout
            background_tasks.add_task(process_slack_event, data)
            logger.info("Event queued for background processing", 
                       event_id=data.get('event_id'))
        
        # Return immediate response to Slack
        return JSONResponse({"status": "ok"})
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Error handling Slack event", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_slack_event(data: Dict[str, Any]):
    """Process Slack event using existing slack_bot"""
    try:
        # Import and use existing slack_bot
        from slack_bot import slack_bot
        result = slack_bot.handle_event(data)
        logger.info("Handled event successfully", result=result)
    except Exception as e:
        logger.error("Error processing Slack event in background", error=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "MiM Youth Sports Swag Bot",
        "version": "2.0.0-simple",
        "mode": "direct_processing"
    })


@app.get("/metrics")
async def metrics():
    """Simple metrics endpoint"""
    return JSONResponse({
        "service": "MiM Slack Bot",
        "version": "2.0.0-simple",
        "status": "running",
        "mode": "direct_processing"
    })


@app.get("/")
async def home():
    """Home endpoint"""
    return JSONResponse({
        "service": "MiM Youth Sports Team Swag Bot",
        "description": "Slack bot for youth sports merchandise customization",
        "version": "2.0.0-simple",
        "mode": "direct_processing",
        "endpoints": {
            "slack_events": "/slack/events",
            "health": "/health",
            "metrics": "/metrics"
        }
    })


if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run("app_simple:app", host='0.0.0.0', port=port)