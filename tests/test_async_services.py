"""
Comprehensive test suite for async services
Tests the new refactored architecture components
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Import the services to test
from core.config import Settings
from core.services.redis_state_manager import RedisStateManager
from core.services.intelligent_cache import IntelligentCache, CacheKey
from core.services.optimized_ai_service import OptimizedAIService, ModelSelector
from core.services.async_product_service import AsyncProductService
from core.services.background_processor import BackgroundEventProcessor
from core.services.service_orchestrator import ServiceOrchestrator


class TestSettings:
    """Test configuration"""
    
    @pytest.fixture
    def test_settings(self):
        """Create test settings"""
        return Settings(
            slack_bot_token="test-token",
            slack_signing_secret="test-secret",
            openai_api_key="test-openai-key",
            printify_api_token="test-printify-token",
            stripe_secret_key="test-stripe-key",
            stripe_publishable_key="test-stripe-pub",
            stripe_webhook_secret="test-stripe-webhook",
            supabase_url="test-supabase-url",
            supabase_anon_key="test-supabase-anon",
            supabase_service_key="test-supabase-service",
            redis_url="redis://localhost:6379/1"  # Use test database
        )


class TestCacheKey:
    """Test cache key generation"""
    
    def test_hash_content_consistency(self):
        """Test that hash generation is consistent"""
        content1 = {"test": "data", "number": 123}
        content2 = {"number": 123, "test": "data"}  # Different order
        
        hash1 = CacheKey.hash_content(content1)
        hash2 = CacheKey.hash_content(content2)
        
        assert hash1 == hash2  # Should be the same despite different order
        assert len(hash1) == 16  # Should be 16 characters
    
    def test_ai_response_key(self):
        """Test AI response cache key generation"""
        key = CacheKey.ai_response("test prompt", "gpt-4o-mini", context="test")
        
        assert key.startswith("ai_response:")
        assert len(key) > len("ai_response:")
    
    def test_logo_analysis_key(self):
        """Test logo analysis cache key generation"""
        key = CacheKey.logo_analysis("https://example.com/logo.png", "colors")
        
        assert key.startswith("logo_analysis:colors:")
        
    def test_product_recommendation_key(self):
        """Test product recommendation cache key generation"""
        intent = "I want a blue shirt"
        context = {"colors": ["blue"], "preferences": {}}
        
        key = CacheKey.product_recommendation(intent, context)
        
        assert key.startswith("product_rec:")


class TestModelSelector:
    """Test AI model selection logic"""
    
    @pytest.fixture
    def model_selector(self, test_settings):
        """Create model selector instance"""
        return ModelSelector(test_settings)
    
    def test_automatic_model_selection(self, model_selector):
        """Test automatic model selection based on task type"""
        # Simple tasks should use mini model
        model = model_selector.select_model("intent_analysis", "auto")
        assert "mini" in model
        
        # Complex tasks should use better model
        model = model_selector.select_model("color_analysis", "auto")
        assert "gpt-4o" in model or "gpt-4" in model
    
    def test_explicit_complexity_selection(self, model_selector):
        """Test explicit complexity level selection"""
        simple_model = model_selector.select_model("any_task", "simple")
        complex_model = model_selector.select_model("any_task", "complex")
        premium_model = model_selector.select_model("any_task", "premium")
        
        assert simple_model != complex_model
        assert complex_model != premium_model
    
    def test_model_info_retrieval(self, model_selector):
        """Test model information retrieval"""
        info = model_selector.get_model_info("gpt-4o-mini")
        
        assert "cost" in info
        assert "speed" in info
        assert "quality" in info
        assert "best_for" in info


@pytest.mark.asyncio
class TestRedisStateManager:
    """Test Redis state management"""
    
    @pytest.fixture
    async def mock_redis(self):
        """Create mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.pipeline.return_value = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    async def state_manager(self, mock_redis):
        """Create state manager with mocked Redis"""
        manager = RedisStateManager("redis://localhost:6379/1")
        manager.redis = mock_redis
        manager.pool = Mock()
        return manager
    
    async def test_conversation_update(self, state_manager, mock_redis):
        """Test conversation state updates"""
        updates = {
            "last_message": "Hello",
            "user_data": {"name": "test"}
        }
        
        # Setup mock pipeline
        mock_pipeline = AsyncMock()
        mock_redis.pipeline.return_value = mock_pipeline
        mock_pipeline.execute.return_value = [True, True]
        
        result = await state_manager.update_conversation(
            "channel123", "user456", updates
        )
        
        assert result is True
        mock_pipeline.hset.assert_called()
        mock_pipeline.expire.assert_called()
        mock_pipeline.execute.assert_called_once()
    
    async def test_conversation_retrieval(self, state_manager, mock_redis):
        """Test conversation state retrieval"""
        mock_data = {
            "last_message": "Hello",
            "user_data": '{"name": "test"}'  # JSON string
        }
        mock_redis.hgetall.return_value = mock_data
        
        result = await state_manager.get_conversation("channel123", "user456")
        
        assert result["last_message"] == "Hello"
        assert result["user_data"] == {"name": "test"}  # Should be parsed from JSON
    
    async def test_event_deduplication(self, state_manager, mock_redis):
        """Test event deduplication logic"""
        event_data = {
            "event_id": "test123",
            "event": {
                "ts": "1234567890",
                "user": "user123",
                "text": "hello"
            }
        }
        
        # First call - should not be duplicate
        mock_redis.exists.return_value = False
        mock_redis.setex.return_value = True
        
        is_duplicate = await state_manager.is_event_duplicate(event_data)
        assert is_duplicate is False
        
        # Second call - should be duplicate
        mock_redis.exists.return_value = True
        
        is_duplicate = await state_manager.is_event_duplicate(event_data)
        assert is_duplicate is True
    
    async def test_health_check(self, state_manager, mock_redis):
        """Test health check functionality"""
        mock_redis.ping.return_value = True
        state_manager.pool = Mock()
        state_manager.pool.created_connections = 5
        state_manager.pool._available_connections = [Mock(), Mock()]
        state_manager.pool._in_use_connections = [Mock(), Mock(), Mock()]
        
        health = await state_manager.health_check()
        
        assert health["healthy"] is True
        assert health["status"] == "healthy"
        assert "connection_pool" in health


