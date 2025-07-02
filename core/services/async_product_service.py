"""
Async Product Service for MiM Slack Bot
High-performance product catalog management with parallel processing
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import structlog

import aiohttp
from asyncio_throttle import Throttler

from ..config import Settings, ProductCatalogConfig
from .intelligent_cache import IntelligentCache
from .optimized_ai_service import OptimizedAIService

logger = structlog.get_logger(__name__)


class AsyncProductService:
    """
    High-performance async product service with:
    - Concurrent product processing
    - Intelligent caching and prefetching
    - AI-powered product recommendations
    - Dynamic catalog management
    - Rate-limited API operations
    """
    
    def __init__(
        self,
        settings: Settings,
        cache: IntelligentCache,
        ai_service: OptimizedAIService
    ):
        """
        Initialize async product service
        
        Args:
            settings: Application settings
            cache: Intelligent cache instance
            ai_service: AI service instance
        """
        self.settings = settings
        self.cache = cache
        self.ai_service = ai_service
        
        # Configuration
        self.config = ProductCatalogConfig()
        
        # Product catalog
        self._products_cache: Dict[str, Any] = {}
        self._last_cache_update: Optional[datetime] = None
        self._cache_update_lock = asyncio.Lock()
        
        # HTTP session for API calls
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting for external APIs
        self.printify_throttler = Throttler(rate_limit=60, period=60)  # 60 calls per minute
        
        # Performance tracking
        self._metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'ai_recommendations': 0,
            'api_calls': 0
        }
        
        logger.info("Async product service initialized")
    
    async def initialize(self):
        """Initialize the async product service"""
        try:
            # Create HTTP session
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'MiM-Bot/2.0'}
            )
            
            # Load initial product cache
            await self._load_product_cache()
            
            # Start background tasks
            asyncio.create_task(self._background_cache_refresh())
            asyncio.create_task(self._background_metrics_collection())
            
            logger.info("Async product service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize async product service", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the async product service"""
        if self._session:
            await self._session.close()
        logger.info("Async product service shutdown complete")
    
    async def get_product_recommendations(
        self,
        user_intent: str,
        logo_colors: Optional[List[str]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        max_products: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered product recommendations with caching
        
        Args:
            user_intent: User's intent/request
            logo_colors: Colors from user's logo
            user_preferences: User preferences
            max_products: Maximum products to return
            
        Returns:
            List of recommended products with AI reasoning
        """
        async with self._track_operation("product_recommendations"):
            try:
                # Prepare context for caching and AI
                context = {
                    'logo_colors': logo_colors or [],
                    'preferences': user_preferences or {},
                    'max_products': max_products
                }
                
                # Check cache first
                cached_recommendations = await self.cache.get_product_recommendation(
                    user_intent, context
                )
                
                if cached_recommendations:
                    self._metrics['cache_hits'] += 1
                    logger.debug("Product recommendations cache hit")
                    return cached_recommendations[:max_products]
                
                # Get available products
                available_products = await self.get_all_products()
                if not available_products:
                    logger.error("No products available for recommendations")
                    return []
                
                # Get AI recommendations
                self._metrics['ai_recommendations'] += 1
                recommendations = await self.ai_service.recommend_products(
                    intent=user_intent,
                    user_preferences=context,
                    available_products=list(available_products.values()),
                    max_products=max_products
                )
                
                # Enrich recommendations with product data
                enriched_recommendations = []
                for rec in recommendations:
                    product_id = rec.get('product_id')
                    if product_id in available_products:
                        product_data = available_products[product_id]
                        enriched_rec = {
                            **rec,
                            'product_data': product_data,
                            'colors': await self.get_colors_for_product(product_id),
                            'sizes': await self.get_sizes_for_product(product_id)
                        }
                        enriched_recommendations.append(enriched_rec)
                
                # Cache results
                await self.cache.cache_product_recommendation(
                    user_intent, context, enriched_recommendations
                )
                
                self._metrics['cache_misses'] += 1
                return enriched_recommendations
                
            except Exception as e:
                logger.error("Failed to get product recommendations", error=str(e))
                return []
    
    async def generate_mockups_parallel(
        self,
        logo_url: str,
        product_recommendations: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate mockups for multiple products in parallel
        
        Args:
            logo_url: URL of the logo image
            product_recommendations: List of product recommendations
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of mockup results
        """
        async with self._track_operation("parallel_mockup_generation"):
            try:
                # Create tasks for parallel processing
                tasks = []
                
                for i, recommendation in enumerate(product_recommendations):
                    task = asyncio.create_task(
                        self._generate_single_mockup_with_ai_colors(
                            logo_url=logo_url,
                            product_recommendation=recommendation,
                            task_id=f"mockup_{i}"
                        )
                    )
                    tasks.append(task)
                
                # Process in parallel with progress tracking
                results = []
                completed = 0
                
                for coro in asyncio.as_completed(tasks):
                    try:
                        result = await coro
                        results.append(result)
                        completed += 1
                        
                        # Progress callback
                        if progress_callback:
                            await progress_callback(completed, len(tasks), result)
                        
                        logger.debug("Mockup generated", 
                                   completed=completed, 
                                   total=len(tasks))
                        
                    except Exception as e:
                        logger.error("Mockup generation failed", error=str(e))
                        results.append({
                            'success': False,
                            'error': str(e)
                        })
                
                # Filter successful results
                successful_results = [r for r in results if r.get('success', False)]
                
                logger.info("Parallel mockup generation completed",
                           total=len(tasks),
                           successful=len(successful_results),
                           failed=len(tasks) - len(successful_results))
                
                return successful_results
                
            except Exception as e:
                logger.error("Parallel mockup generation failed", error=str(e))
                return []
    
    async def _generate_single_mockup_with_ai_colors(
        self,
        logo_url: str,
        product_recommendation: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Generate a single mockup with AI-recommended colors
        
        Args:
            logo_url: URL of the logo image
            product_recommendation: Product recommendation with AI reasoning
            task_id: Unique task identifier
            
        Returns:
            Mockup generation result
        """
        try:
            product_data = product_recommendation.get('product_data', {})
            product_id = product_data.get('id')
            
            if not product_id:
                raise ValueError("Product ID not found in recommendation")
            
            # Get AI color recommendations for this specific product
            available_colors = await self.get_colors_for_product(product_id)
            
            if not available_colors:
                raise ValueError(f"No colors available for product {product_id}")
            
            # Get logo colors if not already analyzed
            logo_analysis = await self.ai_service.analyze_logo_colors(logo_url)
            logo_colors = logo_analysis.get('primary_colors', [])
            
            # Get AI color recommendations
            color_recommendations = await self.ai_service.recommend_colors(
                logo_colors=logo_colors,
                product_type=product_data.get('title', ''),
                available_colors=available_colors,
                max_colors=1  # Just need the best color
            )
            
            # Select the best color
            best_color = None
            if color_recommendations:
                best_color = color_recommendations[0].get('color')
            
            # Fallback to first available color
            if not best_color or best_color not in available_colors:
                best_color = available_colors[0]
            
            # Generate mockup
            mockup_result = await self._generate_printify_mockup(
                logo_url=logo_url,
                product_id=product_id,
                product_data=product_data,
                selected_color=best_color
            )
            
            return {
                'success': True,
                'task_id': task_id,
                'product_id': product_id,
                'product_name': product_data.get('title'),
                'selected_color': best_color,
                'ai_reasoning': product_recommendation.get('reasoning'),
                'mockup_url': mockup_result.get('mockup_url'),
                'purchase_url': mockup_result.get('purchase_url'),
                'printify_design_id': mockup_result.get('design_id')
            }
            
        except Exception as e:
            logger.error("Single mockup generation failed", 
                        task_id=task_id, error=str(e))
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }
    
    async def _generate_printify_mockup(
        self,
        logo_url: str,
        product_id: str,
        product_data: Dict[str, Any],
        selected_color: str
    ) -> Dict[str, Any]:
        """
        Generate mockup using Printify API
        
        Args:
            logo_url: URL of the logo image
            product_id: Product ID
            product_data: Product data
            selected_color: Selected color name
            
        Returns:
            Mockup generation result
        """
        # Import existing services to reuse logic
        from printify_service import printify_service
        from database_service import database_service
        
        # Use existing Printify service logic but in async context
        async with self.printify_throttler:
            self._metrics['api_calls'] += 1
            
            # This would need to be refactored to be truly async
            # For now, run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            result = await loop.run_in_executor(
                None,
                lambda: self._sync_generate_mockup(
                    printify_service,
                    database_service,
                    logo_url,
                    product_id,
                    product_data,
                    selected_color
                )
            )
            
            return result
    
    def _sync_generate_mockup(
        self,
        printify_service,
        database_service,
        logo_url: str,
        product_id: str,
        product_data: Dict[str, Any],
        selected_color: str
    ) -> Dict[str, Any]:
        """
        Sync wrapper for existing mockup generation logic
        """
        try:
            # Use existing logic from printify_service
            # This is a temporary bridge until full async refactor
            
            # Find variant for color
            variants = product_data.get('variants', [])
            selected_variant = None
            
            for variant in variants:
                variant_options = variant.get('options', {})
                if variant_options.get('color') == selected_color:
                    selected_variant = variant
                    break
            
            if not selected_variant:
                # Fallback to first variant
                selected_variant = variants[0] if variants else None
            
            if not selected_variant:
                raise ValueError("No suitable variant found")
            
            # Generate mockup using existing service
            design_result = printify_service.create_product_design_with_mockup(
                product_id=product_id,
                variant_id=selected_variant['id'],
                logo_url=logo_url
            )
            
            if not design_result.get('success'):
                raise ValueError(f"Mockup generation failed: {design_result.get('error')}")
            
            design_id = design_result['design_id']
            mockup_url = design_result.get('mockup_url')
            
            # Save to database
            database_service.save_product_design(
                design_id=design_id,
                product_id=product_id,
                variant_id=selected_variant['id'],
                logo_url=logo_url,
                mockup_url=mockup_url
            )
            
            # Generate purchase URL
            purchase_url = f"{self.settings.app_name}/design/{design_id}"
            
            return {
                'success': True,
                'design_id': design_id,
                'mockup_url': mockup_url,
                'purchase_url': purchase_url
            }
            
        except Exception as e:
            logger.error("Sync mockup generation failed", error=str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_all_products(self) -> Dict[str, Any]:
        """
        Get all available products with caching
        
        Returns:
            Dictionary of products by ID
        """
        # Check if cache needs refresh
        if (not self._products_cache or 
            not self._last_cache_update or
            datetime.utcnow() - self._last_cache_update > timedelta(hours=1)):
            
            async with self._cache_update_lock:
                # Double-check after acquiring lock
                if (not self._products_cache or 
                    not self._last_cache_update or
                    datetime.utcnow() - self._last_cache_update > timedelta(hours=1)):
                    
                    await self._load_product_cache()
        
        return self._products_cache
    
    async def get_colors_for_product(self, product_id: str) -> List[str]:
        """
        Get available colors for a product
        
        Args:
            product_id: Product ID
            
        Returns:
            List of available color names
        """
        products = await self.get_all_products()
        product = products.get(product_id)
        
        if not product:
            return []
        
        colors = set()
        for variant in product.get('variants', []):
            color = variant.get('options', {}).get('color')
            if color:
                colors.add(color)
        
        return sorted(list(colors))
    
    async def get_sizes_for_product(self, product_id: str) -> List[str]:
        """
        Get available sizes for a product
        
        Args:
            product_id: Product ID
            
        Returns:
            List of available size names
        """
        products = await self.get_all_products()
        product = products.get(product_id)
        
        if not product:
            return []
        
        sizes = set()
        for variant in product.get('variants', []):
            size = variant.get('options', {}).get('size')
            if size:
                sizes.add(size)
        
        return sorted(list(sizes))
    
    async def _load_product_cache(self):
        """Load product cache from file or API"""
        try:
            # Try to load from optimized cache file first
            cache_file = "product_cache_optimized.json"
            
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self._products_cache = cache_data.get('products', {})
                    self._last_cache_update = datetime.utcnow()
                    
                    logger.info("Product cache loaded from file", 
                               product_count=len(self._products_cache))
                    return
                    
            except FileNotFoundError:
                logger.warning("Product cache file not found, will load from fallback")
            
            # Fallback: Load from original product service
            from product_service import product_service
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            products = await loop.run_in_executor(
                None, 
                lambda: product_service.get_all_products()
            )
            
            self._products_cache = products or {}
            self._last_cache_update = datetime.utcnow()
            
            logger.info("Product cache loaded from fallback service",
                       product_count=len(self._products_cache))
            
        except Exception as e:
            logger.error("Failed to load product cache", error=str(e))
            self._products_cache = {}
    
    async def _background_cache_refresh(self):
        """Background task to refresh product cache"""
        while True:
            try:
                await asyncio.sleep(3600)  # Refresh every hour
                
                async with self._cache_update_lock:
                    await self._load_product_cache()
                
                logger.debug("Background cache refresh completed")
                
            except Exception as e:
                logger.error("Background cache refresh failed", error=str(e))
    
    async def _background_metrics_collection(self):
        """Background task to collect and log metrics"""
        while True:
            try:
                await asyncio.sleep(300)  # Collect every 5 minutes
                
                logger.info("Product service metrics", **self._metrics)
                
            except Exception as e:
                logger.error("Metrics collection failed", error=str(e))
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        cache_hit_rate = 0
        total_requests = self._metrics['cache_hits'] + self._metrics['cache_misses']
        
        if total_requests > 0:
            cache_hit_rate = (self._metrics['cache_hits'] / total_requests) * 100
        
        return {
            'products_cached': len(self._products_cache),
            'last_cache_update': self._last_cache_update.isoformat() if self._last_cache_update else None,
            'cache_hit_rate_percent': round(cache_hit_rate, 2),
            'metrics': self._metrics
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            stats = await self.get_service_stats()
            
            healthy = True
            issues = []
            
            # Check if products are loaded
            if not self._products_cache:
                healthy = False
                issues.append("No products loaded")
            
            # Check cache age
            if (self._last_cache_update and 
                datetime.utcnow() - self._last_cache_update > timedelta(hours=6)):
                healthy = False
                issues.append("Product cache is stale")
            
            return {
                'status': 'healthy' if healthy else 'degraded',
                'healthy': healthy,
                'issues': issues,
                'statistics': stats
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'healthy': False,
                'error': str(e)
            }
    
    async def _track_operation(self, operation_name: str):
        """Context manager for tracking operations"""
        class OperationTracker:
            def __init__(self, service):
                self.service = service
                
            async def __aenter__(self):
                return self
                
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                # Could add operation tracking here
                pass
        
        return OperationTracker(self)