# Redis Caching Infrastructure for Microschool Property Intelligence Platform

## Overview

This document describes the comprehensive Redis caching infrastructure implemented for the Primer Seek Property microschool intelligence platform. The system is designed to support high-performance property data analysis, compliance scoring, and FOIA data processing with sub-500ms response times for critical operations.

## Architecture Components

### 1. Core Redis Configuration (`/backend/src/core/redis.py`)

**Enhanced Features:**
- **Production Redis Cluster Support**: Automatic cluster detection and failover
- **Performance Monitoring**: Built-in response time tracking and alerting
- **Connection Management**: Advanced pooling with health checks and retry logic
- **Error Handling**: Comprehensive error logging and graceful degradation

**Key Capabilities:**
- Multi-instance Redis support (single instance for dev, cluster for production)
- Connection pooling with configurable limits (default: 50 connections)
- Automatic retries on timeout with exponential backoff
- Health monitoring with 30-second check intervals

### 2. Specialized Cache Services (`/backend/src/services/cache_services.py`)

#### ComplianceCacheService
**Purpose**: Cache compliance scoring and tier classification data with intelligent TTL management.

**Features:**
- **Dual TTL Strategy**: Short TTL (5 min) for dynamic data, long TTL (1 hour) for stable metrics
- **Batch Operations**: Efficient bulk compliance score retrieval
- **Intelligent Invalidation**: Property-specific cache invalidation
- **Performance Tracking**: Sub-100ms compliance scoring target

**Key Methods:**
```python
await compliance_cache.get_compliance_score(property_id, compliance_type)
await compliance_cache.set_compliance_score(property_id, compliance_type, data, use_long_ttl=True)
await compliance_cache.batch_get_compliance_scores(property_ids, compliance_type)
```

#### SessionCacheService
**Purpose**: Manage user session data with role-based access control.

**Features:**
- **Sliding Expiration**: Session TTL extends on access (30 minutes default)
- **Role Caching**: Separate role data caching for authorization
- **Security**: Automatic session invalidation on role changes
- **Monitoring**: Session access pattern tracking

**Key Methods:**
```python
await session_cache.get_session(session_id)
await session_cache.set_session(session_id, session_data)
await session_cache.get_user_roles(user_id)
```

#### FOIACacheService
**Purpose**: Cache FOIA data processing results and column mapping operations.

**Features:**
- **File-based Caching**: Hash-based keys using file metadata
- **Column Mapping Cache**: Intelligent mapping result storage
- **Long TTL**: 24-hour cache for expensive processing operations
- **Content Integrity**: MD5 hashing for cache invalidation triggers

**Key Methods:**
```python
await foia_cache.get_processing_result(file_path, operation, metadata)
await foia_cache.get_column_mapping(source_columns, target_schema)
```

#### PropertyLookupCacheService
**Purpose**: Achieve sub-500ms property lookup performance for interactive mapping.

**Features:**
- **Address-based Caching**: Normalized address key generation
- **Coordinate-based Caching**: Spatial proximity caching with configurable radius
- **Performance Monitoring**: Response time tracking with alerts
- **Batch Operations**: Efficient multi-property lookups

**Key Methods:**
```python
await property_lookup_cache.get_property_by_address(address, city, state)
await property_lookup_cache.get_properties_by_coordinates(lat, lon, radius_m)
await property_lookup_cache.batch_get_properties(addresses)
```

### 3. Cache Invalidation System (`/backend/src/services/cache_invalidation.py`)

**Purpose**: Intelligent automation of cache invalidation to maintain data consistency.

**Features:**
- **Event-driven Invalidation**: Automated triggers for data updates
- **Bulk Operations**: Efficient multi-property invalidation
- **Audit Logging**: Complete invalidation history and statistics
- **Smart Cleanup**: Scheduled cleanup of expired entries

**Invalidation Triggers:**
- `COMPLIANCE_DATA_UPDATE`: Property compliance data changes
- `PROPERTY_DATA_UPDATE`: Core property information changes
- `FOIA_DATA_IMPORT`: New FOIA data processing
- `USER_ROLE_CHANGE`: User permission modifications
- `SCHEDULED_CLEANUP`: Automated maintenance operations