@pytest.mark.asyncio
class TestIntelligentCache:
    """Test intelligent caching functionality"""
    
    @pytest.fixture
    async def mock_redis(self):
        """Create mock Redis client"""
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        return mock_redis
    
    @pytest.fixture
    async def cache(self, mock_redis, test_settings):
        """Create cache instance with mocked Redis"""
        cache = IntelligentCache(mock_redis, test_settings)
        await cache.initialize()
        return cache
    
    async def test_basic_cache_operations(self, cache, mock_redis):
        """Test basic get/set operations"""
        # Test set
        mock_redis.setex.return_value = True
        result = await cache.set("test_key", {"data": "value"}, ttl=3600)
        assert result is True
        
        # Test get
        mock_redis.get.return_value = '{"data": "value"}'
        result = await cache.get("test_key")
        assert result == {"data": "value"}
    
    async def test_ai_response_caching(self, cache, mock_redis):
        """Test AI response caching"""
        prompt = "What is the color of the sky?"
        model = "gpt-4o-mini"
        response = {"answer": "blue", "confidence": "high"}
        
        # Mock successful cache set
        mock_redis.setex.return_value = True
        
        result = await cache.cache_ai_response(prompt, model, response)
        assert result is True
        
        # Verify the cache key and data structure
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert len(call_args[0]) == 3  # key, ttl, value
        
        # Parse the cached data
        cached_data = json.loads(call_args[0][2])
        assert cached_data["response"] == response
        assert cached_data["model"] == model
        assert "cached_at" in cached_data
    
    async def test_logo_analysis_caching(self, cache, mock_redis):
        """Test logo analysis caching"""
        logo_url = "https://example.com/logo.png"
        analysis = {
            "primary_colors": ["blue", "white"],
            "secondary_colors": ["gray"],
            "confidence": "high"
        }
        
        mock_redis.setex.return_value = True
        
        result = await cache.cache_logo_analysis(logo_url, analysis)
        assert result is True
        
        # Test retrieval
        mock_redis.get.return_value = json.dumps({
            "analysis": analysis,
            "logo_url": logo_url,
            "analysis_type": "colors",
            "cached_at": datetime.utcnow().isoformat()
        })
        
        retrieved = await cache.get_logo_analysis(logo_url)
        assert retrieved == analysis
    
    async def test_cache_statistics(self, cache):
        """Test cache statistics tracking"""
        # Simulate some hits and misses
        cache._hits = 10
        cache._misses = 3
        cache._errors = 1
        
        stats = await cache.get_cache_stats()
        
        assert stats["hits"] == 10
        assert stats["misses"] == 3
        assert stats["errors"] == 1
        assert stats["total_requests"] == 13
        assert stats["hit_rate_percent"] == 76.92  # 10/13 * 100


