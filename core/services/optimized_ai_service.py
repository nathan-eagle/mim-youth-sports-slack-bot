"""
Optimized AI service for MiM Slack Bot
Cost-efficient AI operations with intelligent model selection and caching
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import structlog

import openai
from openai import AsyncOpenAI
from asyncio_throttle import Throttler

from ..config import Settings
from .intelligent_cache import IntelligentCache

logger = structlog.get_logger(__name__)


class ModelSelector:
    """
    Intelligent model selection based on task complexity and cost optimization
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Model capabilities and costs (relative)
        self.model_specs = {
            'gpt-4o-mini': {
                'cost': 1,  # Baseline
                'speed': 10,
                'quality': 7,
                'max_tokens': 128000,
                'best_for': ['intent_analysis', 'simple_classification', 'basic_recommendations']
            },
            'gpt-4o': {
                'cost': 15,
                'speed': 8,
                'quality': 9,
                'max_tokens': 128000,
                'best_for': ['color_analysis', 'complex_reasoning', 'detailed_analysis']
            },
            'gpt-4-turbo': {
                'cost': 30,
                'speed': 6,
                'quality': 10,
                'max_tokens': 128000,
                'best_for': ['complex_analysis', 'creative_tasks', 'premium_quality']
            }
        }
    
    def select_model(self, task_type: str, complexity: str = "auto") -> str:
        """
        Select optimal model for task
        
        Args:
            task_type: Type of AI task
            complexity: Complexity level or "auto" for automatic selection
            
        Returns:
            Model name to use
        """
        if complexity != "auto":
            return self.settings.get_openai_model(complexity)
        
        # Automatic model selection based on task type
        task_model_map = {
            'intent_analysis': 'simple',
            'product_matching': 'simple',
            'color_analysis': 'complex',
            'logo_analysis': 'complex',
            'conversation': 'simple',
            'complex_reasoning': 'complex',
            'premium_quality': 'premium'
        }
        
        complexity_level = task_model_map.get(task_type, 'simple')
        return self.settings.get_openai_model(complexity_level)
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a model"""
        return self.model_specs.get(model, self.model_specs['gpt-4o-mini'])


class PromptOptimizer:
    """
    Optimize prompts for cost and performance
    """
    
    @staticmethod
    def compress_prompt(prompt: str, max_tokens: int = 4000) -> str:
        """
        Compress prompt while maintaining meaning
        
        Args:
            prompt: Original prompt
            max_tokens: Maximum tokens allowed
            
        Returns:
            Compressed prompt
        """
        # Simple compression - remove extra whitespace and unnecessary words
        compressed = ' '.join(prompt.split())
        
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        estimated_tokens = len(compressed) // 4
        
        if estimated_tokens <= max_tokens:
            return compressed
        
        # If too long, truncate intelligently
        # Keep the beginning and end, remove middle
        target_length = max_tokens * 4
        if len(compressed) > target_length:
            start_portion = compressed[:target_length//2]
            end_portion = compressed[-(target_length//2):]
            compressed = f"{start_portion}...[content truncated]...{end_portion}"
        
        return compressed
    
    @staticmethod
    def optimize_for_model(prompt: str, model: str) -> str:
        """
        Optimize prompt for specific model
        
        Args:
            prompt: Original prompt
            model: Target model
            
        Returns:
            Optimized prompt
        """
        # Model-specific optimizations
        if 'mini' in model:
            # For mini models, be more direct and concise
            return PromptOptimizer.compress_prompt(prompt, max_tokens=2000)
        elif 'gpt-4o' in model:
            # For GPT-4o, can be more detailed but still efficient
            return PromptOptimizer.compress_prompt(prompt, max_tokens=6000)
        else:
            # For premium models, full prompt is fine
            return prompt


class OptimizedAIService:
    """
    High-performance AI service with intelligent caching, model selection, and cost optimization
    """
    
    def __init__(self, settings: Settings, cache: IntelligentCache):
        """
        Initialize optimized AI service
        
        Args:
            settings: Application settings
            cache: Intelligent cache instance
        """
        self.settings = settings
        self.cache = cache
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Model selection and optimization
        self.model_selector = ModelSelector(settings)
        self.prompt_optimizer = PromptOptimizer()
        
        # Rate limiting
        self.throttler = Throttler(rate_limit=60, period=60)  # 60 calls per minute
        
        # Performance tracking
        self._total_requests = 0
        self._cache_hits = 0
        self._cost_saved = 0.0
        
        logger.info("Optimized AI service initialized")
    
    async def analyze_user_intent(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze user intent with cost optimization
        
        Args:
            message: User message to analyze
            context: Additional context
            
        Returns:
            Intent analysis result
        """
        # Check cache first
        cache_context = context or {}
        cached_result = await self.cache.get_ai_response(
            prompt=message,
            model="intent_analysis",
            context=cache_context
        )
        
        if cached_result:
            self._cache_hits += 1
            logger.debug("Intent analysis cache hit")
            return cached_result
        
        # Select optimal model
        model = self.model_selector.select_model("intent_analysis")
        
        # Optimize prompt
        system_prompt = """You are an AI assistant analyzing user intent for a youth sports merchandise customization service.

Analyze the user's message and determine:
1. What type of product they want (shirt, hoodie, hat, etc.)
2. Any color preferences mentioned
3. Any specific customization requests
4. The urgency level of their request
5. Whether they're asking for help or ready to order

Respond with a JSON object containing:
- intent_type: "product_request", "color_inquiry", "help_request", "order_ready", "general"
- confidence: "high", "medium", "low"
- extracted_info: {product_type, colors, customization, urgency}
- suggested_next_action: brief description"""
        
        user_prompt = f"User message: {message}"
        if context:
            user_prompt += f"\nContext: {context}"
        
        # Optimize prompts
        system_prompt = self.prompt_optimizer.optimize_for_model(system_prompt, model)
        user_prompt = self.prompt_optimizer.optimize_for_model(user_prompt, model)
        
        # Make API call with rate limiting
        async with self.throttler:
            result = await self._make_ai_request(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                task_type="intent_analysis"
            )
        
        # Cache result
        await self.cache.cache_ai_response(
            prompt=message,
            model="intent_analysis", 
            response=result,
            context=cache_context
        )
        
        return result
    
    async def analyze_logo_colors(
        self, 
        logo_url: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze logo colors with caching
        
        Args:
            logo_url: URL of the logo image
            context: Additional context
            
        Returns:
            Color analysis result
        """
        # Check cache first
        cached_result = await self.cache.get_logo_analysis(logo_url, "colors")
        
        if cached_result:
            self._cache_hits += 1
            logger.debug("Logo color analysis cache hit")
            return cached_result
        
        # Select model for image analysis
        model = self.model_selector.select_model("logo_analysis")
        
        system_prompt = """You are an expert in color analysis for youth sports merchandise.

Analyze the logo image and provide:
1. Primary colors (2-3 main colors)
2. Secondary colors (supporting colors)
3. Color harmony type (complementary, triadic, etc.)
4. Recommended merchandise colors that would work well
5. Colors to avoid that would clash

Respond with JSON:
- primary_colors: ["color1", "color2", ...]
- secondary_colors: ["color1", "color2", ...]
- harmony_type: "complementary|triadic|analogous|monochromatic"
- recommended_merchandise_colors: ["color1", "color2", ...]
- avoid_colors: ["color1", "color2", ...]
- confidence: "high|medium|low"
- reasoning: "brief explanation"""
        
        user_prompt = f"Please analyze the colors in this logo image: {logo_url}"
        if context:
            user_prompt += f"\nAdditional context: {context}"
        
        # Make API call
        async with self.throttler:
            result = await self._make_ai_request(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                task_type="logo_analysis"
            )
        
        # Cache result
        await self.cache.cache_logo_analysis(logo_url, result, "colors")
        
        return result
    
    async def recommend_products(
        self, 
        intent: str,
        user_preferences: Dict[str, Any],
        available_products: List[Dict[str, Any]],
        max_products: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get AI-powered product recommendations
        
        Args:
            intent: User intent/request
            user_preferences: User preferences (colors, style, etc.)
            available_products: List of available products
            max_products: Maximum products to recommend
            
        Returns:
            List of recommended products with reasoning
        """
        # Create cache context
        cache_context = {
            'preferences': user_preferences,
            'available_count': len(available_products),
            'max_products': max_products
        }
        
        # Check cache
        cached_result = await self.cache.get_product_recommendation(intent, cache_context)
        
        if cached_result:
            self._cache_hits += 1
            logger.debug("Product recommendation cache hit")
            return cached_result[:max_products]
        
        # Select model
        model = self.model_selector.select_model("product_matching")
        
        # Build prompt
        products_info = []
        for product in available_products:
            products_info.append({
                'id': product.get('id'),
                'title': product.get('title', ''),
                'category': product.get('category', ''),
                'description': product.get('description', '')[:200]  # Truncate for efficiency
            })
        
        system_prompt = """You are an expert in youth sports merchandise recommendations.

Based on the user's request and preferences, recommend the best products from the available catalog.

Consider:
- User's stated preferences and intent
- Product popularity and quality
- Color compatibility
- Age-appropriate designs
- Value for money

Respond with JSON array of recommendations:
[{
  "product_id": "ID",
  "confidence": "high|medium|low",
  "reasoning": "why this product fits",
  "match_score": 1-10
}]

Sort by match_score (highest first)."""
        
        user_prompt = f"""User request: {intent}
User preferences: {json.dumps(user_preferences)}
Available products: {json.dumps(products_info)}
Recommend up to {max_products} products."""
        
        # Optimize prompts
        system_prompt = self.prompt_optimizer.optimize_for_model(system_prompt, model)
        user_prompt = self.prompt_optimizer.optimize_for_model(user_prompt, model)
        
        # Make API call
        async with self.throttler:
            result = await self._make_ai_request(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                task_type="product_matching"
            )
        
        # Process result
        recommendations = result if isinstance(result, list) else []
        
        # Cache result
        await self.cache.cache_product_recommendation(
            intent, cache_context, recommendations
        )
        
        return recommendations[:max_products]
    
    async def recommend_colors(
        self,
        logo_colors: List[str],
        product_type: str,
        available_colors: List[str],
        max_colors: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Recommend colors based on logo and product type
        
        Args:
            logo_colors: Colors extracted from logo
            product_type: Type of product (shirt, hoodie, etc.)
            available_colors: Available colors for product
            max_colors: Maximum colors to recommend
            
        Returns:
            List of color recommendations with reasoning
        """
        # Create cache key
        cache_context = {
            'logo_colors': logo_colors,
            'product_type': product_type,
            'available_colors': sorted(available_colors)  # Sort for consistent caching
        }
        
        cache_key = f"color_rec:{hash(str(cache_context))}"
        cached_result = await self.cache.get(cache_key)
        
        if cached_result:
            self._cache_hits += 1
            return cached_result[:max_colors]
        
        # Select model
        model = self.model_selector.select_model("color_analysis")
        
        system_prompt = """You are a color expert specializing in youth sports merchandise.

Recommend colors that will:
1. Complement the logo colors
2. Look great on the product type
3. Appeal to youth sports teams
4. Work well for team unity

Consider color theory, sports psychology, and practical considerations.

Respond with JSON array:
[{
  "color": "color_name",
  "reasoning": "why this color works well",
  "harmony_type": "complementary|triadic|analogous|contrast",
  "confidence": "high|medium|low",
  "appeal_score": 1-10
}]

Sort by appeal_score (highest first)."""
        
        user_prompt = f"""Logo colors: {', '.join(logo_colors)}
Product type: {product_type}
Available colors: {', '.join(available_colors)}
Recommend up to {max_colors} colors."""
        
        # Make API call
        async with self.throttler:
            result = await self._make_ai_request(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                task_type="color_analysis"
            )
        
        recommendations = result if isinstance(result, list) else []
        
        # Cache result
        await self.cache.set(cache_key, recommendations, ttl=self.settings.get_cache_ttl("ai_responses"))
        
        return recommendations[:max_colors]
    
    async def _make_ai_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        task_type: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Any:
        """
        Make AI API request with error handling and retries
        
        Args:
            model: Model to use
            messages: Messages for the API
            task_type: Type of task for monitoring
            max_tokens: Maximum tokens to generate
            temperature: Generation temperature
            
        Returns:
            AI response
        """
        self._total_requests += 1
        
        try:
            # Set defaults based on model and task
            if max_tokens is None:
                max_tokens = 1000 if 'mini' in model else 1500
            
            if temperature is None:
                temperature = 0.3  # Consistent results for caching
            
            # Make API call
            start_time = datetime.utcnow()
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Parse response
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: return as text
                result = {"response": content, "error": "json_parse_failed"}
            
            # Log performance
            logger.debug("AI request completed",
                        model=model,
                        task_type=task_type,
                        duration_ms=duration * 1000,
                        tokens_used=response.usage.total_tokens if response.usage else 0)
            
            return result
            
        except Exception as e:
            logger.error("AI request failed",
                        model=model,
                        task_type=task_type,
                        error=str(e))
            
            # Return error result
            return {
                "error": str(e),
                "model": model,
                "task_type": task_type
            }
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get AI service performance statistics"""
        cache_stats = await self.cache.get_cache_stats()
        
        cache_hit_rate = (self._cache_hits / self._total_requests * 100) if self._total_requests > 0 else 0
        
        return {
            "total_ai_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "estimated_cost_saved": self._cost_saved,
            "cache_performance": cache_stats
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check AI service health"""
        try:
            # Test simple API call
            test_response = await self.client.chat.completions.create(
                model=self.settings.get_openai_model("simple"),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {
                "status": "healthy",
                "api_accessible": True,
                "model_available": bool(test_response.choices)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy", 
                "api_accessible": False,
                "error": str(e)
            }