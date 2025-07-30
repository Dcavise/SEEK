# Primer Seek Property - Product Requirements Document

## Executive Summary

The Primer Seek Property sourcing system is a comprehensive platform designed to import, normalize, and visualize property data from all cities in Texas, Alabama, and Florida. The system enables the Primer Real Estate function to efficiently analyze potential property lease opportunities, understand compliance related to a given property and identify leads to engage with via a interactive mapping interface.

---

## 1. Project Objectives and Goals

### 1.1 Primary Objectives
- **Data Consolidation**: Aggregate property data from several hundred county CSV files into a unified, searchable database.
- **Performance Optimization**: Achieve high-speed data processing (10-50x faster than traditional methods) using DuckDB
- **User Experience**: Provide intuitive property visualization and analysis tools for the Primer Real Estate team.
- **Scalability**: Build a system capable of handling millions of property records with real-time performance

### 1.2 Business Goals
- **Market Access**: Enable rapid identification of qualified properties for potential Primer campuses across Alabama, Texas, and Florida.
- **Workflow Efficiency**: Reduce property research time from hours to minutes.
- **Data Quality**: Provide normalized, accurate property information with 95%+ accuracy
- **Competitive Advantage**: Deliver comprehensive market intelligence not available elsewhere

### 1.3 Technical Goals
- **High Performance**: Sub-2-second map rendering for any city.
- **Data Integrity**: Implement robust validation and normalization processes
- **Maintainability**: Follow clean code principles for long-term sustainability
- **Extensibility**: Design architecture for future expansion to other states

---

## 2. Target Users and Use Cases

### 2.1 Primary Users

#### Primer Real Estate Team
**Profile**: Startup employees at Primer trying to find potential asset-light real estate for Primer to lease

**Needs**:
- Identify zoned by right properties in target expansion markets.
- Analyze occupancy and fire sprinkler data to gather insight about building compliance.
- Push high signal properties to an external CRM for engagement.

### 2.2 Core Use Cases

#### UC-001: City Property Discovery
**Actor**: Primer Real Estate team members  
**Goal**: Find all properties zoned by right in a specific Texas city  
**Flow**:
1. User searches for city name (e.g., "Austin")
2. System displays autocomplete suggestions with property counts
3. User selects city and views interactive map
4. System renders properties with status indicators
5. User analyzes distribution and identifies opportunities via filters.

#### UC-002: Property Status Management
**Actor**: Real Estate Team Member  
**Goal**: Track property sourcing and acquisition pipeline  
**Flow**:
1. User identifies properties of interest
2. System allows status updates (unreviewed, reviewed, synced, unqualified)
3. User filters properties by status
4. System maintains audit trail of status changes
5. User monitors pipeline progress

---

## 3. Core Features and Functionality

### 3.1 Data Import and Processing Engine

#### High-Performance CSV Import
- **DuckDB Integration**: Leverage DuckDB for 10-50x faster CSV processing
- **Batch Processing**: Handle large datasets in optimized 1,000-row batches
- **Error Recovery**: Implement retry logic with exponential backoff (3 attempts, 5s delay)
- **Progress Monitoring**: Real-time import status and completion tracking

#### Data Normalization
- **City Name Standardization**: Convert all city names to Title Case format
- **Address Parsing**: Extract and normalize street addresses
- **Coordinate Validation**: Verify latitude/longitude accuracy
- **Duplicate Detection**: Identify and handle duplicate property records

#### Quality Assurance
- **Data Validation**: Ensure completeness and accuracy of imported data
- **Schema Compliance**: Validate against defined database schema
- **Audit Logging**: Track all data transformations and imports
- **Error Reporting**: Comprehensive logging of import issues and resolutions

### 3.2 Interactive Mapping Platform

#### Progressive Map Visualization
- **Zoom-Based Rendering**: Adaptive data loading based on map zoom level
  - Zoom 1-7: City overview with cluster points for density
  - Zoom 8-11: Grid-based clustering of properties
  - Zoom 14+: Individual property markers with status colors

#### Real-Time Search and Navigation
- **City Autocomplete**: Instant search with property count previews
- **Geographic Navigation**: Smooth transitions between city views
- **Viewport Optimization**: Efficient loading of properties within map bounds
- **Performance Optimization**: Sub-2-second rendering for any view

#### Property Status Visualization
- **Color-Coded Markers**: Visual status indicators
  - Blue: Unreviewed properties
  - Orange: Reviewed properties
  - Green: Synced properties
  - Red: Unqualified properties
- **Interactive Clustering**: Dynamic grouping based on density and zoom
- **Filtering Controls**: Filter by status, primer team owner, or custom filters on the property record data.

### 3.3 Property Management System

#### Property Information Display
- **Comprehensive Details**: Address, coordinates, parcel number, county, zoning code, permitted by right, occupancy, fire sprinklers, folio number, etc.
- **Status Tracking**: Current sourcing status with update capabilities
- **Metadata Display**: Import date, data source, quality indicators
- **Historical Changes**: Audit trail of status and data modifications

#### Workflow Management
- **Status Updates**: Change property status through UI interactions
- **Bulk Operations**: Update multiple properties simultaneously
- **Pipeline Tracking**: Monitor properties through acquisition workflow
- **Notes and Annotations**: Add custom notes and tags during property review

### 3.4 Analytics and Reporting

#### Market Intelligence
- **Property Density Analysis**: Identify market saturation levels
- **Geographic Trends**: Analyze patterns across regions
- **Status Distribution**: Track pipeline health and conversion rates

#### Data Export and Integration
- **CSV Export**: Download filtered property datasets
- **Push to Salesforce**: Connect with Salesforce CRM to push property record
- **Report Generation**: Automated market analysis reports

---

## 4. Technical Requirements