@pytest.mark.asyncio
class TestOptimizedAIService:
    """Test optimized AI service"""
    
    @pytest.fixture
    async def mock_cache(self):
        """Create mock cache"""
        cache = AsyncMock()
        cache.get_ai_response.return_value = None  # No cache hit by default
        cache.cache_ai_response.return_value = True
        return cache
    
    @pytest.fixture
    async def ai_service(self, test_settings, mock_cache):
        """Create AI service with mocked dependencies"""
        with patch('core.services.optimized_ai_service.AsyncOpenAI') as mock_openai:
            service = OptimizedAIService(test_settings, mock_cache)
            service.client = AsyncMock()
            return service
    
    async def test_intent_analysis_caching(self, ai_service, mock_cache):
        """Test intent analysis with caching"""
        message = "I want a blue shirt for my team"
        expected_result = {
            "intent_type": "product_request",
            "confidence": "high",
            "extracted_info": {
                "product_type": "shirt",
                "colors": ["blue"],
                "customization": "team"
            }
        }
        
        # Mock cache miss, then AI response
        mock_cache.get_ai_response.return_value = None
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(expected_result)
        mock_response.usage.total_tokens = 150
        
        ai_service.client.chat.completions.create.return_value = mock_response
        
        result = await ai_service.analyze_user_intent(message)
        
        assert result == expected_result
        
        # Verify caching was attempted
        mock_cache.cache_ai_response.assert_called_once()
    
    async def test_logo_color_analysis(self, ai_service, mock_cache):
        """Test logo color analysis"""
        logo_url = "https://example.com/logo.png"
        expected_result = {
            "primary_colors": ["blue", "white"],
            "secondary_colors": ["gray"],
            "recommended_merchandise_colors": ["blue", "white", "navy"],
            "confidence": "high"
        }
        
        # Mock cache miss
        mock_cache.get_logo_analysis.return_value = None
        mock_cache.cache_logo_analysis.return_value = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(expected_result)
        mock_response.usage.total_tokens = 200
        
        ai_service.client.chat.completions.create.return_value = mock_response
        
        result = await ai_service.analyze_logo_colors(logo_url)
        
        assert result == expected_result
        assert "blue" in result["primary_colors"]
        assert result["confidence"] == "high"
    
    async def test_product_recommendations(self, ai_service, mock_cache):
        """Test product recommendations"""
        intent = "I need team jerseys"
        user_preferences = {"colors": ["blue"], "size": "youth"}
        available_products = [
            {"id": "12", "title": "Jersey Tee", "category": "shirts"},
            {"id": "92", "title": "Hoodie", "category": "hoodies"}
        ]
        
        expected_recommendations = [
            {
                "product_id": "12",
                "confidence": "high",
                "reasoning": "Perfect match for team jerseys",
                "match_score": 9
            }
        ]
        
        # Mock cache miss
        mock_cache.get_product_recommendation.return_value = None
        mock_cache.cache_product_recommendation.return_value = True
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(expected_recommendations)
        
        ai_service.client.chat.completions.create.return_value = mock_response
        
        result = await ai_service.recommend_products(
            intent, user_preferences, available_products
        )
        
        assert len(result) == 1
        assert result[0]["product_id"] == "12"
        assert result[0]["confidence"] == "high"
    
    async def test_performance_stats(self, ai_service, mock_cache):
        """Test performance statistics tracking"""
        # Simulate some usage
        ai_service._total_requests = 50
        ai_service._cache_hits = 20
        ai_service._cost_saved = 1.25
        
        # Mock cache stats
        mock_cache.get_cache_stats.return_value = {
            "hits": 20,
            "misses": 30,
            "hit_rate_percent": 40.0
        }
        
        stats = await ai_service.get_performance_stats()
        
        assert stats["total_ai_requests"] == 50
        assert stats["cache_hits"] == 20
        assert stats["cache_hit_rate_percent"] == 40.0
        assert stats["estimated_cost_saved"] == 1.25
        assert "cache_performance" in stats


