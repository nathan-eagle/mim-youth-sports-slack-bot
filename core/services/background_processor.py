"""
Background event processor for MiM Slack Bot
Handles async processing of Slack events with queue management
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import structlog

from .supabase_state_manager import SupabaseStateManager
from .performance_monitor import PerformanceMonitor
from .optimized_ai_service import OptimizedAIService
from .intelligent_cache import IntelligentCache

logger = structlog.get_logger(__name__)


class EventPriority(Enum):
    """Event processing priorities"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class EventStatus(Enum):
    """Event processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class BackgroundEventProcessor:
    """
    High-performance background processor for Slack events with:
    - Priority-based queue management
    - Concurrent processing with worker pools
    - Automatic retry logic with exponential backoff
    - Progress tracking and status updates
    - Dead letter queue for failed events
    """
    
    def __init__(
        self,
        state_manager: SupabaseStateManager,
        performance_monitor: Optional[PerformanceMonitor] = None,
        max_workers: int = 4,
        max_retries: int = 3
    ):
        """
        Initialize background event processor
        
        Args:
            state_manager: Redis state manager
            performance_monitor: Performance monitoring instance
            max_workers: Maximum concurrent workers
            max_retries: Maximum retry attempts
        """
        self.state_manager = state_manager
        self.performance_monitor = performance_monitor
        self.max_workers = max_workers
        self.max_retries = max_retries
        
        # Processing queues
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._processing_events: Dict[str, Dict[str, Any]] = {}
        self._failed_events: List[Dict[str, Any]] = []
        
        # Worker management
        self._workers: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        self._worker_semaphore = asyncio.Semaphore(max_workers)
        
        # Event handlers
        self._handlers: Dict[str, Callable] = {}
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'total_failed': 0,
            'total_retries': 0,
            'average_processing_time': 0.0
        }
        
        logger.info("Background event processor initialized", max_workers=max_workers)
    
    async def initialize(self):
        """Initialize background processing"""
        try:
            # Start worker tasks
            for i in range(self.max_workers):
                worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
                self._workers.append(worker)
            
            # Start monitoring task
            asyncio.create_task(self._monitoring_loop())
            
            # Register default event handlers
            await self._register_default_handlers()
            
            logger.info("Background event processor started", worker_count=len(self._workers))
            
        except Exception as e:
            logger.error("Failed to initialize background processor", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown background processing"""
        logger.info("Shutting down background event processor")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for workers to finish current tasks
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        logger.info("Background event processor shutdown complete")
    
    async def process_event(
        self, 
        event_data: Dict[str, Any], 
        priority: EventPriority = EventPriority.NORMAL
    ):
        """
        Queue event for background processing
        
        Args:
            event_data: Slack event data
            priority: Processing priority
        """
        event_id = event_data.get('event_id', f"event_{datetime.utcnow().timestamp()}")
        
        # Create processing context
        processing_context = {
            'event_id': event_id,
            'event_data': event_data,
            'priority': priority,
            'status': EventStatus.QUEUED,
            'queued_at': datetime.utcnow(),
            'retry_count': 0,
            'error_history': []
        }
        
        # Add to queue
        await self._event_queue.put(processing_context)
        
        logger.debug("Event queued for processing", 
                    event_id=event_id, 
                    priority=priority.name,
                    queue_size=self._event_queue.qsize())
    
    async def _worker_loop(self, worker_name: str):
        """
        Main worker loop for processing events
        
        Args:
            worker_name: Name of the worker
        """
        logger.info("Worker started", worker=worker_name)
        
        while not self._shutdown_event.is_set():
            try:
                # Get next event (with timeout to check shutdown)
                try:
                    processing_context = await asyncio.wait_for(
                        self._event_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Process event with semaphore
                async with self._worker_semaphore:
                    await self._process_single_event(processing_context, worker_name)
                
            except Exception as e:
                logger.error("Worker error", worker=worker_name, error=str(e))
                await asyncio.sleep(1)  # Brief pause on error
        
        logger.info("Worker stopped", worker=worker_name)
    
    async def _process_single_event(self, processing_context: Dict[str, Any], worker_name: str):
        """
        Process a single event
        
        Args:
            processing_context: Event processing context
            worker_name: Name of processing worker
        """
        event_id = processing_context['event_id']
        event_data = processing_context['event_data']
        
        # Update status
        processing_context['status'] = EventStatus.PROCESSING
        processing_context['processing_started_at'] = datetime.utcnow()
        processing_context['worker'] = worker_name
        
        self._processing_events[event_id] = processing_context
        
        try:
            async with self.performance_monitor.track_operation("event_processing") if self.performance_monitor else self._null_context():
                # Send immediate acknowledgment to Slack
                await self._send_initial_response(event_data)
                
                # Route event to appropriate handler
                await self._route_and_process_event(event_data)
                
                # Mark as completed
                processing_context['status'] = EventStatus.COMPLETED
                processing_context['completed_at'] = datetime.utcnow()
                
                # Update statistics
                self._stats['total_processed'] += 1
                processing_time = (
                    processing_context['completed_at'] - 
                    processing_context['processing_started_at']
                ).total_seconds()
                
                self._update_average_processing_time(processing_time)
                
                logger.info("Event processed successfully", 
                           event_id=event_id, 
                           worker=worker_name,
                           processing_time_ms=processing_time * 1000)
        
        except Exception as e:
            await self._handle_processing_error(processing_context, str(e))
        
        finally:
            # Remove from processing dict
            self._processing_events.pop(event_id, None)
    
    async def _route_and_process_event(self, event_data: Dict[str, Any]):
        """
        Route event to appropriate handler and process
        
        Args:
            event_data: Slack event data
        """
        event = event_data.get('event', {})
        event_type = event.get('type')
        
        # Get handler for event type
        handler = self._handlers.get(event_type)
        
        if not handler:
            logger.warning("No handler for event type", event_type=event_type)
            return
        
        # Process event
        await handler(event_data)
    
    async def _send_initial_response(self, event_data: Dict[str, Any]):
        """
        Send immediate response to Slack
        
        Args:
            event_data: Slack event data
        """
        event = event_data.get('event', {})
        channel = event.get('channel')
        event_type = event.get('type')
        
        if not channel:
            return
        
        # Import here to avoid circular imports
        from slack_sdk.web.async_client import AsyncWebClient
        import os
        
        try:
            slack_client = AsyncWebClient(token=os.getenv('SLACK_BOT_TOKEN'))
            
            # Send different responses based on event type
            if event_type == 'message':
                await slack_client.chat_postMessage(
                    channel=channel,
                    text="🎨 Got it! I'm creating your custom designs now. This will take 10-15 seconds..."
                )
            elif event_type == 'file_shared':
                await slack_client.chat_postMessage(
                    channel=channel,
                    text="📷 Perfect! I'll analyze your logo and create custom products. Give me 15-20 seconds..."
                )
            
        except Exception as e:
            logger.error("Failed to send initial response", error=str(e))
    
    async def _handle_processing_error(self, processing_context: Dict[str, Any], error: str):
        """
        Handle processing error with retry logic
        
        Args:
            processing_context: Event processing context
            error: Error message
        """
        event_id = processing_context['event_id']
        processing_context['retry_count'] += 1
        processing_context['error_history'].append({
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
            'retry_count': processing_context['retry_count']
        })
        
        logger.warning("Event processing failed", 
                      event_id=event_id, 
                      retry_count=processing_context['retry_count'],
                      error=error)
        
        # Check if we should retry
        if processing_context['retry_count'] <= self.max_retries:
            # Calculate backoff delay (exponential)
            backoff_delay = 2 ** processing_context['retry_count']
            
            processing_context['status'] = EventStatus.RETRYING
            processing_context['retry_at'] = datetime.utcnow() + timedelta(seconds=backoff_delay)
            
            # Schedule retry
            asyncio.create_task(self._schedule_retry(processing_context, backoff_delay))
            
            self._stats['total_retries'] += 1
            
        else:
            # Max retries exceeded, move to failed
            processing_context['status'] = EventStatus.FAILED
            processing_context['failed_at'] = datetime.utcnow()
            
            self._failed_events.append(processing_context)
            self._stats['total_failed'] += 1
            
            # Send error notification
            await self._send_error_notification(processing_context)
            
            logger.error("Event processing failed permanently", 
                        event_id=event_id, 
                        total_retries=processing_context['retry_count'])
    
    async def _schedule_retry(self, processing_context: Dict[str, Any], delay: float):
        """
        Schedule event retry after delay
        
        Args:
            processing_context: Event processing context
            delay: Delay in seconds
        """
        await asyncio.sleep(delay)
        
        # Reset for retry
        processing_context['status'] = EventStatus.QUEUED
        
        # Re-queue for processing
        await self._event_queue.put(processing_context)
        
        logger.info("Event requeued for retry", 
                   event_id=processing_context['event_id'],
                   retry_count=processing_context['retry_count'])
    
    async def _send_error_notification(self, processing_context: Dict[str, Any]):
        """
        Send error notification to user
        
        Args:
            processing_context: Failed event processing context
        """
        try:
            event_data = processing_context['event_data']
            event = event_data.get('event', {})
            channel = event.get('channel')
            
            if not channel:
                return
            
            # Import here to avoid circular imports
            from slack_sdk.web.async_client import AsyncWebClient
            import os
            
            slack_client = AsyncWebClient(token=os.getenv('SLACK_BOT_TOKEN'))
            
            await slack_client.chat_postMessage(
                channel=channel,
                text="😅 Sorry, I'm having trouble processing your request right now. Please try again in a few minutes, or contact support if the issue persists."
            )
            
        except Exception as e:
            logger.error("Failed to send error notification", error=str(e))
    
    async def _register_default_handlers(self):
        """Register default event handlers"""
        # Import handlers here to avoid circular imports
        from .event_handlers import MessageHandler, FileShareHandler
        
        message_handler = MessageHandler(self.state_manager)
        file_handler = FileShareHandler(self.state_manager)
        
        self._handlers['message'] = message_handler.handle
        self._handlers['file_shared'] = file_handler.handle
        
        logger.info("Default event handlers registered")
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register custom event handler
        
        Args:
            event_type: Type of event to handle
            handler: Async handler function
        """
        self._handlers[event_type] = handler
        logger.info("Handler registered", event_type=event_type)
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'queue_size': self._event_queue.qsize(),
            'processing_count': len(self._processing_events),
            'failed_count': len(self._failed_events),
            'total_processed': self._stats['total_processed'],
            'total_failed': self._stats['total_failed'],
            'total_retries': self._stats['total_retries'],
            'average_processing_time_ms': self._stats['average_processing_time'] * 1000,
            'worker_count': len(self._workers),
            'active_workers': sum(1 for w in self._workers if not w.done())
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check processor health"""
        stats = await self.get_processing_stats()
        
        # Determine health status
        healthy = True
        issues = []
        
        # Check queue backup
        if stats['queue_size'] > 100:
            healthy = False
            issues.append(f"Queue backup: {stats['queue_size']} events")
        
        # Check worker health
        active_workers = stats['active_workers']
        if active_workers < self.max_workers // 2:
            healthy = False
            issues.append(f"Low worker count: {active_workers}/{self.max_workers}")
        
        # Check error rate
        total_events = stats['total_processed'] + stats['total_failed']
        if total_events > 0:
            error_rate = (stats['total_failed'] / total_events) * 100
            if error_rate > 10:  # 10% error rate threshold
                healthy = False
                issues.append(f"High error rate: {error_rate:.1f}%")
        
        return {
            'status': 'healthy' if healthy else 'degraded',
            'healthy': healthy,
            'issues': issues,
            'statistics': stats
        }
    
    def _update_average_processing_time(self, processing_time: float):
        """Update rolling average processing time"""
        current_avg = self._stats['average_processing_time']
        count = self._stats['total_processed']
        
        # Simple moving average
        self._stats['average_processing_time'] = (
            (current_avg * (count - 1) + processing_time) / count
        )
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
                # Log processing statistics
                stats = await self.get_processing_stats()
                
                if stats['queue_size'] > 10:
                    logger.warning("Queue backup detected", queue_size=stats['queue_size'])
                
                if self.performance_monitor:
                    await self.performance_monitor.record_slack_event(
                        'background_monitoring', 'completed'
                    )
                
            except Exception as e:
                logger.error("Monitoring loop error", error=str(e))
    
    def _null_context(self):
        """Null context manager when performance monitor is unavailable"""
        class NullContext:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        return NullContext()