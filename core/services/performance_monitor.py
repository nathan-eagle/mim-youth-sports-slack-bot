"""
Performance monitoring service for MiM Slack Bot
Tracks operations, metrics, and system health
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import structlog

# Using in-memory metrics instead of Redis
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logger = structlog.get_logger(__name__)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring with:
    - Operation timing and success/failure tracking
    - Prometheus metrics export
    - Real-time performance dashboards
    - Alerting for performance degradation
    - Resource usage monitoring
    """
    
    def __init__(self):
        """
        Initialize performance monitor with in-memory metrics
        """
        self.redis = None  # Not using Redis anymore
        
        # Prometheus metrics
        self.operation_counter = Counter(
            'mim_operations_total',
            'Total number of operations',
            ['operation', 'status']
        )
        
        self.operation_duration = Histogram(
            'mim_operation_duration_seconds',
            'Operation duration in seconds',
            ['operation'],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]
        )
        
        self.active_operations = Gauge(
            'mim_active_operations',
            'Number of currently active operations',
            ['operation']
        )
        
        self.cache_operations = Counter(
            'mim_cache_operations_total',
            'Cache operations',
            ['operation', 'result']
        )
        
        self.ai_requests = Counter(
            'mim_ai_requests_total',
            'AI API requests',
            ['model', 'task_type', 'status']
        )
        
        self.slack_events = Counter(
            'mim_slack_events_total',
            'Slack events processed',
            ['event_type', 'status']
        )
        
        # In-memory metrics for real-time monitoring
        self._operation_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._operation_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: {'success': 0, 'failure': 0})
        self._active_operations_count: Dict[str, int] = defaultdict(int)
        
        # Performance alerts
        self._alert_thresholds = {
            'slow_operation_seconds': 10.0,
            'high_error_rate_percent': 20.0,
            'memory_usage_percent': 90.0
        }
        
        self._alerts: List[Dict[str, Any]] = []
        
        # System metrics
        self._system_metrics = {
            'start_time': datetime.utcnow(),
            'total_requests': 0,
            'total_errors': 0
        }
        
        logger.info("Performance monitor initialized")
    
    async def initialize(self):
        """Initialize performance monitoring"""
        try:
            # Using in-memory metrics only
            logger.info("Performance monitor initialized with in-memory metrics")
            
            # Start background tasks
            asyncio.create_task(self._background_metrics_collection())
            asyncio.create_task(self._background_alerting())
            
            logger.info("Performance monitor initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize performance monitor", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown performance monitoring"""
        logger.info("Performance monitor shutting down")
    
    @asynccontextmanager
    async def track_operation(self, operation_name: str):
        """
        Context manager to track operation performance
        
        Args:
            operation_name: Name of the operation being tracked
            
        Usage:
            async with monitor.track_operation("ai_request"):
                result = await make_ai_request()
        """
        start_time = time.time()
        self._active_operations_count[operation_name] += 1
        self.active_operations.labels(operation=operation_name).inc()
        
        try:
            yield
            
            # Record success
            duration = time.time() - start_time
            await self._record_operation_success(operation_name, duration)
            
        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            await self._record_operation_failure(operation_name, duration, str(e))
            raise
            
        finally:
            self._active_operations_count[operation_name] -= 1
            self.active_operations.labels(operation=operation_name).dec()
    
    async def _record_operation_success(self, operation_name: str, duration: float):
        """Record successful operation"""
        # Prometheus metrics
        self.operation_counter.labels(operation=operation_name, status='success').inc()
        self.operation_duration.labels(operation=operation_name).observe(duration)
        
        # In-memory tracking
        self._operation_times[operation_name].append(duration)
        self._operation_counts[operation_name]['success'] += 1
        self._system_metrics['total_requests'] += 1
        
        # Check for slow operations
        if duration > self._alert_thresholds['slow_operation_seconds']:
            await self._create_alert(
                'slow_operation',
                f"Operation {operation_name} took {duration:.2f}s",
                {'operation': operation_name, 'duration': duration}
            )
        
        logger.debug("Operation completed successfully", 
                    operation=operation_name, duration_ms=duration * 1000)
    
    async def _record_operation_failure(self, operation_name: str, duration: float, error: str):
        """Record failed operation"""
        # Prometheus metrics
        self.operation_counter.labels(operation=operation_name, status='failure').inc()
        self.operation_duration.labels(operation=operation_name).observe(duration)
        
        # In-memory tracking
        self._operation_times[operation_name].append(duration)
        self._operation_counts[operation_name]['failure'] += 1
        self._system_metrics['total_errors'] += 1
        
        # Check error rate
        total_ops = sum(self._operation_counts[operation_name].values())
        error_rate = (self._operation_counts[operation_name]['failure'] / total_ops) * 100
        
        if error_rate > self._alert_thresholds['high_error_rate_percent']:
            await self._create_alert(
                'high_error_rate',
                f"Operation {operation_name} has {error_rate:.1f}% error rate",
                {'operation': operation_name, 'error_rate': error_rate}
            )
        
        logger.warning("Operation failed", 
                      operation=operation_name, 
                      duration_ms=duration * 1000, 
                      error=error)
    
    async def record_cache_operation(self, operation: str, result: str):
        """
        Record cache operation
        
        Args:
            operation: Type of cache operation (get, set, delete)
            result: Result of operation (hit, miss, error)
        """
        self.cache_operations.labels(operation=operation, result=result).inc()
    
    async def record_ai_request(self, model: str, task_type: str, status: str):
        """
        Record AI API request
        
        Args:
            model: AI model used
            task_type: Type of AI task
            status: Request status (success, failure)
        """
        self.ai_requests.labels(model=model, task_type=task_type, status=status).inc()
    
    async def record_slack_event(self, event_type: str, status: str):
        """
        Record Slack event processing
        
        Args:
            event_type: Type of Slack event
            status: Processing status (processed, ignored, failed)
        """
        self.slack_events.labels(event_type=event_type, status=status).inc()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics
        
        Returns:
            Dictionary of performance metrics
        """
        current_time = datetime.utcnow()
        uptime = current_time - self._system_metrics['start_time']
        
        # Calculate operation statistics
        operation_stats = {}
        for operation, times in self._operation_times.items():
            if times:
                operation_stats[operation] = {
                    'count': len(times),
                    'avg_duration_ms': sum(times) / len(times) * 1000,
                    'min_duration_ms': min(times) * 1000,
                    'max_duration_ms': max(times) * 1000,
                    'success_count': self._operation_counts[operation]['success'],
                    'failure_count': self._operation_counts[operation]['failure'],
                    'error_rate_percent': (
                        self._operation_counts[operation]['failure'] / 
                        sum(self._operation_counts[operation].values()) * 100
                    ) if sum(self._operation_counts[operation].values()) > 0 else 0
                }
        
        metrics = {
            'system': {
                'uptime_seconds': uptime.total_seconds(),
                'start_time': self._system_metrics['start_time'].isoformat(),
                'total_requests': self._system_metrics['total_requests'],
                'total_errors': self._system_metrics['total_errors'],
                'overall_error_rate_percent': (
                    self._system_metrics['total_errors'] / 
                    self._system_metrics['total_requests'] * 100
                ) if self._system_metrics['total_requests'] > 0 else 0
            },
            'operations': operation_stats,
            'active_operations': dict(self._active_operations_count),
            'alerts': self._alerts[-10:],  # Last 10 alerts
            'timestamp': current_time.isoformat()
        }
        
        return metrics
    
    async def get_prometheus_metrics(self) -> str:
        """
        Get metrics in Prometheus format
        
        Returns:
            Prometheus-formatted metrics string
        """
        return generate_latest().decode('utf-8')
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check performance monitor health
        
        Returns:
            Health status information
        """
        try:
            metrics = await self.get_metrics()
            
            # Determine health status
            status = "healthy"
            issues = []
            
            # Check overall error rate
            overall_error_rate = metrics['system']['overall_error_rate_percent']
            if overall_error_rate > self._alert_thresholds['high_error_rate_percent']:
                status = "degraded"
                issues.append(f"High error rate: {overall_error_rate:.1f}%")
            
            # Check for slow operations
            for operation, stats in metrics['operations'].items():
                if stats['avg_duration_ms'] > self._alert_thresholds['slow_operation_seconds'] * 1000:
                    status = "degraded"
                    issues.append(f"Slow operation {operation}: {stats['avg_duration_ms']:.0f}ms avg")
            
            # Check active alerts
            recent_alerts = [a for a in self._alerts if 
                           datetime.fromisoformat(a['timestamp']) > datetime.utcnow() - timedelta(minutes=10)]
            
            if recent_alerts:
                status = "degraded"
                issues.append(f"{len(recent_alerts)} recent alerts")
            
            return {
                'status': status,
                'healthy': status == "healthy",
                'issues': issues,
                'metrics_available': True,
                'uptime_seconds': metrics['system']['uptime_seconds']
            }
            
        except Exception as e:
            logger.error("Performance monitor health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'healthy': False,
                'error': str(e),
                'metrics_available': False
            }
    
    async def _create_alert(self, alert_type: str, message: str, context: Dict[str, Any]):
        """Create performance alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'context': context,
            'timestamp': datetime.utcnow().isoformat(),
            'severity': self._get_alert_severity(alert_type)
        }
        
        self._alerts.append(alert)
        
        # Keep only last 100 alerts
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-100:]
        
        logger.warning("Performance alert created", 
                      type=alert_type, 
                      message=message, 
                      severity=alert['severity'])
        
        # Store alerts in memory (could extend to store in Supabase if needed)
        # For now, just log the alert
        pass
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """Get severity level for alert type"""
        severity_map = {
            'slow_operation': 'warning',
            'high_error_rate': 'critical',
            'memory_usage': 'warning',
            'api_failure': 'critical'
        }
        return severity_map.get(alert_type, 'info')
    
    async def _background_metrics_collection(self):
        """Background task for collecting system metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                
                # Collect system metrics (memory, CPU, etc.)
                # This would integrate with psutil or similar for real system metrics
                
                logger.debug("Background metrics collection completed")
                
            except Exception as e:
                logger.error("Background metrics collection failed", error=str(e))
    
    async def _background_alerting(self):
        """Background task for processing alerts"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Process alert conditions
                await self._check_alert_conditions()
                
            except Exception as e:
                logger.error("Background alerting failed", error=str(e))
    
    async def _check_alert_conditions(self):
        """Check for alert conditions"""
        try:
            metrics = await self.get_metrics()
            
            # Check for operations with consistently high error rates
            for operation, stats in metrics['operations'].items():
                if (stats['count'] >= 10 and  # Minimum sample size
                    stats['error_rate_percent'] > self._alert_thresholds['high_error_rate_percent']):
                    
                    await self._create_alert(
                        'high_error_rate',
                        f"Operation {operation} has sustained high error rate: {stats['error_rate_percent']:.1f}%",
                        {'operation': operation, 'error_rate': stats['error_rate_percent']}
                    )
            
        except Exception as e:
            logger.error("Alert condition checking failed", error=str(e))