@pytest.mark.asyncio
class TestAsyncProductService:
    """Test async product service"""
    
    @pytest.fixture
    async def mock_dependencies(self, test_settings):
        """Create mocked dependencies"""
        cache = AsyncMock()
        ai_service = AsyncMock()
        
        return test_settings, cache, ai_service
    
    @pytest.fixture
    async def product_service(self, mock_dependencies):
        """Create product service with mocked dependencies"""
        settings, cache, ai_service = mock_dependencies
        
        service = AsyncProductService(settings, cache, ai_service)
        
        # Mock the session and other external dependencies
        service._session = AsyncMock()
        service._products_cache = {
            "12": {
                "id": "12",
                "title": "Jersey Tee",
                "category": "shirts",
                "variants": [
                    {"id": "v1", "options": {"color": "blue", "size": "M"}},
                    {"id": "v2", "options": {"color": "red", "size": "M"}}
                ]
            },
            "92": {
                "id": "92", 
                "title": "College Hoodie",
                "category": "hoodies",
                "variants": [
                    {"id": "v3", "options": {"color": "blue", "size": "L"}},
                    {"id": "v4", "options": {"color": "gray", "size": "L"}}
                ]
            }
        }
        service._last_cache_update = datetime.utcnow()
        
        return service
    
    async def test_product_recommendations(self, product_service, mock_dependencies):
        """Test product recommendations with AI integration"""
        settings, cache, ai_service = mock_dependencies
        
        user_intent = "I want team shirts in blue"
        logo_colors = ["blue", "white"]
        
        # Mock cache miss
        cache.get_product_recommendation.return_value = None
        cache.cache_product_recommendation.return_value = True
        
        # Mock AI recommendations
        ai_service.recommend_products.return_value = [
            {
                "product_id": "12",
                "confidence": "high",
                "reasoning": "Perfect for team shirts",
                "match_score": 9
            }
        ]
        
        recommendations = await product_service.get_product_recommendations(
            user_intent=user_intent,
            logo_colors=logo_colors,
            max_products=3
        )
        
        assert len(recommendations) == 1
        assert recommendations[0]["product_id"] == "12"
        assert "product_data" in recommendations[0]
        assert "colors" in recommendations[0]
        assert "sizes" in recommendations[0]
    
    async def test_parallel_mockup_generation(self, product_service):
        """Test parallel mockup generation"""
        logo_url = "https://example.com/logo.png"
        recommendations = [
            {
                "product_data": {"id": "12", "title": "Jersey Tee"},
                "reasoning": "Great for teams"
            },
            {
                "product_data": {"id": "92", "title": "College Hoodie"},
                "reasoning": "Warm and comfortable"
            }
        ]
        
        # Mock the single mockup generation
        async def mock_generate_single_mockup(*args, **kwargs):
            task_id = kwargs.get('task_id', 'test')
            return {
                'success': True,
                'task_id': task_id,
                'product_id': '12',
                'mockup_url': 'https://example.com/mockup.png',
                'purchase_url': 'https://example.com/purchase/123'
            }
        
        product_service._generate_single_mockup_with_ai_colors = mock_generate_single_mockup
        
        results = await product_service.generate_mockups_parallel(
            logo_url, recommendations
        )
        
        assert len(results) == 2
        assert all(r['success'] for r in results)
        assert all('mockup_url' in r for r in results)
    
    async def test_colors_for_product(self, product_service):
        """Test getting colors for a specific product"""
        colors = await product_service.get_colors_for_product("12")
        
        assert "blue" in colors
        assert "red" in colors
        assert len(colors) == 2
    
    async def test_sizes_for_product(self, product_service):
        """Test getting sizes for a specific product"""
        sizes = await product_service.get_sizes_for_product("12")
        
        assert "M" in sizes
        assert len(sizes) == 1  # Only M size in test data
    
    async def test_service_health_check(self, product_service):
        """Test service health check"""
        health = await product_service.health_check()
        
        assert health["healthy"] is True
        assert health["status"] == "healthy"
        assert "statistics" in health
        assert health["statistics"]["products_cached"] == 2


@pytest.mark.asyncio 
class TestBackgroundProcessor:
    """Test background event processor"""
    
    @pytest.fixture
    async def mock_state_manager(self):
        """Create mock state manager"""
        manager = AsyncMock()
        manager.update_conversation.return_value = True
        return manager
    
    @pytest.fixture
    async def mock_performance_monitor(self):
        """Create mock performance monitor"""
        monitor = AsyncMock()
        monitor.track_operation.return_value = AsyncMock()
        return monitor
    
    @pytest.fixture
    async def processor(self, mock_state_manager, mock_performance_monitor):
        """Create background processor with mocked dependencies"""
        processor = BackgroundEventProcessor(
            state_manager=mock_state_manager,
            performance_monitor=mock_performance_monitor,
            max_workers=2,
            max_retries=2
        )
        
        # Mock the event handlers
        processor._handlers = {
            'message': AsyncMock(return_value={'status': 'success'}),
            'file_shared': AsyncMock(return_value={'status': 'success'})
        }
        
        return processor
    
    async def test_event_processing(self, processor):
        """Test basic event processing"""
        event_data = {
            'event_id': 'test123',
            'event': {
                'type': 'message',
                'user': 'user123',
                'channel': 'channel123',
                'text': 'Hello'
            }
        }
        
        # Process event (will be queued)
        await processor.process_event(event_data)
        
        # Verify event was queued
        assert processor._event_queue.qsize() > 0
    
    async def test_processing_stats(self, processor):
        """Test processing statistics"""
        # Simulate some processing
        processor._stats['total_processed'] = 10
        processor._stats['total_failed'] = 2
        processor._stats['average_processing_time'] = 1.5
        
        stats = await processor.get_processing_stats()
        
        assert stats['total_processed'] == 10
        assert stats['total_failed'] == 2
        assert stats['average_processing_time_ms'] == 1500
        assert 'queue_size' in stats
        assert 'worker_count' in stats
    
    async def test_health_check(self, processor):
        """Test processor health check"""
        health = await processor.health_check()
        
        assert 'status' in health
        assert 'healthy' in health
        assert 'statistics' in health


