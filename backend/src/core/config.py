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

    # Database settings - Primary (Write) Connection
    database_url: str = Field(
        ...,  # Required field - must be provided via environment variable
        description="Primary database connection URL (write operations)",
    )
    database_echo: bool = Field(
        default=False, description="Echo SQL queries to console"
    )

    # Read Replica Configuration
    database_read_url: str | None = Field(
        default=None,
        description="Read replica database URL for query optimization",
    )
    enable_read_write_splitting: bool = Field(
        default=False,
        description="Enable read/write splitting for performance optimization",
    )

    # Connection Pool Settings - Write Pool (Primary)
    database_write_pool_size: int = Field(
        default=15, description="Write database connection pool size for FOIA ingestion"
    )
    database_write_max_overflow: int = Field(
        default=25, description="Write database connection pool max overflow"
    )

    # Connection Pool Settings - Read Pool (Replicas)
    database_read_pool_size: int = Field(
        default=30,
        description="Read database connection pool size for property lookups",
    )
    database_read_max_overflow: int = Field(
        default=50, description="Read database connection pool max overflow"
    )

    # ETL and Bulk Operations Pool
    database_etl_pool_size: int = Field(
        default=10, description="ETL connection pool size for 15M+ record processing"
    )
    database_etl_max_overflow: int = Field(
        default=15, description="ETL connection pool max overflow"
    )

    # Connection Management
    database_timeout: int = Field(
        default=30, description="Database query timeout in seconds"
    )
    database_pool_recycle: int = Field(
        default=3600, description="Connection pool recycle time in seconds"
    )
    database_pool_pre_ping: bool = Field(
        default=True, description="Verify connections before use"
    )
    database_pool_reset_on_return: str = Field(
        default="commit", description="Pool reset behavior (commit, rollback, none)"
    )

    # Performance Thresholds
    property_lookup_max_response_time_ms: int = Field(
        default=500, description="Maximum property lookup response time in milliseconds"
    )
    compliance_scoring_max_response_time_ms: int = Field(
        default=100,
        description="Maximum compliance scoring response time in milliseconds",
    )
    etl_batch_processing_timeout_minutes: int = Field(
        default=30, description="Maximum ETL batch processing timeout in minutes"
    )

    # Health Monitoring
    database_health_check_interval: int = Field(
        default=30, description="Database health check interval in seconds"
    )
    slow_query_threshold_ms: int = Field(
        default=1000, description="Slow query threshold in milliseconds"
    )
    connection_pool_warning_threshold: float = Field(
        default=0.8, description="Connection pool usage warning threshold (0.0-1.0)"
    )

    # Failover Configuration
    enable_connection_failover: bool = Field(
        default=True, description="Enable automatic connection failover"
    )
    failover_retry_attempts: int = Field(
        default=3, description="Number of failover retry attempts"
    )
    failover_retry_delay: int = Field(
        default=5, description="Delay between failover retries in seconds"
    )
    circuit_breaker_failure_threshold: int = Field(
        default=5, description="Circuit breaker failure threshold"
    )
    circuit_breaker_timeout: int = Field(
        default=60, description="Circuit breaker timeout in seconds"
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
        ...,  # Required field - must be provided via environment variable
        description="JWT secret key",
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )

    # Supabase settings
    supabase_url: str | None = Field(
        default=None,
        description="Supabase project URL",
    )
    supabase_key: str | None = Field(
        default=None,
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

    # Rate limiting settings
    rate_limit_requests_per_minute: int = Field(
        default=100, description="API rate limit requests per minute"
    )
    rate_limit_burst_size: int = Field(
        default=20, description="Rate limit burst size"
    )

    # Security settings
    enable_https_only: bool = Field(
        default=True, description="Enforce HTTPS-only connections"
    )
    enable_security_headers: bool = Field(
        default=True, description="Enable security headers"
    )
    session_timeout_minutes: int = Field(
        default=60, description="Session timeout in minutes"
    )

    @field_validator("environment")  # type: ignore[misc]
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v

    @field_validator("secret_key")  # type: ignore[misc]
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate JWT secret key strength."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v

    @field_validator("database_url")  # type: ignore[misc]
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v.startswith("postgresql"):
            raise ValueError("Database URL must be a PostgreSQL connection string")
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