**Key Methods:**
```python
await cache_invalidation.invalidate_property_compliance(property_id)
await cache_invalidation.bulk_invalidate_properties(property_ids)
await cache_invalidation.scheduled_cleanup(max_age_hours=24)
```

### 4. Performance Monitoring (`/backend/src/services/redis_monitoring.py`)

**Purpose**: Comprehensive performance monitoring and alerting system.

**Features:**
- **Real-time Metrics**: Hit rates, response times, error rates
- **Performance Alerts**: Configurable thresholds with severity levels
- **Historical Tracking**: Performance trends and analysis
- **Health Checks**: System-wide Redis health monitoring

**Monitoring Metrics:**
- **Hit Rate**: Target >80% for optimal performance
- **Response Time**: <500ms for property lookups, <100ms for compliance
- **Memory Usage**: Configurable limits with alerts
- **Error Rate**: <5% maximum acceptable error rate

**Alert Severities:**
- **Low**: Minor performance degradation
- **Medium**: Threshold violations, manual intervention recommended
- **High**: Significant performance impact
- **Critical**: System reliability at risk

### 5. Cache Warming Service (`/backend/src/services/cache_invalidation.py`)

**Purpose**: Proactive cache warming for frequently accessed data.

**Features:**
- **Compliance Cache Warming**: Pre-load compliance scores for active properties
- **Property Lookup Warming**: Pre-cache high-frequency address searches
- **Batch Processing**: Configurable batch sizes to avoid system overload
- **Smart Skipping**: Avoid overwriting existing valid cache entries

## API Endpoints (`/backend/src/api/cache_monitoring.py`)

### Health and Monitoring
- `GET /api/v1/cache/health` - Comprehensive Redis health check
- `GET /api/v1/cache/metrics` - Current performance metrics
- `GET /api/v1/cache/metrics/history` - Historical performance data
- `GET /api/v1/cache/alerts` - Recent performance alerts

### Cache Management
- `POST /api/v1/cache/invalidate/property/{id}` - Invalidate property cache
- `POST /api/v1/cache/invalidate/bulk` - Bulk property invalidation
- `POST /api/v1/cache/invalidate/pattern` - Pattern-based invalidation
- `POST /api/v1/cache/warm/compliance` - Pre-warm compliance cache

### Maintenance
- `POST /api/v1/cache/cleanup` - Scheduled cache cleanup
- `GET /api/v1/cache/info` - Configuration and status information

## Configuration

### Environment Variables (`.env.example`)

**Redis Connection:**
```bash
# Single Instance (Development)
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Cluster Configuration (Production)
REDIS_CLUSTER_ENABLED=true
REDIS_CLUSTER_NODES=["redis://node1:6379", "redis://node2:6379", "redis://node3:6379"]
```

**Cache TTL Settings:**
```bash
CACHE_TTL_SESSION=1800                    # 30 minutes
CACHE_TTL_COMPLIANCE_SHORT=300           # 5 minutes
CACHE_TTL_COMPLIANCE_LONG=3600           # 1 hour
CACHE_TTL_FOIA_PROCESSING=86400          # 24 hours
CACHE_TTL_PROPERTY_LOOKUP=7200           # 2 hours
CACHE_TTL_TIER_CLASSIFICATION=21600      # 6 hours
```

**Performance Thresholds:**
```bash
PROPERTY_LOOKUP_MAX_RESPONSE_TIME_MS=500
CACHE_WARMING_ENABLED=true
CACHE_WARMING_BATCH_SIZE=100
```

## Production Deployment

### Redis Cluster Setup

**Recommended Architecture:**
- **3 Master Nodes**: For high availability and data distribution
- **3 Replica Nodes**: One replica per master for failover
- **Redis Sentinel**: Automatic failover management
- **Memory Policy**: `allkeys-lru` for automatic eviction
- **Persistence**: RDB snapshots + AOF for data durability

