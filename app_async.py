"""
Async FastAPI application for MiM Slack Bot
High-performance, scalable architecture with background processing
"""

import os
import asyncio
import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from core.services.slack_gateway import SlackEventGateway
from core.services.redis_state_manager import RedisStateManager
from core.services.background_processor import BackgroundEventProcessor
from core.services.performance_monitor import PerformanceMonitor
from core.config import Settings

# Load environment variables
load_dotenv()

# Configure structured logging
import structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global instances
settings = Settings()
state_manager: Optional[RedisStateManager] = None
event_processor: Optional[BackgroundEventProcessor] = None
performance_monitor: Optional[PerformanceMonitor] = None
slack_gateway: Optional[SlackEventGateway] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    Initialize and cleanup resources
    """
    global state_manager, event_processor, performance_monitor, slack_gateway
    
    logger.info("Starting MiM Slack Bot application")
    
    try:
        # Initialize core services
        state_manager = RedisStateManager(settings.redis_url)
        await state_manager.initialize()
        
        performance_monitor = PerformanceMonitor()
        await performance_monitor.initialize()
        
        event_processor = BackgroundEventProcessor(
            state_manager=state_manager,
            performance_monitor=performance_monitor
        )
        await event_processor.initialize()
        
        slack_gateway = SlackEventGateway(
            signing_secret=settings.slack_signing_secret,
            event_processor=event_processor,
            state_manager=state_manager
        )
        
        logger.info("All services initialized successfully")
        yield
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    finally:
        # Cleanup resources
        logger.info("Shutting down application")
        
        if event_processor:
            await event_processor.shutdown()
        if state_manager:
            await state_manager.shutdown()
        if performance_monitor:
            await performance_monitor.shutdown()


# Initialize FastAPI app with lifespan management
app = FastAPI(
    title="MiM Youth Sports Swag Bot",
    description="High-performance Slack bot for youth sports merchandise customization",
    version="2.0.0",
    lifespan=lifespan
)


def verify_slack_request(request_body: str, timestamp: str, signature: str) -> bool:
    """
    Verify that request came from Slack using HMAC signature
    
    Args:
        request_body: Raw request body as string
        timestamp: X-Slack-Request-Timestamp header
        signature: X-Slack-Signature header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not settings.slack_signing_secret:
        logger.warning("SLACK_SIGNING_SECRET not set - skipping verification")
        return True
    
    # Create expected signature
    sig_basestring = f'v0:{timestamp}:{request_body}'
    expected_signature = 'v0=' + hmac.new(
        settings.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(expected_signature, signature)


@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Slack Events API with immediate response and background processing
    
    This endpoint provides immediate acknowledgment to Slack while processing
    events in the background to avoid timeout issues.
    """
    async with performance_monitor.track_operation("slack_event_handling"):
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
            
            # Handle event callbacks
            if data.get('type') == 'event_callback':
                # Process event through gateway (includes deduplication)
                should_process = await slack_gateway.should_process_event(data)
                
                if should_process:
                    # Queue for background processing
                    background_tasks.add_task(
                        event_processor.process_event,
                        data
                    )
                    logger.info("Event queued for background processing", 
                               event_id=data.get('event_id'))
                else:
                    logger.info("Event skipped (duplicate or ignored)", 
                               event_id=data.get('event_id'))
            
            # Return immediate response to Slack
            return JSONResponse({"status": "ok"})
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error("Error handling Slack event", error=str(e))
            raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """
    Health check endpoint with service status
    
    Returns:
        Service health status and component availability
    """
    health_status = {
        "status": "healthy",
        "service": "MiM Youth Sports Swag Bot",
        "version": "2.0.0",
        "timestamp": None
    }
    
    # Check component health
    components = {}
    
    try:
        if state_manager:
            components["redis"] = await state_manager.health_check()
        if event_processor:
            components["background_processor"] = await event_processor.health_check()
        if performance_monitor:
            components["performance_monitor"] = await performance_monitor.health_check()
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        health_status["status"] = "degraded"
    
    health_status["components"] = components
    
    return JSONResponse(health_status)


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns:
        Performance metrics in Prometheus format
    """
    if not performance_monitor:
        raise HTTPException(status_code=503, detail="Metrics not available")
    
    metrics_data = await performance_monitor.get_metrics()
    return JSONResponse(metrics_data)


@app.get("/")
async def home():
    """
    Home endpoint with API information
    
    Returns:
        Service information and available endpoints
    """
    return JSONResponse({
        "service": "MiM Youth Sports Team Swag Bot",
        "description": "High-performance Slack bot for youth sports merchandise customization",
        "version": "2.0.0",
        "architecture": "async",
        "endpoints": {
            "slack_events": "/slack/events",
            "health": "/health",
            "metrics": "/metrics"
        },
        "features": [
            "Async processing",
            "Background task queue",
            "Redis state management",
            "Performance monitoring",
            "AI-powered product recommendations"
        ]
    })


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url.path)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error("Internal server error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("Starting MiM Youth Sports Swag Bot", port=port, debug=debug)
    
    uvicorn.run(
        "app_async:app",
        host='0.0.0.0',
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )