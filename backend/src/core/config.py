"""
Application configuration management using Pydantic Settings.
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(
        default="Primer Seek Property API", description="Application name"
    )
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")  # nosec B104
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:Logistimatics123%21@db.goowadpoiciscdcxpwtm.supabase.co:5432/postgres",  # pragma: allowlist secret
        description="Database connection URL",
    )
    database_echo: bool = Field(
        default=False, description="Echo SQL queries to console"
    )
    database_pool_size: int = Field(
        default=10, description="Database connection pool size"
    )
    database_max_overflow: int = Field(
        default=20, description="Database connection pool max overflow"
    )
    database_timeout: int = Field(
        default=30, description="Database query timeout in seconds"
    )

    # Redis settings
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    redis_max_connections: int = Field(
        default=50, description="Redis connection pool size"
    )
    redis_retry_on_timeout: bool = Field(
        default=True, description="Retry Redis operations on timeout"
    )
    redis_health_check_interval: int = Field(
        default=30, description="Redis health check interval in seconds"
    )
    redis_socket_timeout: int = Field(
        default=5, description="Redis socket timeout in seconds"
    )
    redis_socket_connect_timeout: int = Field(
        default=5, description="Redis socket connect timeout in seconds"
    )

    # Redis Cluster settings (for production)
    redis_cluster_nodes: list[str] = Field(
        default=[], description="Redis cluster node URLs for production"
    )
    redis_cluster_enabled: bool = Field(
        default=False, description="Enable Redis cluster mode"
    )
    redis_cluster_skip_full_coverage_check: bool = Field(
        default=False, description="Skip full coverage check in cluster mode"
    )

    # Cache TTL settings for different data types
    cache_ttl_session: int = Field(
        default=1800, description="Session cache TTL in seconds (30 minutes)"
    )
    cache_ttl_compliance_short: int = Field(
        default=300, description="Short compliance cache TTL in seconds (5 minutes)"
    )
    cache_ttl_compliance_long: int = Field(
        default=3600, description="Long compliance cache TTL in seconds (1 hour)"
    )
    cache_ttl_foia_processing: int = Field(
        default=86400, description="FOIA processing cache TTL in seconds (24 hours)"
    )
    cache_ttl_property_lookup: int = Field(
        default=7200, description="Property lookup cache TTL in seconds (2 hours)"
    )
    cache_ttl_tier_classification: int = Field(
        default=21600, description="Tier classification cache TTL in seconds (6 hours)"
    )

    # Cache warming and performance settings
    cache_warming_enabled: bool = Field(
        default=True, description="Enable cache warming strategies"
    )
    cache_warming_batch_size: int = Field(
        default=100, description="Batch size for cache warming operations"
    )
    property_lookup_max_response_time_ms: int = Field(
        default=500, description="Maximum property lookup response time in milliseconds"
    )

    # Authentication settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production", description="JWT secret key"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )

    # Supabase settings
    supabase_url: str | None = Field(
        default="https://goowadpoiciscdcxpwtm.supabase.co",
        description="Supabase project URL",
    )
    supabase_key: str | None = Field(
        default="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdvb3dhZHBvaWNpc2NkY3hwd3RtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4Mzk1NzYsImV4cCI6MjA2OTQxNTU3Nn0.bNWJlbfFqXiQLJc-rvWp1Pn4ycxUvfQBFWmSvyKKnxs",  # pragma: allowlist secret
        description="Supabase anon key",
    )

    # External API settings
    mapbox_access_token: str | None = Field(
        default=None, description="Mapbox access token"
    )

    # Data processing settings
    max_import_batch_size: int = Field(
        default=1000, description="Maximum batch size for data imports"
    )
    import_retry_attempts: int = Field(
        default=3, description="Number of retry attempts for failed imports"
    )
    import_retry_delay: int = Field(
        default=5, description="Delay between retry attempts in seconds"
    )

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="CORS allowed origins",
    )

    @field_validator("environment")  # type: ignore[misc]
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
