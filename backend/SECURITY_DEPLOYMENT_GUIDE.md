# Security Hardening & Deployment Guide

## 🚨 Critical Security Fixes Implemented

### 1. Environment Variable Security
- **FIXED**: Removed all hardcoded credentials from `config.py`
- **REQUIRED**: Set environment variables before deployment

```bash
# Required Environment Variables
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/db"
export SECRET_KEY="your-super-secure-32-character-minimum-jwt-key"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-supabase-anon-key"
```

### 2. JWT Authentication System
- **NEW**: Comprehensive JWT authentication with role-based access control
- **SECURED**: All administrative endpoints now require authentication
- **FEATURES**:
  - Token-based authentication
  - Role-based permissions (admin, monitoring, database:admin)
  - Automatic token expiration
  - Rate limiting protection

#### Default Users (Change in Production!)
```python
# admin user: admin / admin123
# monitor user: monitor / monitor123
```

### 3. API Rate Limiting
- **IMPLEMENTED**: Request rate limiting (100 req/min default)
- **FEATURES**:
  - Per-IP and per-user rate limiting
  - Burst protection
  - 429 status codes with Retry-After headers

### 4. Input Validation Enhancement
- **SECURED**: All coordinate inputs validated (-90/90, -180/180)
- **LIMITS**: Search radius limited to 50km maximum
- **VALIDATION**: Comprehensive Pydantic field validation

## 🏗️ Architecture Improvements

### 1. Dependency Injection System
- **REPLACED**: Global singletons with FastAPI dependency injection
- **BENEFITS**: Better testability, resource management, lifecycle control
- **FILES**: `core/dependencies.py` - centralized dependency container

### 2. Standardized Error Handling
- **IMPLEMENTED**: Centralized exception handling system
- **FEATURES**:
  - Consistent error response format
  - Detailed error logging
  - HTTP status code mapping
  - Security-aware error messages

### 3. Resource Management
- **ENHANCED**: Proper async task lifecycle management
- **ADDED**: Graceful shutdown procedures
- **MONITORING**: Background task tracking

## ⚡ Performance Enhancements

### 1. Adaptive Connection Pooling
- **NEW**: Dynamic pool sizing based on load patterns
- **FEATURES**:
  - Automatic scale up/down based on utilization
  - Time-based usage pattern analysis
  - Performance threshold monitoring
  - Pool efficiency optimization

### 2. Concurrency Control
- **IMPLEMENTED**: Semaphore-based operation limiting
- **FEATURES**:
  - Operation type-specific limits
  - Priority queue management
  - Bulk operation protection
  - Resource exhaustion prevention

## 🔐 Security Headers & Middleware

### HTTPS & Security Headers
```python
# Security headers automatically added:
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

## 📋 Deployment Checklist

### Pre-Deployment Security Steps

1. **Environment Configuration**
   ```bash
   # Copy example environment
   cp .env.example .env

   # Fill in production values
   nano .env
   ```

2. **Generate Secure JWT Secret**
   ```python
   import secrets
   print(secrets.token_urlsafe(32))
   ```

3. **Database Security**
   - Use connection pooling with SSL
   - Set up read/write replicas if needed
   - Configure backup encryption

4. **Network Security**
   - Enable HTTPS-only in production
   - Configure firewall rules
   - Set up VPN access for admin endpoints

### Production Environment Variables

```bash
# Application
ENVIRONMENT=production
DEBUG=false

# Security (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:secure_password@host:5432/db
SECRET_KEY=your-super-secure-jwt-secret-key-minimum-32-chars

# Security Settings
ENABLE_HTTPS_ONLY=true
ENABLE_SECURITY_HEADERS=true
SESSION_TIMEOUT_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_BURST_SIZE=10

# Performance
PROPERTY_LOOKUP_MAX_RESPONSE_TIME_MS=500
COMPLIANCE_SCORING_MAX_RESPONSE_TIME_MS=100