### 4.1 Architecture Overview

#### Backend Infrastructure
- **Database**: Supabase PostgreSQL with PostGIS extension
- **Data Processing**: DuckDB for high-performance CSV operations
- **API Layer**: Supabase Edge Functions (Deno runtime), FastAPI endpoints for heavy processing
- **Authentication**: Supabase Auth (future implementation)
- **Caching**: Redis

#### Frontend Platform
- **Framework**: React 18+ with TypeScript
- **Build System**: Vite for fast development and builds
- **Styling**: Tailwind CSS with design system tokens
- **Mapping**: Mapbox GL JS with vector tiles support
- **State Management**: Zustand + React Query
- **Data Fetching**: "@tanstack/react-query": "^5.0.0"
- **Virtualization**: "@tanstack/react-virtual": "^3.0.0"
- **Error Handling**: "react-error-boundary": "^4.0.0"

#### Development Environment
**Languages:**
- Python: "3.12.x"
- TypeScript: "5.x"

**Package Management:**
- Python: "Poetry 1.7+"
- Frontend: "pnpm 8.x"

**Code Quality:**
- Python: "ruff + black + mypy"
- Frontend: "ESLint + Prettier + TypeScript strict"
- Hooks: "pre-commit with comprehensive checks"

**Development Tools:**
- Environment: "direnv + .envrc"
- Task Runner: "Makefile + scripts/"
- IDE: "VS Code with recommended extensions"

**Version Control:**
- Commits: "Conventional commits with commitlint"
- PR Process: "Template-driven with checklists"
- Automation: "GitHub Actions for CI/CD"

### 4.2 Performance Requirements

#### Data Processing Performance
- **Import Speed**: Process 300K+ records per minute
- **Memory Efficiency**: Handle large datasets within 8GB RAM limit
- **Batch Optimization**: 1,000-row batches for optimal throughput
- **Error Recovery**: Resume capability for failed imports

#### Frontend Performance
- **Initial Load**: < 3 seconds for application startup
- **Map Rendering**: < 2 seconds for any city view
- **Search Response**: < 500ms for autocomplete results
- **Data Updates**: Real-time status changes without page refresh

#### Database Performance
```javascript
{
  'simple_queries': '< 50ms',
  'geospatial_queries': '< 200ms (vs 1s)',
  'complex_aggregations': '< 500ms',
  'concurrent_users': '150+ (vs 100+)',
  'connection_efficiency': '95%+ pool utilization',
  'cache_hit_ratio': '> 90%',
  'replication_lag': '< 100ms'
}
```

### 4.3 Data Requirements

#### Data Sources
- **Coverage**: All counties in Texas, Alabama, and Florida
- **Format**: CSV files from county records
- **Volume**: Millions of property records
- **Update Frequency**: Quarterly data refreshes

#### Data Quality Standards
- **Accuracy**: 95%+ data accuracy rate
- **Completeness**: < 20% missing critical fields
- **Consistency**: Standardized formatting across all records
- **Timeliness**: Data freshness within 180 days

#### Security and Privacy
- **Access Control**: Role-based permissions (future)
- **Audit Logging**: Complete audit trail of data access

### 4.4 Integration Requirements

#### External Services
- **Mapbox**: Maps, geocoding, and vector tiles
- **Supabase**: Database, authentication, and edge functions
- **Third-Party APIs**: County data sources (future)

#### Internal Systems
- **CRM Integration**: Export to real estate CRM systems (future)
- **Analytics Tools**: Integration with business intelligence platforms

---

## 5. Success Criteria

### 5.1 Technical Success Metrics

#### Performance Benchmarks
- **Data Import**: Complete county import in < 30 minutes
- **Search Performance**: City search results in < 10 seconds
- **Map Rendering**: Full city view loads in < 2 seconds
- **System Uptime**: 99.5% availability during business hours

#### Data Quality Metrics
- **Accuracy Rate**: 95%+ validated property information
- **Completeness**: < 5% missing essential fields
- **Normalization**: 100% city names in Title Case format
- **Duplicate Rate**: < 1% duplicate properties in database

#### Code Quality Standards
- **Test Coverage**: > 80% code coverage for critical functions
- **Documentation**: 100% public API documentation
- **Code Review**: All changes reviewed before deployment
- **Clean Code**: Zero magic numbers, meaningful names throughout

### 5.2 Business Success Metrics

#### Operational Efficiency
- **Time Savings**: 75% reduction in property research time
- **Data Access**: 90% of properties accessible through platform
- **Workflow Improvement**: 50% faster property pipeline management
- **Decision Speed**: 60% faster investment decision making

#### Market Impact
- **Market Coverage**: Comprehensive data for top 50 Texas cities
- **Competitive Advantage**: Unique data insights not available elsewhere
- **Revenue Impact**: Measurable ROI for real estate professionals
- **Scalability**: Architecture proven for expansion to other states

### 5.3 User Experience Success Criteria

#### Usability Metrics
- **Learning Curve**: New users productive within 15 minutes
- **Task Completion**: 90%+ success rate for core user tasks
- **Error Rate**: < 5% user errors during typical workflows
- **Support Requests**: < 10% of users require support assistance

#### Feature Adoption
- **Search Usage**: 95% of sessions include city search
- **Map Interaction**: 80% of users zoom/pan for detailed views
- **Status Updates**: 60% of identified properties get status updates
- **Export Features**: 40% of users export data for analysis

---

## 6. Risk Assessment and Mitigation

### Technical Risks
- **Data Quality Issues**: Implement comprehensive validation and monitoring
- **Performance Bottlenecks**: Conduct regular performance testing and optimization
- **Scalability Challenges**: Design with horizontal scaling from day one
- **Integration Failures**: Build robust error handling and fallback mechanisms