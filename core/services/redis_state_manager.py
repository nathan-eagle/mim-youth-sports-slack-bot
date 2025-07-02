"""
Redis-based state management for conversation tracking
High-performance replacement for file-based state storage
"""

import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
import structlog

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

logger = structlog.get_logger(__name__)


class RedisStateManager:
    """
    High-performance Redis-based state management for conversations
    
    Features:
    - Automatic expiration of old conversations
    - Atomic operations with pipelines  
    - Connection pooling for performance
    - Event deduplication with rolling cleanup
    - Health monitoring and circuit breaker
    """
    
    def __init__(self, redis_url: str, max_connections: int = 20):
        """
        Initialize Redis state manager
        
        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connections in pool
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.pool: Optional[ConnectionPool] = None
        self.redis: Optional[redis.Redis] = None
        
        # Key prefixes for different data types
        self.CONVERSATION_PREFIX = "conv"
        self.EVENT_DEDUP_PREFIX = "event_dedup"
        self.METRICS_PREFIX = "metrics"
        self.TEMP_DATA_PREFIX = "temp"
        
        # Configuration
        self.default_conversation_ttl = 86400  # 24 hours
        self.event_dedup_ttl = 3600  # 1 hour
        self.max_dedup_events = 10000  # Maximum events to track
        
        # Health tracking
        self._connection_failures = 0
        self._max_failures = 5
        self._circuit_open = False
        self._last_failure_time = None
        
    async def initialize(self):
        """Initialize Redis connection pool and test connectivity"""
        try:
            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                decode_responses=True
            )
            
            # Create Redis client
            self.redis = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.redis.ping()
            
            logger.info("Redis state manager initialized successfully",
                       url=self.redis_url, max_connections=self.max_connections)
            
            # Start background cleanup task
            asyncio.create_task(self._background_cleanup())
            
        except Exception as e:
            logger.error("Failed to initialize Redis state manager", error=str(e))
            raise
    
    async def shutdown(self):
        """Cleanup Redis connections"""
        try:
            if self.redis:
                await self.redis.close()
            if self.pool:
                await self.pool.disconnect()
            logger.info("Redis state manager shutdown complete")
        except Exception as e:
            logger.error("Error during Redis shutdown", error=str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis health and connectivity
        
        Returns:
            Health status information
        """
        if self._circuit_open:
            return {
                "status": "circuit_open",
                "healthy": False,
                "failures": self._connection_failures,
                "last_failure": self._last_failure_time
            }
        
        try:
            # Test basic operations
            start_time = datetime.utcnow()
            await self.redis.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Get pool info
            pool_info = {
                "created_connections": self.pool.created_connections,
                "available_connections": len(self.pool._available_connections),
                "in_use_connections": len(self.pool._in_use_connections)
            }
            
            return {
                "status": "healthy",
                "healthy": True,
                "response_time_ms": response_time * 1000,
                "connection_pool": pool_info,
                "failures": self._connection_failures
            }
            
        except Exception as e:
            await self._handle_redis_error(e)
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e),
                "failures": self._connection_failures
            }
    
    async def _handle_redis_error(self, error: Exception):
        """Handle Redis connection errors with circuit breaker logic"""
        self._connection_failures += 1
        self._last_failure_time = datetime.utcnow().isoformat()
        
        logger.error("Redis operation failed", 
                    error=str(error), 
                    failures=self._connection_failures)
        
        # Open circuit breaker if too many failures
        if self._connection_failures >= self._max_failures:
            self._circuit_open = True
            logger.warning("Redis circuit breaker opened", 
                          failures=self._connection_failures)
    
    async def _reset_circuit_breaker(self):
        """Reset circuit breaker after successful operation"""
        if self._circuit_open or self._connection_failures > 0:
            self._circuit_open = False
            self._connection_failures = 0
            self._last_failure_time = None
            logger.info("Redis circuit breaker reset")
    
    def _get_conversation_key(self, channel_id: str, user_id: str) -> str:
        """Get Redis key for conversation state"""
        return f"{self.CONVERSATION_PREFIX}:{channel_id}:{user_id}"
    
    def _get_event_dedup_key(self, event_data: Dict[str, Any]) -> str:
        """Generate deduplication key for event"""
        # Create hash from event content
        event_content = {
            'event_id': event_data.get('event_id', ''),
            'ts': event_data.get('event', {}).get('ts', ''),
            'user': event_data.get('event', {}).get('user', ''),
            'text': event_data.get('event', {}).get('text', ''),
            'type': event_data.get('event', {}).get('type', '')
        }
        
        content_str = json.dumps(event_content, sort_keys=True)
        event_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        
        return f"{self.EVENT_DEDUP_PREFIX}:{event_hash}"
    
    async def update_conversation(
        self, 
        channel_id: str, 
        user_id: str, 
        updates: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Update conversation state atomically
        
        Args:
            channel_id: Slack channel ID
            user_id: Slack user ID  
            updates: Dictionary of updates to apply
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if self._circuit_open:
            logger.warning("Redis circuit breaker open, skipping state update")
            return False
        
        try:
            key = self._get_conversation_key(channel_id, user_id)
            ttl = ttl or self.default_conversation_ttl
            
            # Use pipeline for atomic operations
            pipe = self.redis.pipeline()
            
            # Update conversation data
            for field, value in updates.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                pipe.hset(key, field, value)
            
            # Set expiration
            pipe.expire(key, ttl)
            
            # Execute pipeline
            await pipe.execute()
            
            await self._reset_circuit_breaker()
            
            logger.debug("Conversation state updated", 
                        channel=channel_id, user=user_id, fields=list(updates.keys()))
            
            return True
            
        except Exception as e:
            await self._handle_redis_error(e)
            return False
    
    async def get_conversation(
        self, 
        channel_id: str, 
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get conversation state
        
        Args:
            channel_id: Slack channel ID
            user_id: Slack user ID
            
        Returns:
            Conversation state dictionary or None if not found
        """
        if self._circuit_open:
            logger.warning("Redis circuit breaker open, returning empty state")
            return {}
        
        try:
            key = self._get_conversation_key(channel_id, user_id)
            
            # Get all fields
            data = await self.redis.hgetall(key)
            
            if not data:
                return {}
            
            # Parse JSON fields
            parsed_data = {}
            for field, value in data.items():
                try:
                    # Try to parse as JSON
                    parsed_data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Keep as string if not JSON
                    parsed_data[field] = value
            
            await self._reset_circuit_breaker()
            
            return parsed_data
            
        except Exception as e:
            await self._handle_redis_error(e)
            return {}
    
    async def delete_conversation(self, channel_id: str, user_id: str) -> bool:
        """
        Delete conversation state
        
        Args:
            channel_id: Slack channel ID
            user_id: Slack user ID
            
        Returns:
            True if successful, False otherwise
        """
        if self._circuit_open:
            return False
        
        try:
            key = self._get_conversation_key(channel_id, user_id)
            result = await self.redis.delete(key)
            
            await self._reset_circuit_breaker()
            
            logger.debug("Conversation deleted", 
                        channel=channel_id, user=user_id, existed=bool(result))
            
            return bool(result)
            
        except Exception as e:
            await self._handle_redis_error(e)
            return False
    
    async def is_event_duplicate(self, event_data: Dict[str, Any]) -> bool:
        """
        Check if event has already been processed (deduplication)
        
        Args:
            event_data: Slack event data
            
        Returns:
            True if event is duplicate, False if new
        """
        if self._circuit_open:
            return False  # Process events when circuit is open
        
        try:
            key = self._get_event_dedup_key(event_data)
            
            # Check if key exists
            exists = await self.redis.exists(key)
            
            if not exists:
                # Mark as processed with TTL
                await self.redis.setex(key, self.event_dedup_ttl, "1")
                
                await self._reset_circuit_breaker()
                return False
            else:
                await self._reset_circuit_breaker()
                return True
                
        except Exception as e:
            await self._handle_redis_error(e)
            return False  # Process events on Redis errors
    
    async def store_temp_data(
        self, 
        key: str, 
        data: Any, 
        ttl: int = 3600
    ) -> bool:
        """
        Store temporary data with expiration
        
        Args:
            key: Storage key
            data: Data to store
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self._circuit_open:
            return False
        
        try:
            full_key = f"{self.TEMP_DATA_PREFIX}:{key}"
            
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            
            await self.redis.setex(full_key, ttl, data)
            
            await self._reset_circuit_breaker()
            return True
            
        except Exception as e:
            await self._handle_redis_error(e)
            return False
    
    async def get_temp_data(self, key: str) -> Any:
        """
        Get temporary data
        
        Args:
            key: Storage key
            
        Returns:
            Stored data or None if not found
        """
        if self._circuit_open:
            return None
        
        try:
            full_key = f"{self.TEMP_DATA_PREFIX}:{key}"
            data = await self.redis.get(full_key)
            
            if data is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return data
                
        except Exception as e:
            await self._handle_redis_error(e)
            return None
    
    async def increment_metric(self, metric_name: str, value: int = 1) -> Optional[int]:
        """
        Increment a metric counter
        
        Args:
            metric_name: Name of the metric
            value: Value to increment by
            
        Returns:
            New metric value or None on error
        """
        if self._circuit_open:
            return None
        
        try:
            key = f"{self.METRICS_PREFIX}:{metric_name}"
            result = await self.redis.incrby(key, value)
            
            # Set expiration for daily metrics
            await self.redis.expire(key, 86400)
            
            await self._reset_circuit_breaker()
            return result
            
        except Exception as e:
            await self._handle_redis_error(e)
            return None
    
    async def get_metrics(self) -> Dict[str, int]:
        """
        Get all metrics
        
        Returns:
            Dictionary of metric names and values
        """
        if self._circuit_open:
            return {}
        
        try:
            pattern = f"{self.METRICS_PREFIX}:*"
            keys = await self.redis.keys(pattern)
            
            if not keys:
                return {}
            
            # Get all metric values
            values = await self.redis.mget(keys)
            
            # Create metrics dictionary
            metrics = {}
            for key, value in zip(keys, values):
                metric_name = key.replace(f"{self.METRICS_PREFIX}:", "")
                metrics[metric_name] = int(value) if value else 0
            
            await self._reset_circuit_breaker()
            return metrics
            
        except Exception as e:
            await self._handle_redis_error(e)
            return {}
    
    async def _background_cleanup(self):
        """Background task for cleanup operations"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up expired event deduplication keys
                await self._cleanup_expired_keys()
                
                logger.debug("Background cleanup completed")
                
            except Exception as e:
                logger.error("Background cleanup failed", error=str(e))
    
    async def _cleanup_expired_keys(self):
        """Clean up expired deduplication keys"""
        try:
            # Get all deduplication keys
            pattern = f"{self.EVENT_DEDUP_PREFIX}:*"
            keys = await self.redis.keys(pattern)
            
            if len(keys) > self.max_dedup_events:
                # Sort by creation time and remove oldest
                oldest_keys = keys[:-self.max_dedup_events]
                if oldest_keys:
                    await self.redis.delete(*oldest_keys)
                    logger.info("Cleaned up old deduplication keys", count=len(oldest_keys))
                    
        except Exception as e:
            logger.error("Failed to cleanup expired keys", error=str(e))