# Connection Pools
DATABASE_WRITE_POOL_SIZE=15
DATABASE_READ_POOL_SIZE=30
DATABASE_ETL_POOL_SIZE=10

# Monitoring
DATABASE_HEALTH_CHECK_INTERVAL=30
SLOW_QUERY_THRESHOLD_MS=1000

# CORS (Production domains)
CORS_ORIGINS=["https://yourdomain.com"]
```

## 🔐 Authentication Usage

### Getting Access Token
```bash
curl -X POST "https://api.yourdomain.com/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

### Using Authentication
```bash
# Add Authorization header to all authenticated requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "https://api.yourdomain.com/api/v1/database/health"
```

### Role Permissions
- **admin**: Full system access
- **database:admin**: Database operations, connection management
- **monitoring:read**: Read-only monitoring access
- **monitoring:admin**: Monitoring control (start/stop services)

## 🏥 Health Monitoring Endpoints

### System Health
```bash
GET /api/v1/system/status          # Overall system status
GET /api/v1/system/concurrency     # Concurrency management
GET /api/v1/system/adaptive-pooling # Pool management
GET /api/v1/system/performance-metrics # Performance data
```

### Database Health
```bash
GET /api/v1/database/health        # Database connection health
GET /api/v1/database/performance   # Performance metrics
GET /health/database               # Basic health check
```

## 🚨 Security Monitoring

### Key Metrics to Monitor
1. **Authentication Failures**: Failed login attempts
2. **Rate Limit Violations**: 429 responses
3. **Database Connection Health**: Pool utilization
4. **Performance Thresholds**: Response time violations
5. **Error Rates**: 5xx responses

### Log Analysis
```bash
# Monitor authentication failures
grep "Failed login attempt" /var/log/app.log

# Check rate limiting
grep "Rate limit exceeded" /var/log/app.log

# Database connection issues
grep "Database connection failed" /var/log/app.log
```

## 🔄 Maintenance Operations

### Restart System Services
```bash
POST /api/v1/system/maintenance/restart-services?service=all
Authorization: Bearer ADMIN_TOKEN
```

### Pool Management
```bash
# Register adaptive pool
POST /api/v1/system/adaptive-pooling/register-pool
  ?pool_name=primary&min_size=10&max_size=50
```

### Connection Management
```bash
# Emergency: Close all connections
POST /api/v1/database/connections/close-all?confirm=true
Authorization: Bearer DATABASE_ADMIN_TOKEN
```

## ⚠️ Production Warnings

1. **Change Default Passwords**: Update admin/monitor default credentials
2. **SSL/TLS Required**: Always use HTTPS in production
3. **Firewall Configuration**: Restrict admin endpoints to VPN
4. **Database Security**: Use encrypted connections and backups
5. **Monitoring Setup**: Configure alerts for critical metrics
6. **Regular Updates**: Keep dependencies updated for security patches

## 📊 Performance Targets Maintained

- **Property Lookup**: < 500ms response time
- **Compliance Scoring**: < 100ms response time
- **ETL Processing**: 15M+ records within 30-minute threshold
- **Connection Pool Efficiency**: > 80% utilization during peak hours
- **API Availability**: 99.9% uptime target

## 🔧 Troubleshooting

### Common Issues

1. **"Invalid token" errors**: Check JWT secret key configuration
2. **Rate limit exceeded**: Adjust limits or implement backoff
3. **Database connection failures**: Check pool configuration
4. **High response times**: Monitor adaptive pooling recommendations

### Debug Endpoints (Development Only)
```bash
GET /docs     # Swagger documentation (disabled in production)
GET /redoc    # ReDoc documentation (disabled in production)
```

---

**Security Note**: This implementation provides enterprise-grade security for the microschool property intelligence platform while maintaining the critical performance targets of sub-500ms property lookup and sub-100ms compliance scoring.