**Network Configuration:**
```bash
# Master Nodes
redis-master-1.internal:6379
redis-master-2.internal:6379
redis-master-3.internal:6379

# Replica Nodes
redis-replica-1.internal:6379
redis-replica-2.internal:6379
redis-replica-3.internal:6379
```

### Monitoring and Alerting

**Key Metrics to Monitor:**
1. **Cache Hit Rate**: Should maintain >80% for optimal performance
2. **Response Time**: Property lookups <500ms, compliance <100ms
3. **Memory Usage**: Monitor for memory pressure and evictions
4. **Connection Count**: Ensure pool limits are appropriate
5. **Error Rate**: Should remain <5% under normal operations

**Alert Thresholds:**
- **Response Time > 500ms**: Medium severity
- **Hit Rate < 80%**: Medium severity
- **Memory Usage > 80%**: High severity
- **Error Rate > 5%**: Critical severity

### Performance Optimization

**Cache Key Design:**
- **Hierarchical Keys**: `service:type:identifier` pattern
- **Consistent Hashing**: Even distribution across cluster nodes
- **Expiration Strategy**: Appropriate TTL for data freshness requirements

**Memory Optimization:**
- **Data Compression**: JSON serialization with compression for large objects
- **Key Prefixing**: Consistent naming for efficient pattern matching
- **TTL Management**: Automatic cleanup of expired entries

## Integration with Microschool Compliance

### Compliance Workflow Optimization

1. **Initial Property Assessment**:
   - Cache zoning compliance (long TTL - stable data)
   - Cache safety compliance (short TTL - may change)
   - Cache accessibility compliance (medium TTL)

2. **FOIA Data Processing**:
   - Cache column mapping results (24-hour TTL)
   - Cache processed data extracts
   - Invalidate on new FOIA imports

3. **Interactive Property Search**:
   - Sub-500ms property lookup requirement
   - Batch property retrieval for map views
   - Coordinate-based spatial caching

### Data Consistency Strategy

**Cache-Aside Pattern**: Application manages cache population and invalidation
**Write-Through Updates**: Critical compliance data immediately invalidates cache
**Eventual Consistency**: Non-critical data allows brief staleness for performance

## Monitoring and Maintenance

### Daily Operations

1. **Health Checks**: Automated monitoring via `/health/redis` endpoint
2. **Performance Review**: Check metrics dashboard for trends
3. **Alert Response**: Address performance alerts promptly
4. **Cache Warming**: Pre-warm cache for peak usage periods

### Weekly Maintenance

1. **Performance Analysis**: Review hit rates and response times
2. **Memory Usage**: Monitor for memory pressure and optimization opportunities
3. **Error Review**: Investigate recurring errors or timeouts
4. **Configuration Tuning**: Adjust TTL values based on usage patterns

### Disaster Recovery

**Backup Strategy**:
- RDB snapshots every 6 hours
- AOF replication for point-in-time recovery
- Cross-region replica for disaster recovery

**Failover Procedures**:
- Automatic failover via Redis Sentinel
- Application-level circuit breakers for cache failures
- Graceful degradation to database-only mode

## Security Considerations

**Network Security**:
- Private network deployment
- Redis AUTH password protection
- TLS encryption for sensitive environments

**Access Control**:
- Application-level authentication only
- No direct Redis access for users
- Audit logging for cache operations

**Data Protection**:
- No sensitive PII in cache keys
- Configurable data retention periods
- Secure disposal of cached credentials

---

## Performance Benchmarks

**Target Performance Metrics:**
- **Property Lookup**: <500ms (95th percentile)
- **Compliance Scoring**: <100ms (average)
- **Cache Hit Rate**: >80% (overall)
- **FOIA Processing**: 24-hour cache retention
- **Session Management**: 30-minute sliding expiration

**Scalability Targets:**
- **15M+ Properties**: Support for full Regrid dataset (TX/AL/FL)
- **1000+ Concurrent Users**: Session and lookup performance
- **100K+ Daily Compliance Checks**: Efficient caching and invalidation
- **Zero Data Loss Tolerance**: For compliance accuracy requirements
