"""
Service Orchestrator for MiM Slack Bot
Coordinates all services and provides a unified interface
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

import redis.asyncio as redis

from ..config import Settings
from .redis_state_manager import RedisStateManager
from .intelligent_cache import IntelligentCache
from .optimized_ai_service import OptimizedAIService
from .async_product_service import AsyncProductService
from .async_database_service import AsyncDatabaseService
from .background_processor import BackgroundEventProcessor
from .slack_gateway import SlackEventGateway
from .performance_monitor import PerformanceMonitor

logger = structlog.get_logger(__name__)


class ServiceOrchestrator:
    """
    Central orchestrator for all MiM Bot services
    
    Provides:
    - Service lifecycle management
    - Dependency injection
    - Health monitoring
    - Graceful shutdown
    - Unified service interface
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize service orchestrator
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Core infrastructure
        self.redis_client: Optional[redis.Redis] = None
        self.state_manager: Optional[RedisStateManager] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        
        # Business services
        self.cache: Optional[IntelligentCache] = None
        self.ai_service: Optional[OptimizedAIService] = None
        self.product_service: Optional[AsyncProductService] = None
        self.database_service: Optional[AsyncDatabaseService] = None
        
        # Processing services
        self.background_processor: Optional[BackgroundEventProcessor] = None
        self.slack_gateway: Optional[SlackEventGateway] = None
        
        # Service status
        self._initialized = False
        self._shutdown = False
        
        logger.info("Service orchestrator created")
    
    async def initialize(self):
        """
        Initialize all services in dependency order
        """
        try:
            logger.info("Starting service initialization")
            
            # 1. Initialize Redis connection
            await self._initialize_redis()
            
            # 2. Initialize core infrastructure services
            await self._initialize_infrastructure()
            
            # 3. Initialize business services
            await self._initialize_business_services()
            
            # 4. Initialize processing services
            await self._initialize_processing_services()
            
            # 5. Start background tasks
            await self._start_background_tasks()
            
            self._initialized = True
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error("Service initialization failed", error=str(e))
            await self.shutdown()
            raise
    
    async def shutdown(self):
        """
        Gracefully shutdown all services
        """
        if self._shutdown:
            return
        
        self._shutdown = True
        logger.info("Starting graceful shutdown")
        
        try:
            # Shutdown in reverse dependency order
            
            # 1. Stop processing services
            if self.background_processor:
                await self.background_processor.shutdown()
            
            # 2. Shutdown business services
            if self.product_service:
                await self.product_service.shutdown()
            
            if self.database_service:
                await self.database_service.shutdown()
            
            # 3. Shutdown infrastructure services
            if self.state_manager:
                await self.state_manager.shutdown()
            
            if self.performance_monitor:
                await self.performance_monitor.shutdown()
            
            # 4. Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Graceful shutdown completed")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
    
    async def _initialize_redis(self):
        """Initialize Redis connection"""
        logger.debug("Initializing Redis connection")
        
        self.redis_client = redis.Redis.from_url(
            self.settings.redis_url,
            max_connections=self.settings.redis_max_connections,
            socket_timeout=self.settings.redis_socket_timeout,
            decode_responses=True
        )
        
        # Test connection
        await self.redis_client.ping()
        logger.info("Redis connection established")
    
    async def _initialize_infrastructure(self):
        """Initialize core infrastructure services"""
        logger.debug("Initializing infrastructure services")
        
        # State Manager
        self.state_manager = RedisStateManager(
            redis_url=self.settings.redis_url,
            max_connections=self.settings.redis_max_connections
        )
        await self.state_manager.initialize()
        
        # Performance Monitor
        self.performance_monitor = PerformanceMonitor(self.redis_client)
        await self.performance_monitor.initialize()
        
        logger.info("Infrastructure services initialized")
    
    async def _initialize_business_services(self):
        """Initialize business logic services"""
        logger.debug("Initializing business services")
        
        # Intelligent Cache
        self.cache = IntelligentCache(self.redis_client, self.settings)
        await self.cache.initialize()
        
        # AI Service
        self.ai_service = OptimizedAIService(self.settings, self.cache)
        
        # Product Service
        self.product_service = AsyncProductService(
            self.settings, 
            self.cache, 
            self.ai_service
        )
        await self.product_service.initialize()
        
        # Database Service
        self.database_service = AsyncDatabaseService(self.settings)
        await self.database_service.initialize()
        
        logger.info("Business services initialized")
    
    async def _initialize_processing_services(self):
        """Initialize event processing services"""
        logger.debug("Initializing processing services")
        
        # Background Processor
        self.background_processor = BackgroundEventProcessor(
            state_manager=self.state_manager,
            performance_monitor=self.performance_monitor,
            max_workers=self.settings.async_worker_count
        )
        await self.background_processor.initialize()
        
        # Slack Gateway
        self.slack_gateway = SlackEventGateway(
            signing_secret=self.settings.slack_signing_secret,
            event_processor=self.background_processor,
            state_manager=self.state_manager,
            performance_monitor=self.performance_monitor
        )
        
        logger.info("Processing services initialized")
    
    async def _start_background_tasks(self):
        """Start background monitoring and maintenance tasks"""
        logger.debug("Starting background tasks")
        
        # Start health monitoring
        asyncio.create_task(self._health_monitoring_loop())
        
        # Start metrics collection
        asyncio.create_task(self._metrics_collection_loop())
        
        logger.info("Background tasks started")
    
    # Service Access Methods
    
    def get_state_manager(self) -> RedisStateManager:
        """Get state manager instance"""
        if not self._initialized or not self.state_manager:
            raise RuntimeError("State manager not initialized")
        return self.state_manager
    
    def get_ai_service(self) -> OptimizedAIService:
        """Get AI service instance"""
        if not self._initialized or not self.ai_service:
            raise RuntimeError("AI service not initialized")
        return self.ai_service
    
    def get_product_service(self) -> AsyncProductService:
        """Get product service instance"""
        if not self._initialized or not self.product_service:
            raise RuntimeError("Product service not initialized")
        return self.product_service
    
    def get_database_service(self) -> AsyncDatabaseService:
        """Get database service instance"""
        if not self._initialized or not self.database_service:
            raise RuntimeError("Database service not initialized")
        return self.database_service
    
    def get_background_processor(self) -> BackgroundEventProcessor:
        """Get background processor instance"""
        if not self._initialized or not self.background_processor:
            raise RuntimeError("Background processor not initialized")
        return self.background_processor
    
    def get_slack_gateway(self) -> SlackEventGateway:
        """Get Slack gateway instance"""
        if not self._initialized or not self.slack_gateway:
            raise RuntimeError("Slack gateway not initialized")
        return self.slack_gateway
    
    def get_performance_monitor(self) -> PerformanceMonitor:
        """Get performance monitor instance"""
        if not self._initialized or not self.performance_monitor:
            raise RuntimeError("Performance monitor not initialized")
        return self.performance_monitor
    
    def get_cache(self) -> IntelligentCache:
        """Get cache instance"""
        if not self._initialized or not self.cache:
            raise RuntimeError("Cache not initialized")
        return self.cache
    
    # High-level Operations
    
    async def process_slack_event(
        self, 
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process Slack event through the complete pipeline
        
        Args:
            event_data: Slack event data
            
        Returns:
            Processing result
        """
        if not self._initialized:
            raise RuntimeError("Services not initialized")
        
        try:
            # Check if event should be processed
            should_process = await self.slack_gateway.should_process_event(event_data)
            
            if not should_process:
                return {
                    'status': 'ignored',
                    'reason': 'filtered_by_gateway'
                }
            
            # Queue for background processing
            await self.background_processor.process_event(event_data)
            
            return {
                'status': 'queued',
                'message': 'Event queued for background processing'
            }
            
        except Exception as e:
            logger.error("Event processing failed", error=str(e))
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def generate_product_recommendations(
        self,
        user_intent: str,
        logo_url: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate AI-powered product recommendations
        
        Args:
            user_intent: User's intent/request
            logo_url: Optional logo URL for color analysis
            user_preferences: Optional user preferences
            
        Returns:
            List of product recommendations
        """
        if not self._initialized:
            raise RuntimeError("Services not initialized")
        
        try:
            # Analyze logo colors if provided
            logo_colors = None
            if logo_url:
                logo_analysis = await self.ai_service.analyze_logo_colors(logo_url)
                logo_colors = logo_analysis.get('primary_colors', [])
            
            # Get product recommendations
            recommendations = await self.product_service.get_product_recommendations(
                user_intent=user_intent,
                logo_colors=logo_colors,
                user_preferences=user_preferences,
                max_products=self.settings.max_products_per_request
            )
            
            return recommendations
            
        except Exception as e:
            logger.error("Product recommendation failed", error=str(e))
            return []
    
    async def generate_mockups_parallel(
        self,
        logo_url: str,
        product_recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate mockups for products in parallel
        
        Args:
            logo_url: Logo URL
            product_recommendations: Product recommendations
            
        Returns:
            List of mockup results
        """
        if not self._initialized:
            raise RuntimeError("Services not initialized")
        
        try:
            results = await self.product_service.generate_mockups_parallel(
                logo_url=logo_url,
                product_recommendations=product_recommendations
            )
            
            return results
            
        except Exception as e:
            logger.error("Parallel mockup generation failed", error=str(e))
            return []
    
    # Health and Monitoring
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status
        
        Returns:
            System health information
        """
        if not self._initialized:
            return {
                'status': 'not_initialized',
                'healthy': False,
                'services': {}
            }
        
        try:
            services_health = {}
            overall_healthy = True
            
            # Check each service
            service_checks = [
                ('redis', self.state_manager.health_check()),
                ('ai_service', self.ai_service.health_check()),
                ('product_service', self.product_service.health_check()),
                ('database_service', self.database_service.health_check()),
                ('background_processor', self.background_processor.health_check()),
                ('slack_gateway', self.slack_gateway.health_check()),
                ('performance_monitor', self.performance_monitor.health_check())
            ]
            
            # Run health checks in parallel
            results = await asyncio.gather(
                *[check for _, check in service_checks],
                return_exceptions=True
            )
            
            # Process results
            for i, (service_name, _) in enumerate(service_checks):
                result = results[i]
                
                if isinstance(result, Exception):
                    services_health[service_name] = {
                        'status': 'error',
                        'healthy': False,
                        'error': str(result)
                    }
                    overall_healthy = False
                else:
                    services_health[service_name] = result
                    if not result.get('healthy', False):
                        overall_healthy = False
            
            return {
                'status': 'healthy' if overall_healthy else 'degraded',
                'healthy': overall_healthy,
                'timestamp': datetime.utcnow().isoformat(),
                'services': services_health
            }
            
        except Exception as e:
            logger.error("System health check failed", error=str(e))
            return {
                'status': 'error',
                'healthy': False,
                'error': str(e)
            }
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive system metrics
        
        Returns:
            System performance metrics
        """
        if not self._initialized or not self.performance_monitor:
            return {}
        
        try:
            return await self.performance_monitor.get_metrics()
            
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {}
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while not self._shutdown:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                health = await self.get_system_health()
                
                if not health.get('healthy', False):
                    logger.warning("System health degraded", health_status=health)
                
            except Exception as e:
                logger.error("Health monitoring loop failed", error=str(e))
    
    async def _metrics_collection_loop(self):
        """Background metrics collection loop"""
        while not self._shutdown:
            try:
                await asyncio.sleep(300)  # Collect every 5 minutes
                
                metrics = await self.get_system_metrics()
                
                # Log key metrics
                if metrics:
                    system_metrics = metrics.get('system', {})
                    logger.info("System metrics", 
                               uptime_seconds=system_metrics.get('uptime_seconds'),
                               total_requests=system_metrics.get('total_requests'),
                               error_rate=system_metrics.get('overall_error_rate_percent'))
                
            except Exception as e:
                logger.error("Metrics collection loop failed", error=str(e))
    
    @property
    def initialized(self) -> bool:
        """Check if orchestrator is initialized"""
        return self._initialized
    
    @property
    def shutdown_requested(self) -> bool:
        """Check if shutdown has been requested"""
        return self._shutdown