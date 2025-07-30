# Database Connection Management System

## Overview

This document describes the comprehensive database connection management system implemented for the Microschool Property Intelligence Platform. The system is designed to handle large-scale property data processing (15M+ records) while maintaining strict performance requirements for compliance-critical operations.

## Key Performance Requirements

- **Property Lookup**: Sub-500ms response time
- **Compliance Scoring**: Sub-100ms response time
- **ETL Processing**: 15M+ records within 30 minutes
- **Zero-tolerance Availability**: Automatic failover for compliance operations

## Architecture Components

### 1. Connection Manager (`database_manager.py`)

The core connection management system provides:

#### Connection Pooling Strategy
- **Write Pool**: Optimized for FOIA data ingestion (15 connections, 25 max overflow)
- **Read Pool**: Optimized for property lookups (30 connections, 50 max overflow)
- **ETL Pool**: Optimized for bulk operations (10 connections, 15 max overflow)

#### Read/Write Splitting
```python
# Automatic routing based on query type
async with connection_manager.get_session(QueryType.READ) as session:
    # Routes to read replica or optimized read pool

async with connection_manager.get_session(QueryType.WRITE) as session:
    # Routes to primary database with write optimization

async with connection_manager.get_session(QueryType.ETL) as session:
    # Routes to ETL pool with extended timeouts and memory settings
```

#### Circuit Breaker Pattern
- Automatic failure detection and circuit breaker activation
- Configurable failure thresholds and timeout periods
- Graceful degradation with intelligent retry logic

### 2. Database Monitoring (`database_monitoring.py`)

Real-time monitoring and alerting system:

#### Performance Metrics
- Response time tracking with millisecond precision
- Connection pool usage monitoring
- Query count and error rate analysis
- Compliance-specific performance tracking

#### Alert Management
```python
# Alert levels and thresholds
AlertLevel.CRITICAL  # Property lookup > 500ms, compliance issues
AlertLevel.WARNING   # Pool usage > 80%, slow queries
AlertLevel.INFO      # General performance notifications
```

#### Health Checks
- Continuous monitoring every 30 seconds
- Database connectivity verification
- PostGIS extension availability
- Performance threshold validation

### 3. Specialized Database Services (`database_services.py`)

#### PropertyLookupService
- Sub-500ms geospatial property searches
- Intelligent Redis caching with configurable TTL
- Spatial indexing optimization
- Bulk lookup operations

```python
# Example usage
properties = await property_lookup_service.find_properties_by_location(
    latitude=30.2672,
    longitude=-97.7431,
    radius_meters=1000,
    limit=100
)
```

#### ComplianceScoringService
- Sub-100ms compliance score calculations
- Real-time microschool suitability assessment
- Cached scoring with short TTL for accuracy
- Bulk scoring operations

```python
# Example usage
result = await compliance_scoring_service.calculate_compliance_score(property_id)
# Returns: compliance_score, response_time_ms, detailed breakdown
```

#### FOIADataIngestionService
- High-throughput write operations
- PostgreSQL UPSERT optimization
- Batch processing with configurable sizes
- Automatic cache invalidation

#### ETLPipelineService
- 15M+ record processing capability
- Progress tracking and status monitoring
- Optimized for large-scale data transformations
- Recovery and error handling

## Configuration

### Environment Variables

```bash
# Primary Database Connection
DATABASE_URL=postgresql+asyncpg://user:password@host:port/db  # pragma: allowlist secret

# Read Replica (optional)
DATABASE_READ_URL=postgresql+asyncpg://user:password@read-host:port/db  # pragma: allowlist secret
ENABLE_READ_WRITE_SPLITTING=true

# Connection Pool Sizes
DATABASE_WRITE_POOL_SIZE=15
DATABASE_WRITE_MAX_OVERFLOW=25
DATABASE_READ_POOL_SIZE=30
DATABASE_READ_MAX_OVERFLOW=50
DATABASE_ETL_POOL_SIZE=10
DATABASE_ETL_MAX_OVERFLOW=15

# Performance Thresholds
PROPERTY_LOOKUP_MAX_RESPONSE_TIME_MS=500
COMPLIANCE_SCORING_MAX_RESPONSE_TIME_MS=100
SLOW_QUERY_THRESHOLD_MS=1000

# Health Monitoring
DATABASE_HEALTH_CHECK_INTERVAL=30
CONNECTION_POOL_WARNING_THRESHOLD=0.8

# Failover Configuration
ENABLE_CONNECTION_FAILOVER=true
FAILOVER_RETRY_ATTEMPTS=3
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60
```

## API Endpoints

### Health Monitoring
- `GET /health/database` - Comprehensive database health check
- `GET /health/performance` - Performance metrics and compliance report
- `GET /health/alerts` - Active alerts and warnings

### Property Operations
- `POST /api/v1/database/property/lookup` - High-performance property search
- `GET /api/v1/database/property/{id}` - Property details with compliance data
- `POST /api/v1/database/property/bulk-lookup` - Bulk property searches

### Compliance Operations
- `POST /api/v1/database/compliance/score` - Real-time compliance scoring
- `POST /api/v1/database/compliance/bulk-score` - Bulk compliance scoring

