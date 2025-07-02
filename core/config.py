"""
Configuration management for MiM Slack Bot
Centralized settings with environment variable support
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """
    Application settings with validation and type safety
    
    All settings can be overridden via environment variables
    with the prefix 'MIM_' (e.g., MIM_REDIS_URL)
    """
    
    # Application settings
    app_name: str = Field(default="MiM Youth Sports Swag Bot", env="MIM_APP_NAME")
    app_version: str = Field(default="2.0.0", env="MIM_APP_VERSION")
    debug_mode: bool = Field(default=False, env="MIM_DEBUG_MODE")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Slack API settings
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    
    # OpenAI API settings
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model_simple: str = Field(default="gpt-4o-mini", env="MIM_OPENAI_MODEL_SIMPLE")
    openai_model_complex: str = Field(default="gpt-4o", env="MIM_OPENAI_MODEL_COMPLEX")
    openai_model_premium: str = Field(default="gpt-4-turbo", env="MIM_OPENAI_MODEL_PREMIUM")
    openai_max_tokens: int = Field(default=1000, env="MIM_OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.3, env="MIM_OPENAI_TEMPERATURE")
    
    # Printify API settings
    printify_api_token: str = Field(..., env="PRINTIFY_API_TOKEN")
    printify_base_url: str = Field(default="https://api.printify.com/v1", env="MIM_PRINTIFY_BASE_URL")
    printify_rate_limit: int = Field(default=50, env="MIM_PRINTIFY_RATE_LIMIT")  # calls per minute
    
    # Stripe settings
    stripe_publishable_key: str = Field(..., env="STRIPE_PUBLISHABLE_KEY")
    stripe_secret_key: str = Field(..., env="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(..., env="STRIPE_WEBHOOK_SECRET")
    
    # Database settings
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_anon_key: str = Field(..., env="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    database_pool_size: int = Field(default=10, env="MIM_DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="MIM_DATABASE_MAX_OVERFLOW")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_max_connections: int = Field(default=20, env="MIM_REDIS_MAX_CONNECTIONS")
    redis_socket_timeout: int = Field(default=5, env="MIM_REDIS_SOCKET_TIMEOUT")
    
    # Performance settings
    async_worker_count: int = Field(default=4, env="MIM_ASYNC_WORKER_COUNT")
    max_concurrent_requests: int = Field(default=100, env="MIM_MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, env="MIM_REQUEST_TIMEOUT")
    
    # Cache settings
    cache_ttl_default: int = Field(default=3600, env="MIM_CACHE_TTL_DEFAULT")  # 1 hour
    cache_ttl_ai_responses: int = Field(default=86400, env="MIM_CACHE_TTL_AI_RESPONSES")  # 24 hours
    cache_ttl_product_data: int = Field(default=7200, env="MIM_CACHE_TTL_PRODUCT_DATA")  # 2 hours
    cache_ttl_logo_analysis: int = Field(default=604800, env="MIM_CACHE_TTL_LOGO_ANALYSIS")  # 1 week
    
    # Business logic settings
    max_products_per_request: int = Field(default=6, env="MIM_MAX_PRODUCTS_PER_REQUEST")
    default_product_ids: List[int] = Field(default=[12, 92, 6], env="MIM_DEFAULT_PRODUCT_IDS")
    mockup_generation_timeout: int = Field(default=30, env="MIM_MOCKUP_GENERATION_TIMEOUT")
    conversation_cleanup_hours: int = Field(default=24, env="MIM_CONVERSATION_CLEANUP_HOURS")
    
    # Monitoring settings
    enable_metrics: bool = Field(default=True, env="MIM_ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="MIM_METRICS_PORT")
    enable_health_checks: bool = Field(default=True, env="MIM_ENABLE_HEALTH_CHECKS")
    
    # File processing settings
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MIM_MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        env="MIM_ALLOWED_FILE_TYPES"
    )
    temp_file_cleanup_hours: int = Field(default=2, env="MIM_TEMP_FILE_CLEANUP_HOURS")
    
    @validator('default_product_ids', pre=True)
    def parse_product_ids(cls, v):
        """Parse product IDs from environment variable"""
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(',') if x.strip().isdigit()]
        return v
    
    @validator('allowed_file_types', pre=True)
    def parse_file_types(cls, v):
        """Parse file types from environment variable"""
        if isinstance(v, str):
            return [x.strip() for x in v.split(',') if x.strip()]
        return v
    
    class Config:
        env_prefix = "MIM_"
        case_sensitive = False
        
    def get_openai_model(self, complexity: str = "simple") -> str:
        """
        Get appropriate OpenAI model based on task complexity
        
        Args:
            complexity: "simple", "complex", or "premium"
            
        Returns:
            Model name for the specified complexity level
        """
        models = {
            "simple": self.openai_model_simple,
            "complex": self.openai_model_complex,
            "premium": self.openai_model_premium
        }
        return models.get(complexity, self.openai_model_simple)
    
    def get_cache_ttl(self, cache_type: str = "default") -> int:
        """
        Get cache TTL for specific data type
        
        Args:
            cache_type: Type of data being cached
            
        Returns:
            TTL in seconds
        """
        ttl_map = {
            "default": self.cache_ttl_default,
            "ai_responses": self.cache_ttl_ai_responses,
            "product_data": self.cache_ttl_product_data,
            "logo_analysis": self.cache_ttl_logo_analysis
        }
        return ttl_map.get(cache_type, self.cache_ttl_default)


# Global settings instance
settings = Settings()


class ProductCatalogConfig:
    """
    Configuration for product catalog management
    Supports dynamic product selection and AI-driven recommendations
    """
    
    def __init__(self):
        self.catalog_version = "3.0-optimized"
        self.selection_strategies = {
            "ai_only": self._ai_only_selection,
            "popularity_based": self._popularity_based_selection,
            "ai_hybrid": self._ai_hybrid_selection
        }
        
        # Product category mappings for AI
        self.category_keywords = {
            "apparel": {
                "keywords": ["shirt", "hoodie", "jersey", "clothing", "wear", "tee", "sweatshirt"],
                "priority": "high",
                "processing_time": "fast"
            },
            "accessories": {
                "keywords": ["hat", "cap", "bag", "bottle", "accessory"],
                "priority": "medium",
                "processing_time": "medium"
            },
            "custom": {
                "keywords": ["custom", "personalized", "unique", "special"],
                "priority": "low", 
                "processing_time": "slow"
            }
        }
        
        # AI model selection for different tasks
        self.ai_task_models = {
            "intent_analysis": "simple",
            "color_analysis": "complex",
            "product_matching": "simple",
            "complex_recommendations": "complex"
        }
    
    def get_strategy(self, strategy_name: str = "ai_hybrid"):
        """Get product selection strategy function"""
        return self.selection_strategies.get(strategy_name, self._ai_hybrid_selection)
    
    def _ai_only_selection(self, context: Dict[str, Any]) -> List[int]:
        """Pure AI-based product selection"""
        # Implementation will be in product service
        pass
    
    def _popularity_based_selection(self, context: Dict[str, Any]) -> List[int]:
        """Popularity-based product selection with AI enhancement"""
        # Implementation will be in product service
        pass
    
    def _ai_hybrid_selection(self, context: Dict[str, Any]) -> List[int]:
        """Hybrid AI + popularity product selection (default)"""
        # Implementation will be in product service
        pass


# Global product config instance
product_config = ProductCatalogConfig()