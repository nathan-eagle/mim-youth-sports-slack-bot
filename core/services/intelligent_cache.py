"""
Intelligent caching layer for MiM Slack Bot
Multi-level caching with AI response optimization and cost reduction
"""

import json
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import structlog

import redis.asyncio as redis
from redis.exceptions import RedisError

from ..config import Settings

logger = structlog.get_logger(__name__)


class CacheKey:
    """Utility class for generating consistent cache keys"""
    
    @staticmethod
    def hash_content(content: Union[str, Dict, List]) -> str:
        """Generate consistent hash for content"""
        if isinstance(content, (dict, list)):
            content = json.dumps(content, sort_keys=True)
        
        return hashlib.sha256(str(content).encode()).hexdigest()[:16]
    
    @staticmethod
    def ai_response(prompt: str, model: str, **kwargs) -> str:
        """Generate cache key for AI responses"""
        cache_data = {
            'prompt': prompt,
            'model': model,
            **kwargs
        }
        hash_key = CacheKey.hash_content(cache_data)
        return f"ai_response:{hash_key}"
    
    @staticmethod
    def logo_analysis(logo_url: str, analysis_type: str = "colors") -> str:
        """Generate cache key for logo analysis"""
        hash_key = CacheKey.hash_content(f"{logo_url}:{analysis_type}")
        return f"logo_analysis:{analysis_type}:{hash_key}"
    
    @staticmethod
    def product_recommendation(intent: str, context: Dict[str, Any]) -> str:
        """Generate cache key for product recommendations"""
        cache_data = {
            'intent': intent,
            'context': context
        }
        hash_key = CacheKey.hash_content(cache_data)
        return f"product_rec:{hash_key}"
    
    @staticmethod
    def mockup_design(logo_hash: str, product_id: str, color: str) -> str:
        """Generate cache key for mockup designs"""
        cache_data = f"{logo_hash}:{product_id}:{color}"
        hash_key = CacheKey.hash_content(cache_data)
        return f"mockup:{hash_key}"
    
    @staticmethod
    def api_response(endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for API responses"""
        cache_data = {
            'endpoint': endpoint,
            'params': params
        }
        hash_key = CacheKey.hash_content(cache_data)
        return f"api_response:{hash_key}"


class IntelligentCache:
    """
    Multi-level intelligent caching system with:
    - AI response caching with content-based keys
    - API response caching with rate limit awareness
    - Logo analysis caching for expensive operations
    - Automatic cache warming and invalidation
    - Performance monitoring and hit rate optimization
    """
    
    def __init__(self, redis_client: redis.Redis, settings: Settings):
        """
        Initialize intelligent cache
        
        Args:
            redis_client: Redis client instance
            settings: Application settings
        """
        self.redis = redis_client
        self.settings = settings
        
        # Cache prefixes
        self.AI_PREFIX = "ai_cache"
        self.API_PREFIX = "api_cache"
        self.LOGO_PREFIX = "logo_cache"
        self.PRODUCT_PREFIX = "product_cache"
        self.MOCKUP_PREFIX = "mockup_cache"
        self.METRICS_PREFIX = "cache_metrics"
        
        # Cache statistics
        self._hits = 0
        self._misses = 0
        self._errors = 0
        
        # Cache warming settings
        self._warming_enabled = True
        self._warming_queue: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """Initialize cache system and start background tasks"""
        try:
            # Test Redis connection
            await self.redis.ping()
            
            # Start background tasks
            asyncio.create_task(self._background_maintenance())
            asyncio.create_task(self._cache_warming_worker())
            
            logger.info("Intelligent cache system initialized")
            
        except Exception as e:
            logger.error("Failed to initialize cache system", error=str(e))
            raise
    
    # High-level caching decorators and methods
    
    def cached(
        self, 
        ttl: Optional[int] = None, 
        cache_type: str = "default",
        key_generator: Optional[Callable] = None
    ):
        """
        Decorator for caching function results
        
        Args:
            ttl: Time to live in seconds
            cache_type: Type of cache for TTL selection
            key_generator: Custom key generation function
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    cache_key = self._generate_function_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    await self._record_hit(func.__name__)
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                cache_ttl = ttl or self.settings.get_cache_ttl(cache_type)
                await self.set(cache_key, result, ttl=cache_ttl)
                
                await self._record_miss(func.__name__)
                return result
                
            return wrapper
        return decorator
    
    async def cache_ai_response(
        self, 
        prompt: str, 
        model: str, 
        response: Any,
        context: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache AI response with intelligent key generation
        
        Args:
            prompt: AI prompt
            model: AI model used
            response: AI response to cache
            context: Additional context for cache key
            ttl: Time to live override
            
        Returns:
            True if cached successfully
        """
        try:
            cache_key = CacheKey.ai_response(prompt, model, **(context or {}))
            cache_ttl = ttl or self.settings.get_cache_ttl("ai_responses")
            
            cache_data = {
                'response': response,
                'model': model,
                'cached_at': datetime.utcnow().isoformat(),
                'context': context or {}
            }
            
            success = await self.set(cache_key, cache_data, ttl=cache_ttl)
            
            if success:
                logger.debug("AI response cached", model=model, key=cache_key[:16])
            
            return success
            
        except Exception as e:
            logger.error("Failed to cache AI response", error=str(e))
            return False
    
    async def get_ai_response(
        self, 
        prompt: str, 
        model: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get cached AI response
        
        Args:
            prompt: AI prompt
            model: AI model
            context: Additional context for cache key
            
        Returns:
            Cached response or None if not found
        """
        try:
            cache_key = CacheKey.ai_response(prompt, model, **(context or {}))
            cached_data = await self.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                # Check if response is still valid
                cached_at = datetime.fromisoformat(cached_data.get('cached_at', ''))
                max_age = timedelta(seconds=self.settings.get_cache_ttl("ai_responses"))
                
                if datetime.utcnow() - cached_at < max_age:
                    logger.debug("AI response cache hit", model=model, key=cache_key[:16])
                    return cached_data.get('response')
            
            return None
            
        except Exception as e:
            logger.error("Failed to get cached AI response", error=str(e))
            return None
    
    async def cache_logo_analysis(
        self, 
        logo_url: str, 
        analysis_result: Dict[str, Any],
        analysis_type: str = "colors",
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache logo analysis results
        
        Args:
            logo_url: URL of the logo
            analysis_result: Analysis result to cache
            analysis_type: Type of analysis (colors, style, etc.)
            ttl: Time to live override
            
        Returns:
            True if cached successfully
        """
        try:
            cache_key = CacheKey.logo_analysis(logo_url, analysis_type)
            cache_ttl = ttl or self.settings.get_cache_ttl("logo_analysis")
            
            cache_data = {
                'analysis': analysis_result,
                'logo_url': logo_url,
                'analysis_type': analysis_type,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            success = await self.set(cache_key, cache_data, ttl=cache_ttl)
            
            if success:
                logger.debug("Logo analysis cached", 
                           analysis_type=analysis_type, key=cache_key[:16])
            
            return success
            
        except Exception as e:
            logger.error("Failed to cache logo analysis", error=str(e))
            return False
    
    async def get_logo_analysis(
        self, 
        logo_url: str, 
        analysis_type: str = "colors"
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached logo analysis
        
        Args:
            logo_url: URL of the logo
            analysis_type: Type of analysis
            
        Returns:
            Cached analysis or None if not found
        """
        try:
            cache_key = CacheKey.logo_analysis(logo_url, analysis_type)
            cached_data = await self.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                logger.debug("Logo analysis cache hit", 
                           analysis_type=analysis_type, key=cache_key[:16])
                return cached_data.get('analysis')
            
            return None
            
        except Exception as e:
            logger.error("Failed to get cached logo analysis", error=str(e))
            return None
    
    async def cache_product_recommendation(
        self, 
        intent: str, 
        context: Dict[str, Any],
        recommendations: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache product recommendations
        
        Args:
            intent: User intent/request
            context: Request context (colors, preferences, etc.)
            recommendations: Product recommendations to cache
            ttl: Time to live override
            
        Returns:
            True if cached successfully
        """
        try:
            cache_key = CacheKey.product_recommendation(intent, context)
            cache_ttl = ttl or self.settings.get_cache_ttl("product_data")
            
            cache_data = {
                'recommendations': recommendations,
                'intent': intent,
                'context': context,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            success = await self.set(cache_key, cache_data, ttl=cache_ttl)
            
            if success:
                logger.debug("Product recommendations cached", 
                           count=len(recommendations), key=cache_key[:16])
            
            return success
            
        except Exception as e:
            logger.error("Failed to cache product recommendations", error=str(e))
            return False
    
    async def get_product_recommendation(
        self, 
        intent: str, 
        context: Dict[str, Any]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached product recommendations
        
        Args:
            intent: User intent/request
            context: Request context
            
        Returns:
            Cached recommendations or None if not found
        """
        try:
            cache_key = CacheKey.product_recommendation(intent, context)
            cached_data = await self.get(cache_key)
            
            if cached_data and isinstance(cached_data, dict):
                logger.debug("Product recommendation cache hit", key=cache_key[:16])
                return cached_data.get('recommendations')
            
            return None
            
        except Exception as e:
            logger.error("Failed to get cached product recommendations", error=str(e))
            return None
    
    # Low-level cache operations
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            
            if value is None:
                self._misses += 1
                return None
            
            # Try to parse as JSON
            try:
                parsed_value = json.loads(value)
                self._hits += 1
                return parsed_value
            except json.JSONDecodeError:
                self._hits += 1
                return value
                
        except Exception as e:
            self._errors += 1
            logger.error("Cache get failed", key=key, error=str(e))
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            # Set with TTL
            if ttl:
                result = await self.redis.setex(key, ttl, serialized_value)
            else:
                result = await self.redis.set(key, serialized_value)
            
            return bool(result)
            
        except Exception as e:
            self._errors += 1
            logger.error("Cache set failed", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("Cache exists check failed", key=key, error=str(e))
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self._hits,
            'misses': self._misses,
            'errors': self._errors,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'error_rate_percent': round((self._errors / total_requests * 100) if total_requests > 0 else 0, 2)
        }
    
    def _generate_function_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function calls"""
        cache_data = {
            'function': func_name,
            'args': args,
            'kwargs': kwargs
        }
        hash_key = CacheKey.hash_content(cache_data)
        return f"func:{func_name}:{hash_key}"
    
    async def _record_hit(self, operation: str):
        """Record cache hit for metrics"""
        self._hits += 1
        await self.redis.incr(f"{self.METRICS_PREFIX}:hits:{operation}")
    
    async def _record_miss(self, operation: str):
        """Record cache miss for metrics"""
        self._misses += 1
        await self.redis.incr(f"{self.METRICS_PREFIX}:misses:{operation}")
    
    async def _background_maintenance(self):
        """Background task for cache maintenance"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Update cache statistics
                await self._update_cache_statistics()
                
                # Clean up expired entries
                await self._cleanup_expired_entries()
                
                logger.debug("Cache maintenance completed")
                
            except Exception as e:
                logger.error("Cache maintenance failed", error=str(e))
    
    async def _cache_warming_worker(self):
        """Background worker for cache warming"""
        while True:
            try:
                if self._warming_queue and self._warming_enabled:
                    # Process warming requests
                    warming_item = self._warming_queue.pop(0)
                    await self._process_warming_item(warming_item)
                
                await asyncio.sleep(1)  # Check queue every second
                
            except Exception as e:
                logger.error("Cache warming failed", error=str(e))
    
    async def _update_cache_statistics(self):
        """Update cache performance statistics"""
        try:
            stats = await self.get_cache_stats()
            
            # Store daily stats
            today = datetime.utcnow().strftime('%Y-%m-%d')
            stats_key = f"{self.METRICS_PREFIX}:daily:{today}"
            
            await self.set(stats_key, stats, ttl=86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error("Failed to update cache statistics", error=str(e))
    
    async def _cleanup_expired_entries(self):
        """Clean up expired cache entries"""
        # Redis automatically handles TTL expiration
        # This method can be extended for custom cleanup logic
        pass
    
    async def _process_warming_item(self, item: Dict[str, Any]):
        """Process cache warming item"""
        # Implementation for cache warming based on access patterns
        # This can be extended to pre-load frequently accessed data
        pass