### Data Ingestion
- `POST /api/v1/database/foia/ingest` - FOIA data ingestion
- `POST /api/v1/database/etl/start` - Start ETL pipeline
- `GET /api/v1/database/etl/status/{pipeline_id}` - ETL progress tracking

### Performance Testing
- `GET /api/v1/database/test/property-lookup-performance` - Automated performance testing
- `GET /api/v1/database/test/compliance-scoring-performance` - Compliance performance testing

## Performance Optimization Features

### 1. Intelligent Caching
- Redis integration with tiered TTL strategies
- Property lookup cache: 2 hours
- Compliance score cache: 5 minutes (short for accuracy)
- Session cache: 30 minutes

### 2. Query Optimization
- PostGIS spatial indexing for geospatial queries
- Materialized views for frequently accessed data
- Connection-specific PostgreSQL settings optimization
- Prepared statement caching

### 3. Connection Lifecycle Management
- Pre-ping verification before query execution
- Automatic connection recycling (1 hour default)
- Pool reset behavior configuration
- Graceful connection cleanup

### 4. Monitoring and Alerting
- Real-time performance metrics collection
- Threshold-based alerting system
- Historical performance tracking
- Automated recommendations generation

## Failover and High Availability

### 1. Circuit Breaker Implementation
```python
# Automatic circuit breaker states
CircuitBreakerState.CLOSED   # Normal operation
CircuitBreakerState.OPEN     # Failed state, requests blocked
CircuitBreakerState.HALF_OPEN # Testing recovery
```

### 2. Automatic Failover
- Configurable retry attempts with exponential backoff
- Automatic detection of connection failures
- Graceful degradation for non-critical operations
- Health check restoration verification

### 3. Zero-Downtime Operations
- Connection pool management during maintenance
- Rolling connection refresh
- Background health monitoring
- Proactive connection replacement

## Usage Examples

### FastAPI Dependency Injection
```python
from backend.src.core.database_manager import get_read_session, get_write_session

@app.get("/properties/search")
async def search_properties(
    lat: float,
    lng: float,
    session: AsyncSession = Depends(get_read_session)
):
    # Automatic read optimization
    pass

@app.post("/properties/update")
async def update_property(
    data: PropertyUpdate,
    session: AsyncSession = Depends(get_write_session)
):
    # Automatic write optimization
    pass
```

### Direct Service Usage
```python
from backend.src.services.database_services import property_lookup_service

# High-performance property search
properties = await property_lookup_service.find_properties_by_location(
    latitude=30.2672,
    longitude=-97.7431,
    radius_meters=1000
)
```

### Monitoring Integration
```python
from backend.src.core.database_monitoring import database_monitor

# Get current performance metrics
metrics = await database_monitor.get_current_metrics()

# Get performance report
report = await database_monitor.get_performance_report()
```

## Best Practices

### 1. Query Type Classification
Always specify the appropriate query type for optimal routing:
- `QueryType.READ` - Property lookups, compliance queries
- `QueryType.WRITE` - Data ingestion, updates
- `QueryType.ETL` - Bulk operations, migrations
- `QueryType.COMPLIANCE` - Time-critical compliance scoring

### 2. Connection Management
- Use context managers for automatic cleanup
- Specify query types for intelligent routing
- Monitor connection pool usage regularly
- Configure appropriate timeouts

### 3. Performance Monitoring
- Implement comprehensive logging
- Set up alerting for threshold breaches
- Regular performance testing
- Monitor cache hit rates

### 4. Error Handling
- Implement retry logic with exponential backoff
- Use circuit breakers for graceful degradation
- Log performance warnings and errors
- Provide meaningful error messages

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
   - Monitor pool usage via `/health/database`
   - Increase pool sizes if consistently above 80%
   - Check for connection leaks in application code

2. **Slow Query Performance**
   - Review slow query logs in monitoring
   - Verify spatial indexes are being used
   - Check cache hit rates
   - Consider read replica scaling

3. **Circuit Breaker Activation**
   - Check database connectivity
   - Review error logs for root cause
   - Verify network stability
   - Adjust failure thresholds if needed

4. **Cache Performance Issues**
   - Monitor Redis connectivity
   - Check cache hit rates
   - Review TTL configurations
   - Verify cache invalidation logic

### Performance Tuning

1. **Pool Size Optimization**
   - Monitor concurrent connection usage
   - Adjust pool sizes based on workload patterns
   - Consider separate pools for different operations

2. **Timeout Configuration**
   - Set appropriate query timeouts
   - Configure connection timeouts
   - Adjust circuit breaker timeouts

3. **Caching Strategy**
   - Tune TTL values based on data freshness requirements
   - Implement cache warming for critical data
   - Monitor cache memory usage

## Maintenance and Operations

### Regular Maintenance Tasks
- Monitor connection pool metrics
- Review slow query performance
- Update performance thresholds
- Test failover procedures
- Validate backup/recovery processes

### Scaling Considerations
- Add read replicas for read-heavy workloads
- Implement connection pooling at application level
- Consider database sharding for very large datasets
- Monitor and optimize query performance regularly

## Security Considerations

- Connection strings stored in environment variables
- SSL/TLS encryption for all database connections
- Connection timeout configurations prevent resource exhaustion
- Audit logging for all database operations
- Secure credential management practices
