"""
Slack Event Gateway for MiM Bot
Handles event processing, deduplication, and routing with rate limiting
"""

import asyncio
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
import structlog

from .supabase_state_manager import SupabaseStateManager
from .performance_monitor import PerformanceMonitor

logger = structlog.get_logger(__name__)


class SlackEventGateway:
    """
    Gateway for processing Slack events with:
    - Event deduplication using Redis
    - Rate limiting per user/channel
    - Event type filtering and routing
    - Performance monitoring
    - Circuit breaker for overloaded systems
    """
    
    def __init__(
        self,
        signing_secret: str,
        event_processor,  # BackgroundEventProcessor
        state_manager: SupabaseStateManager,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """
        Initialize Slack event gateway
        
        Args:
            signing_secret: Slack signing secret for verification
            event_processor: Background event processor instance
            state_manager: Supabase state manager
            performance_monitor: Performance monitoring instance
        """
        self.signing_secret = signing_secret
        self.event_processor = event_processor
        self.state_manager = state_manager
        self.performance_monitor = performance_monitor
        
        # Event filtering configuration
        self.IGNORED_SUBTYPES = {
            'bot_message',
            'message_changed', 
            'message_deleted',
            'channel_join',
            'channel_leave'
        }
        
        self.SUPPORTED_EVENT_TYPES = {
            'message',
            'file_shared'
        }
        
        # Rate limiting configuration
        self.RATE_LIMITS = {
            'per_user_per_minute': 10,
            'per_channel_per_minute': 20,
            'global_per_minute': 100
        }
        
        # Rate limiting tracking
        self._rate_limit_windows: Dict[str, List[datetime]] = {}
        
        # Circuit breaker state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 10
        self._circuit_breaker_open = False
        self._circuit_breaker_last_failure = None
        
        logger.info("Slack event gateway initialized")
    
    async def should_process_event(self, event_data: Dict[str, Any]) -> bool:
        """
        Determine if event should be processed
        
        Checks:
        - Event deduplication
        - Event type filtering  
        - Rate limiting
        - Circuit breaker status
        
        Args:
            event_data: Slack event data
            
        Returns:
            True if event should be processed, False otherwise
        """
        async with self.performance_monitor.track_operation("event_filtering") if self.performance_monitor else self._null_context():
            try:
                # Check circuit breaker
                if self._circuit_breaker_open:
                    await self._check_circuit_breaker_recovery()
                    if self._circuit_breaker_open:
                        logger.warning("Circuit breaker open, rejecting event")
                        return False
                
                # Extract event info
                event = event_data.get('event', {})
                event_type = event.get('type')
                event_subtype = event.get('subtype')
                user_id = event.get('user')
                channel_id = event.get('channel')
                
                # Filter by event type
                if not self._should_process_event_type(event_type, event_subtype):
                    logger.debug("Event type filtered out", 
                               event_type=event_type, subtype=event_subtype)
                    return False
                
                # Check for duplicates
                is_duplicate = await self.state_manager.is_event_duplicate(event_data)
                if is_duplicate:
                    logger.debug("Duplicate event detected", event_id=event_data.get('event_id'))
                    return False
                
                # Check rate limits
                if not await self._check_rate_limits(user_id, channel_id):
                    logger.warning("Rate limit exceeded", 
                                 user=user_id, channel=channel_id)
                    return False
                
                # Event passes all checks
                logger.debug("Event approved for processing", 
                           event_type=event_type, user=user_id, channel=channel_id)
                
                return True
                
            except Exception as e:
                logger.error("Error in event filtering", error=str(e))
                await self._record_circuit_breaker_failure()
                return False
    
    def _should_process_event_type(self, event_type: str, event_subtype: Optional[str]) -> bool:
        """
        Check if event type should be processed
        
        Args:
            event_type: Type of Slack event
            event_subtype: Subtype of event (if any)
            
        Returns:
            True if event should be processed
        """
        # Skip unsupported event types
        if event_type not in self.SUPPORTED_EVENT_TYPES:
            return False
        
        # Skip ignored subtypes
        if event_subtype in self.IGNORED_SUBTYPES:
            return False
        
        return True
    
    async def _check_rate_limits(self, user_id: Optional[str], channel_id: Optional[str]) -> bool:
        """
        Check if event is within rate limits
        
        Args:
            user_id: Slack user ID
            channel_id: Slack channel ID
            
        Returns:
            True if within rate limits
        """
        current_time = datetime.utcnow()
        minute_ago = current_time - timedelta(minutes=1)
        
        # Clean old entries
        await self._cleanup_rate_limit_windows(minute_ago)
        
        # Check user rate limit
        if user_id:
            user_key = f"user:{user_id}"
            user_requests = self._rate_limit_windows.get(user_key, [])
            recent_user_requests = [t for t in user_requests if t > minute_ago]
            
            if len(recent_user_requests) >= self.RATE_LIMITS['per_user_per_minute']:
                return False
            
            # Record this request
            self._rate_limit_windows[user_key] = recent_user_requests + [current_time]
        
        # Check channel rate limit
        if channel_id:
            channel_key = f"channel:{channel_id}"
            channel_requests = self._rate_limit_windows.get(channel_key, [])
            recent_channel_requests = [t for t in channel_requests if t > minute_ago]
            
            if len(recent_channel_requests) >= self.RATE_LIMITS['per_channel_per_minute']:
                return False
            
            # Record this request
            self._rate_limit_windows[channel_key] = recent_channel_requests + [current_time]
        
        # Check global rate limit
        global_key = "global"
        global_requests = self._rate_limit_windows.get(global_key, [])
        recent_global_requests = [t for t in global_requests if t > minute_ago]
        
        if len(recent_global_requests) >= self.RATE_LIMITS['global_per_minute']:
            return False
        
        # Record this request
        self._rate_limit_windows[global_key] = recent_global_requests + [current_time]
        
        return True
    
    async def _cleanup_rate_limit_windows(self, cutoff_time: datetime):
        """Clean up old rate limit tracking data"""
        for key in list(self._rate_limit_windows.keys()):
            self._rate_limit_windows[key] = [
                t for t in self._rate_limit_windows[key] if t > cutoff_time
            ]
            
            # Remove empty entries
            if not self._rate_limit_windows[key]:
                del self._rate_limit_windows[key]
    
    async def _record_circuit_breaker_failure(self):
        """Record a failure for circuit breaker logic"""
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = datetime.utcnow()
        
        if self._circuit_breaker_failures >= self._circuit_breaker_threshold:
            self._circuit_breaker_open = True
            logger.warning("Circuit breaker opened", 
                          failures=self._circuit_breaker_failures)
    
    async def _check_circuit_breaker_recovery(self):
        """Check if circuit breaker should be reset"""
        if (self._circuit_breaker_last_failure and 
            datetime.utcnow() - self._circuit_breaker_last_failure > timedelta(minutes=5)):
            
            self._circuit_breaker_open = False
            self._circuit_breaker_failures = 0
            self._circuit_breaker_last_failure = None
            
            logger.info("Circuit breaker reset")
    
    async def get_gateway_stats(self) -> Dict[str, Any]:
        """Get gateway performance statistics"""
        current_time = datetime.utcnow()
        minute_ago = current_time - timedelta(minutes=1)
        
        # Count recent requests by type
        stats = {
            "circuit_breaker": {
                "open": self._circuit_breaker_open,
                "failures": self._circuit_breaker_failures,
                "last_failure": self._circuit_breaker_last_failure.isoformat() if self._circuit_breaker_last_failure else None
            },
            "rate_limits": {},
            "active_windows": len(self._rate_limit_windows),
            "total_recent_requests": 0
        }
        
        # Calculate rate limit usage
        for key, timestamps in self._rate_limit_windows.items():
            recent_requests = [t for t in timestamps if t > minute_ago]
            
            if key.startswith("user:"):
                limit_type = "per_user_per_minute"
            elif key.startswith("channel:"):
                limit_type = "per_channel_per_minute"
            else:
                limit_type = "global_per_minute"
            
            if limit_type not in stats["rate_limits"]:
                stats["rate_limits"][limit_type] = {
                    "current_usage": 0,
                    "limit": self.RATE_LIMITS[limit_type],
                    "active_keys": 0
                }
            
            stats["rate_limits"][limit_type]["current_usage"] = max(
                stats["rate_limits"][limit_type]["current_usage"],
                len(recent_requests)
            )
            stats["rate_limits"][limit_type]["active_keys"] += 1
            stats["total_recent_requests"] += len(recent_requests)
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Check gateway health"""
        try:
            stats = await self.get_gateway_stats()
            
            health_status = {
                "status": "healthy",
                "circuit_breaker_open": self._circuit_breaker_open,
                "rate_limit_exceeded": False,
                "performance": stats
            }
            
            # Check if any rate limits are close to being exceeded
            for limit_type, limit_data in stats["rate_limits"].items():
                usage_percent = (limit_data["current_usage"] / limit_data["limit"]) * 100
                if usage_percent > 80:
                    health_status["rate_limit_exceeded"] = True
                    health_status["status"] = "degraded"
            
            if self._circuit_breaker_open:
                health_status["status"] = "degraded"
            
            return health_status
            
        except Exception as e:
            logger.error("Gateway health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _null_context(self):
        """Null context manager for when performance monitor is not available"""
        class NullContext:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        return NullContext()


class EventRouter:
    """
    Routes processed events to appropriate handlers
    """
    
    def __init__(self):
        """Initialize event router"""
        self.handlers: Dict[str, List[callable]] = {}
        
        logger.info("Event router initialized")
    
    def register_handler(self, event_type: str, handler: callable):
        """
        Register handler for event type
        
        Args:
            event_type: Type of event to handle
            handler: Async handler function
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        
        logger.debug("Handler registered", event_type=event_type, handler=handler.__name__)
    
    async def route_event(self, event_data: Dict[str, Any]) -> List[Any]:
        """
        Route event to registered handlers
        
        Args:
            event_data: Slack event data
            
        Returns:
            List of handler results
        """
        event_type = event_data.get('event', {}).get('type')
        
        if event_type not in self.handlers:
            logger.debug("No handlers for event type", event_type=event_type)
            return []
        
        # Execute all handlers for this event type
        handlers = self.handlers[event_type]
        tasks = []
        
        for handler in handlers:
            try:
                task = asyncio.create_task(handler(event_data))
                tasks.append(task)
            except Exception as e:
                logger.error("Failed to create handler task", 
                           handler=handler.__name__, error=str(e))
        
        # Wait for all handlers to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error("Handler failed", 
                               handler=handlers[i].__name__, 
                               error=str(result))
            
            return results
        
        return []