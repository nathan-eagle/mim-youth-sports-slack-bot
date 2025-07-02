"""
Async Database Service for MiM Slack Bot
High-performance database operations with connection pooling
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import structlog

import asyncpg
from asyncpg import Pool

from ..config import Settings

logger = structlog.get_logger(__name__)


class AsyncDatabaseService:
    """
    High-performance async database service with:
    - Connection pooling for scalability
    - Query optimization and batching
    - Automatic retry logic
    - Health monitoring
    - Fallback to sync service for compatibility
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize async database service
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.pool: Optional[Pool] = None
        
        # Connection configuration
        self.pool_config = {
            'min_size': 5,
            'max_size': settings.database_pool_size,
            'max_queries': 50000,
            'max_inactive_connection_lifetime': 300,
            'command_timeout': 10
        }
        
        # Performance tracking
        self._metrics = {
            'total_queries': 0,
            'failed_queries': 0,
            'connection_errors': 0,
            'average_query_time': 0.0
        }
        
        # Fallback to sync service
        self._sync_fallback = None
        
        logger.info("Async database service initialized")
    
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            # Parse Supabase URL for connection
            database_url = self.settings.supabase_url
            
            # For Supabase, we need to construct the proper connection string
            # This is a simplified approach - production would need proper URL parsing
            if "supabase" in database_url:
                # Use service key for server-side connections
                connection_string = f"postgresql://postgres:{self.settings.supabase_service_key}@{database_url.split('//')[1].split('/')[0]}/postgres"
            else:
                connection_string = database_url
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                connection_string,
                **self.pool_config
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            logger.info("Database connection pool initialized", 
                       min_size=self.pool_config['min_size'],
                       max_size=self.pool_config['max_size'])
            
            # Initialize fallback service
            from database_service import database_service
            self._sync_fallback = database_service
            
        except Exception as e:
            logger.error("Failed to initialize database pool", error=str(e))
            
            # Initialize fallback only
            from database_service import database_service
            self._sync_fallback = database_service
            logger.warning("Using sync database service as fallback")
    
    async def shutdown(self):
        """Shutdown database connections"""
        if self.pool:
            await self.pool.close()
        logger.info("Database connection pool closed")
    
    async def save_product_design_async(
        self,
        design_id: str,
        product_id: str,
        variant_id: str,
        logo_url: str,
        mockup_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save product design asynchronously
        
        Args:
            design_id: Unique design ID
            product_id: Product ID
            variant_id: Variant ID
            logo_url: Logo URL
            mockup_url: Mockup URL
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        if not self.pool:
            # Fallback to sync service
            return await self._fallback_save_design(
                design_id, product_id, variant_id, logo_url, mockup_url, metadata
            )
        
        try:
            query = """
                INSERT INTO product_designs (
                    design_id, product_id, variant_id, logo_url, 
                    mockup_url, metadata, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (design_id) 
                DO UPDATE SET
                    mockup_url = EXCLUDED.mockup_url,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    design_id,
                    product_id,
                    variant_id,
                    logo_url,
                    mockup_url,
                    json.dumps(metadata or {}),
                    datetime.utcnow()
                )
            
            self._metrics['total_queries'] += 1
            return True
            
        except Exception as e:
            logger.error("Failed to save product design", error=str(e))
            self._metrics['failed_queries'] += 1
            
            # Fallback to sync service
            return await self._fallback_save_design(
                design_id, product_id, variant_id, logo_url, mockup_url, metadata
            )
    
    async def get_product_design_async(self, design_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product design by ID
        
        Args:
            design_id: Design ID to retrieve
            
        Returns:
            Design data or None if not found
        """
        if not self.pool:
            # Fallback to sync service
            return await self._fallback_get_design(design_id)
        
        try:
            query = """
                SELECT design_id, product_id, variant_id, logo_url,
                       mockup_url, metadata, created_at, updated_at
                FROM product_designs
                WHERE design_id = $1
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, design_id)
            
            self._metrics['total_queries'] += 1
            
            if row:
                return {
                    'design_id': row['design_id'],
                    'product_id': row['product_id'],
                    'variant_id': row['variant_id'],
                    'logo_url': row['logo_url'],
                    'mockup_url': row['mockup_url'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
                }
            
            return None
            
        except Exception as e:
            logger.error("Failed to get product design", design_id=design_id, error=str(e))
            self._metrics['failed_queries'] += 1
            
            # Fallback to sync service
            return await self._fallback_get_design(design_id)
    
    async def batch_save_designs(
        self, 
        designs: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        Save multiple designs in a batch operation
        
        Args:
            designs: List of design data dictionaries
            
        Returns:
            Dictionary mapping design_id to success status
        """
        if not self.pool:
            # Fallback to individual saves
            results = {}
            for design in designs:
                success = await self._fallback_save_design(**design)
                results[design['design_id']] = success
            return results
        
        try:
            query = """
                INSERT INTO product_designs (
                    design_id, product_id, variant_id, logo_url,
                    mockup_url, metadata, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (design_id)
                DO UPDATE SET
                    mockup_url = EXCLUDED.mockup_url,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
            """
            
            results = {}
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for design in designs:
                        try:
                            await conn.execute(
                                query,
                                design['design_id'],
                                design['product_id'],
                                design['variant_id'],
                                design['logo_url'],
                                design.get('mockup_url'),
                                json.dumps(design.get('metadata', {})),
                                datetime.utcnow()
                            )
                            results[design['design_id']] = True
                            
                        except Exception as e:
                            logger.error("Failed to save design in batch", 
                                       design_id=design['design_id'], error=str(e))
                            results[design['design_id']] = False
            
            self._metrics['total_queries'] += len(designs)
            return results
            
        except Exception as e:
            logger.error("Batch save failed", error=str(e))
            self._metrics['failed_queries'] += 1
            
            # Fallback to individual saves
            results = {}
            for design in designs:
                success = await self._fallback_save_design(**design)
                results[design['design_id']] = success
            return results
    
    async def get_recent_designs(
        self, 
        limit: int = 10, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent designs within time window
        
        Args:
            limit: Maximum number of designs to return
            hours: Time window in hours
            
        Returns:
            List of recent designs
        """
        if not self.pool:
            # Fallback to sync service
            return await self._fallback_get_recent_designs(limit, hours)
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = """
                SELECT design_id, product_id, variant_id, logo_url,
                       mockup_url, metadata, created_at
                FROM product_designs
                WHERE created_at >= $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, cutoff_time, limit)
            
            self._metrics['total_queries'] += 1
            
            designs = []
            for row in rows:
                designs.append({
                    'design_id': row['design_id'],
                    'product_id': row['product_id'],
                    'variant_id': row['variant_id'],
                    'logo_url': row['logo_url'],
                    'mockup_url': row['mockup_url'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {},
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return designs
            
        except Exception as e:
            logger.error("Failed to get recent designs", error=str(e))
            self._metrics['failed_queries'] += 1
            
            # Fallback to sync service
            return await self._fallback_get_recent_designs(limit, hours)
    
    async def _fallback_save_design(
        self,
        design_id: str,
        product_id: str,
        variant_id: str,
        logo_url: str,
        mockup_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Fallback to sync database service"""
        if not self._sync_fallback:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._sync_fallback.save_product_design(
                    design_id=design_id,
                    product_id=product_id,
                    variant_id=variant_id,
                    logo_url=logo_url,
                    mockup_url=mockup_url,
                    metadata=metadata
                )
            )
            return result
            
        except Exception as e:
            logger.error("Fallback save failed", error=str(e))
            return False
    
    async def _fallback_get_design(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Fallback to sync database service"""
        if not self._sync_fallback:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._sync_fallback.get_product_design(design_id)
            )
            return result
            
        except Exception as e:
            logger.error("Fallback get failed", error=str(e))
            return None
    
    async def _fallback_get_recent_designs(
        self, 
        limit: int, 
        hours: int
    ) -> List[Dict[str, Any]]:
        """Fallback to sync database service"""
        if not self._sync_fallback:
            return []
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._sync_fallback.get_recent_designs(limit, hours)
            )
            return result or []
            
        except Exception as e:
            logger.error("Fallback get recent failed", error=str(e))
            return []
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get database service statistics"""
        pool_stats = {}
        
        if self.pool:
            pool_stats = {
                'pool_size': self.pool.get_size(),
                'pool_max_size': self.pool._maxsize,
                'pool_min_size': self.pool._minsize,
                'pool_free_connections': self.pool.get_idle_size(),
                'pool_used_connections': self.pool.get_size() - self.pool.get_idle_size()
            }
        
        return {
            'connection_pool': pool_stats,
            'metrics': self._metrics,
            'fallback_active': self.pool is None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database service health"""
        try:
            healthy = True
            issues = []
            
            if self.pool:
                # Test pool connectivity
                try:
                    async with self.pool.acquire() as conn:
                        await conn.execute("SELECT 1")
                except Exception as e:
                    healthy = False
                    issues.append(f"Pool connection failed: {str(e)}")
            else:
                # Check fallback service
                if not self._sync_fallback:
                    healthy = False
                    issues.append("No database connection available")
                else:
                    issues.append("Using fallback sync service")
            
            # Check error rate
            total_queries = self._metrics['total_queries']
            if total_queries > 0:
                error_rate = (self._metrics['failed_queries'] / total_queries) * 100
                if error_rate > 10:  # 10% error rate threshold
                    healthy = False
                    issues.append(f"High error rate: {error_rate:.1f}%")
            
            stats = await self.get_service_stats()
            
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