@pytest.mark.asyncio
class TestServiceOrchestrator:
    """Test service orchestrator"""
    
    @pytest.fixture
    async def test_settings(self):
        """Create test settings for orchestrator"""
        return Settings(
            slack_bot_token="test-token",
            slack_signing_secret="test-secret", 
            openai_api_key="test-openai-key",
            printify_api_token="test-printify-token",
            stripe_secret_key="test-stripe-key",
            stripe_publishable_key="test-stripe-pub",
            stripe_webhook_secret="test-stripe-webhook",
            supabase_url="postgresql://test:test@localhost/test",
            supabase_anon_key="test-supabase-anon",
            supabase_service_key="test-supabase-service",
            redis_url="redis://localhost:6379/1"
        )
    
    @pytest.fixture
    async def orchestrator(self, test_settings):
        """Create orchestrator instance"""
        orchestrator = ServiceOrchestrator(test_settings)
        
        # Mock the Redis connection for testing
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_redis_class.from_url.return_value = mock_redis
            
            # Mock other external dependencies
            with patch('core.services.redis_state_manager.RedisStateManager') as mock_state_manager_class:
                mock_state_manager = AsyncMock()
                mock_state_manager.initialize.return_value = None
                mock_state_manager.health_check.return_value = {"healthy": True, "status": "healthy"}
                mock_state_manager_class.return_value = mock_state_manager
                
                with patch('core.services.performance_monitor.PerformanceMonitor') as mock_monitor_class:
                    mock_monitor = AsyncMock()
                    mock_monitor.initialize.return_value = None
                    mock_monitor.health_check.return_value = {"healthy": True, "status": "healthy"}
                    mock_monitor_class.return_value = mock_monitor
                    
                    # Initialize with mocked dependencies
                    await orchestrator.initialize()
                    
                    return orchestrator
    
    async def test_initialization(self, orchestrator):
        """Test orchestrator initialization"""
        assert orchestrator.initialized is True
        assert orchestrator.state_manager is not None
        assert orchestrator.performance_monitor is not None
    
    async def test_service_access_methods(self, orchestrator):
        """Test service access methods"""
        # These should not raise exceptions since orchestrator is initialized
        state_manager = orchestrator.get_state_manager()
        assert state_manager is not None
        
        performance_monitor = orchestrator.get_performance_monitor()
        assert performance_monitor is not None
        
        # Test that uninitialized access raises error
        uninitialized_orchestrator = ServiceOrchestrator(Settings())
        
        with pytest.raises(RuntimeError, match="not initialized"):
            uninitialized_orchestrator.get_state_manager()
    
    async def test_system_health_check(self, orchestrator):
        """Test system health monitoring"""
        health = await orchestrator.get_system_health()
        
        assert 'status' in health
        assert 'healthy' in health
        assert 'services' in health
        assert 'timestamp' in health
        
        # Should have health info for each service
        assert 'redis' in health['services']
        assert 'performance_monitor' in health['services']
    
    async def test_graceful_shutdown(self, orchestrator):
        """Test graceful shutdown"""
        await orchestrator.shutdown()
        
        assert orchestrator.shutdown_requested is True


# Integration Tests
@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.slow
    async def test_end_to_end_event_processing(self):
        """Test complete event processing pipeline"""
        # This would be a more comprehensive test that exercises
        # the entire system from Slack event to mockup generation
        # Skipped in normal test runs due to external dependencies
        pass
    
    @pytest.mark.slow  
    async def test_performance_under_load(self):
        """Test system performance under load"""
        # This would test concurrent event processing
        # and verify performance characteristics
        pass


if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        # Run quick tests only
        pytest.main([__file__, "-v", "-m", "not slow"])
    else:
        # Run all tests
        pytest.main([__file__, "-v"])